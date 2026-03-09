from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click
from sqlalchemy import text
from flask import Flask

from .extensions import db
from .models import (
    GB_18218_2018,
    AlphaRule,
    AuditLog,
    CategoryBeta,
    CategoryThreshold,
    Chemical,
    EvaluationResult,
    LevelRule,
    RuleSet,
    StorageRecord,
    User,
)
from .services.identify import identify_gb18218
from .services.gb18218_import import import_gb18218_full_seed_sql
from .services.gb18218_beta_seed import seed_gb18218_beta_and_thresholds


def _read_sql_text_with_fallback(path: Path) -> str:
    """Read SQL text with encoding fallback for common CN exports (UTF-8/GBK)."""
    raw = path.read_bytes()
    candidates = ["utf-8", "utf-8-sig", "gb18030", "gbk"]
    best_text = None
    best_bad = 10**9

    for enc in candidates:
        try:
            txt = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        bad = txt.count("�")
        if bad < best_bad:
            best_bad = bad
            best_text = txt
            if bad == 0:
                break

    if best_text is not None:
        return best_text
    return raw.decode("utf-8", errors="replace")


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command():
        """Create tables and seed minimal reference data."""
        db.create_all()
        _ensure_default_rules()
        _ensure_default_admin()
        _ensure_demo_chemicals()
        _ensure_extended_reference_chemicals()
        _ensure_gb18218_params()
        click.echo("OK: database initialized.")

    @app.cli.command("create-admin")
    @click.option("--username", default="admin", show_default=True)
    @click.option("--password", default="admin123", show_default=True)
    def create_admin(username: str, password: str):
        """Create or reset an admin account."""
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, role="admin", is_active=True)
            db.session.add(user)
        user.set_password(password)
        user.role = "admin"
        user.is_active = True
        db.session.commit()
        click.echo(f"OK: admin '{username}' ready.")

    @app.cli.command("dump-rules")
    def dump_rules():
        rules = RuleSet.query.all()
        click.echo(json.dumps([r.levels for r in rules], ensure_ascii=False, indent=2))

    @app.cli.command("db-upgrade")
    def db_upgrade():
        """Apply Alembic migrations to the current database."""
        try:
            from alembic import command
            from alembic.config import Config
        except Exception as e:  # pragma: no cover
            raise click.ClickException(
                "未安装 alembic，请先执行 `pip install -r requirements.txt`。"
            ) from e

        root = Path(__file__).resolve().parent.parent
        ini_path = root / "alembic.ini"
        if not ini_path.exists():
            raise click.ClickException(f"未找到 {ini_path}，无法执行迁移。")
        cfg = Config(str(ini_path))
        cfg.set_main_option("script_location", "migrations")
        command.upgrade(cfg, "head")
        click.echo("OK: database upgraded to latest migration.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Insert extra demo data for presentation."""
        db.create_all()
        _ensure_default_rules()
        _ensure_default_admin()
        _ensure_demo_chemicals()
        _ensure_extended_reference_chemicals()
        _seed_more_chemicals()
        _ensure_gb18218_params()
        _seed_demo_users()
        _seed_demo_storage_and_results()
        click.echo("OK: demo data seeded.")

    @app.cli.command("import-gb18218-sql")
    @click.option("--file", "file_path", required=True, help="Path to GB18218_full_seed.sql")
    @click.option("--replace-rules/--keep-rules", default=True, show_default=True)
    def import_gb18218_sql(file_path: str, replace_rules: bool):
        """Import GB18218_full_seed.sql into current schema (chemicals + parameter tables)."""
        db.create_all()
        text = _read_sql_text_with_fallback(Path(file_path))
        summary = import_gb18218_full_seed_sql(text, replace_rules=replace_rules)
        click.echo(
            f"OK: imported chemicals={summary.chemicals}, alpha_rules={summary.alpha_rules}, "
            f"level_rules={summary.level_rules}, category_thresholds={summary.category_thresholds}, "
            f"category_betas={summary.category_betas}"
        )



    @app.cli.command("import-all-sql")
    @click.option("--root", "root_dir", default=".", show_default=True, help="目录根路径")
    def import_all_sql(root_dir: str):
        """一键导入项目根目录下 4 个 SQL 文件（按顺序 best-effort）。"""
        root = Path(root_dir).resolve()
        files = [
            root / "db_schema.sql",
            root / "GB18218_full_seed.sql",
            root / "GB18218_full_seed_fixed.sql",
            root / "db_init_gb18218.sql",
        ]

        db.create_all()
        click.echo(f"[1/4] schema ready: {root}")

        schema_report = _exec_sql_file_best_effort(files[0])
        click.echo(f"[2/4] db_schema.sql -> executed={schema_report['executed']} skipped={schema_report['skipped']} errors={schema_report['errors']}")

        for idx, fp in enumerate(files[1:3], start=3):
            if not fp.exists():
                click.echo(f"[{idx}/4] {fp.name} not found, skip")
                continue
            txt = _read_sql_text_with_fallback(fp)
            try:
                summary = import_gb18218_full_seed_sql(txt, replace_rules=True)
                db.session.commit()
                click.echo(
                    f"[{idx}/4] {fp.name} -> chemicals={summary.chemicals}, alpha={summary.alpha_rules}, level={summary.level_rules}, cat_q={summary.category_thresholds}, cat_beta={summary.category_betas}"
                )
            except Exception as e:
                db.session.rollback()
                click.echo(f"[{idx}/4] {fp.name} import failed: {e}")

        init_report = _exec_sql_file_best_effort(files[3])
        click.echo(f"[4/4] db_init_gb18218.sql -> executed={init_report['executed']} skipped={init_report['skipped']} errors={init_report['errors']}")

        _ensure_default_rules()
        _ensure_default_admin()
        _ensure_demo_chemicals()
        _ensure_extended_reference_chemicals()
        _ensure_gb18218_params()
        click.echo("OK: import-all-sql done.")

    @app.cli.command("seed-reference-data")
    def seed_reference_data():
        """补齐一批常见危化品参考数据（幂等，可重复执行）。"""
        db.create_all()
        inserted = _ensure_extended_reference_chemicals()
        click.echo(f"OK: reference chemicals ready, inserted={inserted}.")

    @app.cli.command("seed-gb18218-beta")
    def seed_gb18218_beta():
        """Seed GB 18218-2018 Table3/Table4 β and category thresholds, then fill missing chemicals.beta."""
        db.create_all()
        summary = seed_gb18218_beta_and_thresholds()
        db.session.commit()
        click.echo(
            "OK: seed-gb18218-beta "
            f"category_betas_upserted={summary.category_betas_upserted}, "
            f"category_thresholds_upserted={summary.category_thresholds_upserted}, "
            f"chemicals_table3_beta_updated={summary.chemicals_table3_beta_updated}, "
            f"chemicals_table4_beta_filled={summary.chemicals_table4_beta_filled}"
        )




def _exec_sql_file_best_effort(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"executed": 0, "skipped": 1, "errors": 0}

    text_sql = path.read_text(encoding="utf-8", errors="replace")
    statements = [seg.strip() for seg in text_sql.split(";") if seg.strip()]
    executed = 0
    skipped = 0
    errors = 0

    for stmt in statements:
        up = stmt.upper()
        # Skip directives that are MySQL session-level and often unsupported cross-db.
        if up.startswith("SET ") or up.startswith("USE "):
            skipped += 1
            continue
        try:
            db.session.execute(text(stmt))
            executed += 1
        except Exception:
            db.session.rollback()
            errors += 1

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        errors += 1

    return {"executed": executed, "skipped": skipped, "errors": errors}
def _ensure_default_rules() -> None:
    existing = RuleSet.query.filter_by(is_active=True).first()
    if existing:
        return
    levels = [
        {"min": 1, "max": 10, "level": "四级"},
        {"min": 10, "max": 50, "level": "三级"},
        {"min": 50, "max": 100, "level": "二级"},
        {"min": 100, "max": None, "level": "一级"},
    ]
    rule = RuleSet(name="默认规则（GB 18218 常用区间）", is_active=True, levels=levels)
    db.session.add(rule)
    db.session.commit()


def _ensure_default_admin() -> None:
    admin = User.query.filter_by(role="admin").first()
    if admin:
        return
    admin = User(username="admin", role="admin", is_active=True)
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()


def _ensure_demo_chemicals() -> None:
    if Chemical.query.count() > 0:
        return
    demo = [
        ("液氯", "毒性气体", "7782-50-5", 10.0),
        ("液氨", "毒性气体", "7664-41-7", 10.0),
        ("液化石油气", "易燃气体", None, 200.0),
        ("汽油", "易燃液体", None, 200.0),
        ("硝酸铵", "氧化性固体", "6484-52-2", 1000.0),
    ]
    for name, category, cas, critical in demo:
        db.session.add(
            Chemical(
                name=name,
                category=category,
                cas_no=cas,
                critical_quantity=critical,
                unit="t",
                source_standard="GB 18218（示例数据）",
            )
        )
    db.session.commit()


def _ensure_gb18218_params() -> None:
    # NOTE:
    # - alpha_rules / level_rules use the values from the user's engineering description.
    # - category_* tables are optional placeholders until you import full Table 2/4 data.
    if AlphaRule.query.filter_by(gb_version=GB_18218_2018).count() == 0:
        rules = [
            (0, 1, 0.5),
            (1, 30, 1.0),
            (30, 50, 1.2),
            (50, 100, 1.5),
            (100, None, 2.0),
        ]
        for min_p, max_p, a in rules:
            db.session.add(
                AlphaRule(
                    gb_version=GB_18218_2018,
                    min_people=min_p,
                    max_people=max_p,
                    alpha=float(a),
                    source=f"{GB_18218_2018} 表5",
                    note="按工程化描述录入；如采用正式标准表格，请核对后更新。",
                )
            )
        db.session.commit()

    if LevelRule.query.filter_by(gb_version=GB_18218_2018).count() == 0:
        rules = [
            (0, 10, "四级"),
            (10, 50, "三级"),
            (50, 100, "二级"),
            (100, None, "一级"),
        ]
        for min_r, max_r, level in rules:
            db.session.add(
                LevelRule(
                    gb_version=GB_18218_2018,
                    min_r=float(min_r),
                    max_r=float(max_r) if max_r is not None else None,
                    level=level,
                    source=f"{GB_18218_2018} 表6",
                    note="按工程化描述录入；如采用正式标准表格，请核对后更新。",
                )
            )
        db.session.commit()

    # Category-level fallbacks for mixtures or missing chemical beta/Q.
    if CategoryBeta.query.filter_by(gb_version=GB_18218_2018).count() == 0:
        demo = [
            ("A", 1.0),
            ("B", 1.2),
            ("C", 1.5),
        ]
        for sym, beta in demo:
            db.session.add(
                CategoryBeta(
                    gb_version=GB_18218_2018,
                    category_symbol=sym,
                    beta=float(beta),
                    beta_source="占位",
                    source=f"{GB_18218_2018} 表4",
                    note="占位示例：请按表4补全后启用类别兜底 β。",
                )
            )
        db.session.commit()

    if CategoryThreshold.query.filter_by(gb_version=GB_18218_2018).count() == 0:
        demo = [
            ("A", 10.0, "t"),
            ("B", 200.0, "t"),
            ("C", 1000.0, "t"),
        ]
        for sym, q, unit in demo:
            db.session.add(
                CategoryThreshold(
                    gb_version=GB_18218_2018,
                    category_symbol=sym,
                    threshold_quantity=float(q),
                    unit=unit,
                    source=f"{GB_18218_2018} 表2",
                    note="占位示例：请按表2补全后启用类别兜底 Qi。",
                )
            )
        db.session.commit()

    _ensure_gb18218_table1_table3_chemicals()


def _ensure_gb18218_table1_table3_chemicals() -> None:
    # Minimal runnable subset from the user's description (Table 1 / Table 3 examples).
    # This keeps existing demo rows and only upserts by name+cas_no.
    upserts = [
        # Table 1 examples (Qi)
        {
            "name": "氨",
            "category": "毒性气体",
            "cas_no": None,
            "critical_quantity": 10.0,
            "unit": "t",
            "source_standard": f"{GB_18218_2018} 表1",
            # Table 3 example (β)
            "beta": 2.0,
            "beta_source": f"{GB_18218_2018} 表3",
        },
        {
            "name": "氯",
            "category": "毒性气体",
            "cas_no": None,
            "critical_quantity": 5.0,
            "unit": "t",
            "source_standard": f"{GB_18218_2018} 表1",
            "beta": 4.0,
            "beta_source": f"{GB_18218_2018} 表3",
        },
        {
            "name": "甲醇",
            "category": "易燃液体",
            "cas_no": None,
            "critical_quantity": 500.0,
            "unit": "t",
            "source_standard": f"{GB_18218_2018} 表1",
            "beta": None,
            "beta_source": None,
        },
    ]

    for row in upserts:
        chem = Chemical.query.filter_by(name=row["name"], cas_no=row["cas_no"]).first()
        if not chem:
            chem = Chemical(
                gb_version=GB_18218_2018,
                name=row["name"],
                category=row["category"],
                cas_no=row["cas_no"],
                critical_quantity=float(row["critical_quantity"]),
                unit=row["unit"],
                source_standard=row["source_standard"],
                hazard_category_symbol=None,
                beta=row["beta"],
                beta_source=row["beta_source"],
            )
            db.session.add(chem)
        else:
            chem.gb_version = GB_18218_2018
            chem.category = row["category"]
            chem.critical_quantity = float(row["critical_quantity"])
            chem.unit = row["unit"]
            chem.source_standard = row["source_standard"]
            if row["beta"] is not None:
                chem.beta = float(row["beta"])
                chem.beta_source = row["beta_source"]
        db.session.commit()

    # Table 3 examples: apply β to existing rows if present.
    beta_updates = [
        (("一氧化碳", "CO"), 2.0),
        (("氨", "液氨"), 2.0),
        (("氯", "液氯"), 4.0),
        (("硫化氢", "H2S"), 5.0),
        (("氯化氢", "氯化氢（无水）", "HCl"), 3.0),
        (("氰化氢", "HCN"), 10.0),
        (("碳酰氯", "光气", "COCl2"), 20.0),
    ]
    for names, beta in beta_updates:
        for name in names:
            chem = Chemical.query.filter_by(name=name).first()
            if not chem:
                continue
            chem.gb_version = GB_18218_2018
            chem.beta = float(beta)
            chem.beta_source = f"{GB_18218_2018} 表3"
        db.session.commit()


def _seed_more_chemicals() -> None:
    # Teaching/demo dataset (not authoritative); you can replace with accurate GB 18218 list later.
    more = [
        ("苯", "易燃液体", "71-43-2", 50.0),
        ("甲苯", "易燃液体", "108-88-3", 200.0),
        ("乙醇", "易燃液体", "64-17-5", 500.0),
        ("甲醇", "易燃液体", "67-56-1", 500.0),
        ("硫酸", "腐蚀性液体", "7664-93-9", 1000.0),
        ("盐酸", "腐蚀性液体", "7647-01-0", 1000.0),
        ("氢氧化钠溶液", "腐蚀性液体", "1310-73-2", 1000.0),
        ("过氧化氢（27.5%）", "氧化性液体", "7722-84-1", 200.0),
        ("乙炔", "易燃气体", "74-86-2", 10.0),
        ("氢气", "易燃气体", "1333-74-0", 10.0),
        ("一氧化碳", "毒性气体", "630-08-0", 10.0),
        ("硫化氢", "毒性气体", "7783-06-4", 10.0),
        ("丙烯", "易燃气体", "115-07-1", 200.0),
        ("乙烯", "易燃气体", "74-85-1", 200.0),
        ("二甲醚", "易燃气体", "115-10-6", 200.0),
        ("丙酮", "易燃液体", "67-64-1", 500.0),
        ("正己烷", "易燃液体", "110-54-3", 200.0),
        ("柴油", "易燃液体", None, 2000.0),
        ("苯乙烯", "易燃液体", "100-42-5", 200.0),
        ("乙酸乙酯", "易燃液体", "141-78-6", 500.0),
        ("乙二醇", "可燃液体", "107-21-1", 1000.0),
        ("硝酸", "腐蚀性液体", "7697-37-2", 1000.0),
        ("氯化氢（无水）", "毒性气体", "7647-01-0", 10.0),
    ]
    existing_names = {c.name for c in Chemical.query.with_entities(Chemical.name).all()}
    to_add = []
    for name, category, cas, critical in more:
        if name in existing_names:
            continue
        to_add.append(
            Chemical(
                name=name,
                category=category,
                cas_no=cas,
                critical_quantity=float(critical),
                unit="t",
                source_standard="GB 18218（教学示例数据）",
            )
        )
    if to_add:
        db.session.add_all(to_add)
        db.session.commit()


def _ensure_extended_reference_chemicals() -> int:
    """More complete baseline chemical dataset for first-run and demos."""
    rows = [
        ("氯乙烯", "易燃气体", "75-01-4", 50.0, None),
        ("氯化氢（无水）", "毒性气体", "7647-01-0", 20.0, 3.0),
        ("正己烷", "易燃液体", "110-54-3", 500.0, None),
        ("汽油", "易燃液体", "86290-81-5", 200.0, None),
        ("溴", "毒性液体", "7726-95-6", 20.0, None),
        ("甲苯二异氰酸酯(TDI)", "毒性液体", "26471-62-5", 100.0, None),
        ("过氧化钾", "氧化性固体", "17014-71-0", 20.0, None),
        ("液氨", "毒性气体", "7664-41-7", 10.0, 2.0),
        ("液氯", "毒性气体", "7782-50-5", 10.0, 4.0),
        ("二氧化氮", "毒性气体", "10102-44-0", 1.0, None),
        ("二氧化硫", "毒性气体", "7446-09-5", 20.0, None),
        ("二氟化氧", "氧化性气体", "7783-41-7", 1.0, None),
        ("二硫化碳", "易燃液体", "75-15-0", 50.0, None),
        ("丙酮", "易燃液体", "67-64-1", 500.0, None),
        ("乙烯", "易燃气体", "74-85-1", 50.0, None),
        ("乙酸乙酯", "易燃液体", "141-78-6", 500.0, None),
        ("乙醇", "易燃液体", "64-17-5", 500.0, None),
        ("乙醚", "易燃液体", "60-29-7", 10.0, None),
        ("硝酸", "氧化性液体", "7697-37-2", 100.0, None),
        ("碳化钙", "遇湿易燃物", "75-20-7", 100.0, None),
        ("碳酰氯（光气）", "毒性气体", "75-44-5", 0.3, 20.0),
        ("发烟硫酸", "腐蚀性液体", "52583-42-3", 20.0, None),
        ("硫酸二甲酯", "毒性液体", "77-78-1", 1.0, None),
        ("煤气", "易燃气体", None, 20.0, None),
        ("环己烷", "易燃液体", "110-82-7", 500.0, None),
        ("环氧乙烷", "易燃气体", "75-21-8", 10.0, None),
        ("甲醛（含量>90%）", "毒性液体", "50-00-0", 5.0, None),
        ("甲苯", "易燃液体", "108-88-3", 500.0, None),
        ("白磷", "自燃固体", "12185-10-3", 50.0, None),
        ("砷化氢", "毒性气体", "7784-42-1", 1.0, None),
        ("苯", "易燃液体", "71-43-2", 50.0, None),
    ]
    existing = {
        (n, c)
        for n, c in db.session.query(Chemical.name, Chemical.cas_no).all()
    }
    add_count = 0
    for name, category, cas, critical, beta in rows:
        key = (name, cas)
        if key in existing:
            continue
        db.session.add(
            Chemical(
                gb_version=GB_18218_2018,
                name=name,
                category=category,
                cas_no=cas,
                critical_quantity=float(critical),
                unit="t",
                source_standard=f"{GB_18218_2018}（内置补充数据）",
                beta=beta,
                beta_source=f"{GB_18218_2018} 表3" if beta is not None else None,
            )
        )
        add_count += 1
    if add_count:
        db.session.commit()
    return add_count


def _seed_demo_users() -> None:
    users = [
        ("demo1", "demo123", "华安化工有限公司", "张三", "13800000001", "XX省XX市XX区"),
        ("demo2", "demo123", "海润能源有限公司", "李四", "13800000002", "XX省XX市XX区"),
        ("demo3", "demo123", "恒泰仓储有限公司", "王五", "13800000003", "XX省XX市XX区"),
        ("demo4", "demo123", "新源新材料有限公司", "赵六", "13800000004", "XX省XX市高新区"),
        ("demo5", "demo123", "宏远物流园区", "钱七", "13800000005", "XX省XX市经开区"),
    ]
    for username, pwd, company, contact, phone, address in users:
        u = User.query.filter_by(username=username).first()
        if not u:
            u = User(username=username, role="user", is_active=True)
            u.set_password(pwd)
            db.session.add(u)
        u.company_name = company
        u.contact_name = contact
        u.phone = phone
        u.address = address
    db.session.commit()


def _seed_demo_storage_and_results() -> None:
    admin = User.query.filter_by(role="admin").first()
    active_rule = RuleSet.query.filter_by(is_active=True).first()
    if not active_rule:
        _ensure_default_rules()
        active_rule = RuleSet.query.filter_by(is_active=True).first()

    def chem_id(name: str) -> int:
        c = Chemical.query.filter_by(name=name).first()
        if not c:
            raise RuntimeError(f"chemical not found: {name}")
        return c.id

    demo_map = {
        "demo1": [
            {
                "enterprise": "华安化工有限公司",
                "status": "approved",
                "items": [
                    ("液氯", 6.0, "t", "液氯罐区", "压力容器"),
                    ("液氨", 4.0, "t", "液氨罐区", "压力容器"),
                    ("苯", 18.0, "t", "溶剂库", "储罐"),
                ],
            },
            {
                "enterprise": "华安化工（分厂）",
                "status": "approved",
                "items": [
                    ("乙醇", 20.0, "t", "溶剂仓库", "桶装/托盘"),
                    ("丙酮", 15.0, "t", "溶剂仓库", "桶装/托盘"),
                ],
            },
        ],
        "demo2": [
            {
                "enterprise": "海润能源有限公司",
                "status": "approved",
                "items": [
                    ("液化石油气", 120.0, "t", "球罐区", "压力容器"),
                    ("汽油", 80.0, "t", "油罐区", "常压储罐"),
                    ("柴油", 600.0, "t", "油品库区", "常压储罐"),
                ],
            },
            {
                "enterprise": "海润能源（油库）",
                "status": "pending",
                "items": [
                    ("汽油", 30.0, "t", "油罐区", "常压储罐"),
                    ("柴油", 150.0, "t", "油罐区", "常压储罐"),
                ],
            },
        ],
        "demo3": [
            {
                "enterprise": "恒泰仓储有限公司",
                "status": "approved",
                "items": [
                    ("硝酸铵", 200.0, "t", "危化仓库", "袋装/托盘"),
                    ("过氧化氢（27.5%）", 60.0, "t", "危化仓库", "塑料桶"),
                    ("盐酸", 200.0, "t", "酸碱库", "塑料槽罐"),
                ],
            },
            {
                "enterprise": "恒泰仓储（酸碱库）",
                "status": "rejected",
                "items": [
                    ("硫酸", 80.0, "t", "酸碱库", "防腐储罐"),
                    ("氢氧化钠溶液", 120.0, "t", "酸碱库", "防腐储罐"),
                ],
            },
        ],
        "demo4": [
            {
                "enterprise": "新源新材料有限公司",
                "status": "approved",
                "items": [
                    ("甲苯", 60.0, "t", "溶剂罐区", "常压储罐"),
                    ("苯乙烯", 40.0, "t", "溶剂罐区", "常压储罐"),
                ],
            }
        ],
        "demo5": [
            {
                "enterprise": "宏远物流园区",
                "status": "pending",
                "items": [
                    ("盐酸", 50.0, "t", "中转库", "槽罐车"),
                    ("过氧化氢（27.5%）", 20.0, "t", "中转库", "桶装"),
                ],
            }
        ],
    }

    for username, scenarios in demo_map.items():
        owner = User.query.filter_by(username=username).first()
        if not owner:
            continue
        for info in scenarios:
            enterprise = info["enterprise"]
            desired_status = info.get("status", "pending")
            # If already has data, skip to avoid duplicates.
            existing = StorageRecord.query.filter_by(
                owner_id=owner.id, enterprise_name=enterprise
            ).count()
            if existing > 0:
                continue

            recs: list[StorageRecord] = []
            for chem_name, amount, unit, location, method in info["items"]:
                rec = StorageRecord(
                    owner_id=owner.id,
                    enterprise_name=enterprise,
                    chemical_id=chem_id(chem_name),
                    amount=float(amount),
                    unit=unit,
                    location=location,
                    storage_method=method,
                    properties="系统预置示例数据",
                )
                recs.append(rec)
            db.session.add_all(recs)
            db.session.commit()

            records = StorageRecord.query.filter_by(
                owner_id=owner.id, enterprise_name=enterprise
            ).all()
            out = identify_gb18218(
                enterprise_name=enterprise,
                records=records,
                exposure_people_500m=500,
                gb_version=GB_18218_2018,
                rule_set=active_rule,
            )

            status = desired_status if desired_status in {"approved", "pending", "rejected"} else "pending"
            reviewer_id = None
            reviewed_at = None
            review_remark = None
            if admin and status in {"approved", "rejected"}:
                reviewer_id = admin.id
                reviewed_at = datetime.utcnow()
                review_remark = (
                    "系统预置示例数据：审核通过" if status == "approved" else "系统预置示例数据：驳回（信息需补充）"
                )

            result = EvaluationResult(
                owner_id=owner.id,
                enterprise_name=enterprise,
                rule_set_id=active_rule.id,
                gb_version=out.gb_version,
                s_value=out.s_value,
                exposure_people_500m=out.exposure_people_500m,
                alpha_used=out.alpha_used,
                r_value=out.r_value,
                is_major_hazard=out.is_major_hazard,
                level=out.level_compat,
                level_by_gb=out.level_by_gb,
                basis=out.basis,
                status=status,
                reviewer_id=reviewer_id,
                reviewed_at=reviewed_at,
                review_remark=review_remark,
            )
            db.session.add(result)
            db.session.commit()

            db.session.add(
                AuditLog(
                    user_id=owner.id,
                    action="seed_demo",
                    detail=f"enterprise={enterprise}, status={status}",
                    ip="127.0.0.1",
                )
            )
            db.session.commit()
