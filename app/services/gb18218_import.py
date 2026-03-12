from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

from ..extensions import db
from ..models import (
    GB_18218_2018,
    AlphaRule,
    CategoryBeta,
    CategoryThreshold,
    Chemical,
    LevelRule,
)


@dataclass(frozen=True)
class ImportSummary:
    chemicals: int
    alpha_rules: int
    level_rules: int
    category_thresholds: int
    category_betas: int


@dataclass(frozen=True)
class ValidationReport:
    chemicals_total_inserts: int
    chemicals_unique: int
    chemicals_importable: int
    chemicals_skipped: int
    skipped_samples: tuple[str, ...]
    alpha_rules: int
    level_rules: int
    category_thresholds: int
    category_betas: int


def import_gb18218_full_seed_sql(
    sql_text: str,
    *,
    gb_version: str = GB_18218_2018,
    replace_rules: bool = True,
) -> ImportSummary:
    parsed = parse_gb18218_full_seed_sql(sql_text)

    now = datetime.utcnow()
    # Use a nested transaction (SAVEPOINT) to avoid "A transaction is already begun on this Session."
    with db.session.begin_nested():
        # α / level rules: prefer replace for idempotency and to avoid duplicates.
        if replace_rules:
            AlphaRule.query.filter_by(gb_version=gb_version).delete(synchronize_session=False)
            LevelRule.query.filter_by(gb_version=gb_version).delete(synchronize_session=False)

        for r in parsed["alpha_rules"]:
            db.session.add(
                AlphaRule(
                    gb_version=gb_version,
                    min_people=r["min_people"],
                    max_people=r["max_people"],
                    alpha=r["alpha"],
                    source=f"{gb_version} 表5",
                    note="由 GB18218_full_seed.sql 导入",
                )
            )
        for r in parsed["level_rules"]:
            db.session.add(
                LevelRule(
                    gb_version=gb_version,
                    min_r=r["min_r"],
                    max_r=r["max_r"],
                    level=r["level"],
                    source=f"{gb_version} 表6",
                    note="由 GB18218_full_seed.sql 导入",
                )
            )

        # category_thresholds / category_betas: cross-db upsert via query-then-update/insert.
        for r in parsed["category_thresholds"]:
            existing_q = CategoryThreshold.query.filter_by(
                gb_version=gb_version,
                category_symbol=r["category_symbol"],
            ).first()
            if existing_q:
                existing_q.threshold_quantity = r["threshold_quantity"]
                existing_q.unit = r["unit"] or "t"
                existing_q.source = f"{gb_version} 表2"
                existing_q.note = "由 GB18218_full_seed.sql 导入"
            else:
                db.session.add(
                    CategoryThreshold(
                        gb_version=gb_version,
                        category_symbol=r["category_symbol"],
                        threshold_quantity=r["threshold_quantity"],
                        unit=r["unit"] or "t",
                        source=f"{gb_version} 表2",
                        note="由 GB18218_full_seed.sql 导入",
                    )
                )

        for r in parsed["category_betas"]:
            existing_b = CategoryBeta.query.filter_by(
                gb_version=gb_version,
                category_symbol=r["category_symbol"],
            ).first()
            if existing_b:
                existing_b.beta = r["beta"]
                existing_b.beta_source = r.get("beta_source") or "TABLE4"
                existing_b.source = f"{gb_version} 表4"
                existing_b.note = "由 GB18218_full_seed.sql 导入"
            else:
                db.session.add(
                    CategoryBeta(
                        gb_version=gb_version,
                        category_symbol=r["category_symbol"],
                        beta=r["beta"],
                        beta_source=r.get("beta_source") or "TABLE4",
                        source=f"{gb_version} 表4",
                        note="由 GB18218_full_seed.sql 导入",
                    )
                )

        # chemicals: cross-db upsert by logical key (name + cas_no).
        for r in parsed["chemicals"]:
            q = Chemical.query.filter(Chemical.name == r["name"])
            if r.get("cas_no") is None:
                q = q.filter(Chemical.cas_no.is_(None))
            else:
                q = q.filter(Chemical.cas_no == r.get("cas_no"))
            existing = q.order_by(Chemical.updated_at.desc(), Chemical.id.desc()).first()

            if existing:
                existing.gb_version = gb_version
                existing.category = r.get("category")
                existing.critical_quantity = r["critical_quantity"]
                existing.unit = r.get("unit") or "t"
                existing.source_standard = _normalize_source_standard(r.get("source_standard") or "")
                existing.updated_at = now
                continue

            db.session.add(
                Chemical(
                    gb_version=gb_version,
                    name=r["name"],
                    category=r.get("category"),
                    cas_no=r.get("cas_no"),
                    critical_quantity=r["critical_quantity"],
                    unit=r.get("unit") or "t",
                    source_standard=_normalize_source_standard(r.get("source_standard") or ""),
                    hazard_category_symbol=None,
                    beta=None,
                    beta_source=None,
                    created_at=now,
                    updated_at=now,
                )
            )

    return ImportSummary(
        chemicals=len(parsed["chemicals"]),
        alpha_rules=len(parsed["alpha_rules"]),
        level_rules=len(parsed["level_rules"]),
        category_thresholds=len(parsed["category_thresholds"]),
        category_betas=len(parsed["category_betas"]),
    )


def parse_gb18218_full_seed_sql(sql_text: str) -> dict[str, list[dict[str, Any]]]:
    """
    Parse GB18218_full_seed.sql (auto-generated) into our system tables.

    Supported sources in that file:
    - INSERT INTO gb18218_alpha_rules(...)
    - INSERT INTO gb18218_level_rules(...)
    - INSERT INTO gb18218_category_thresholds(...)
    - INSERT INTO gb18218_category_betas(...)
    - INSERT INTO chemicals(...)
    """

    normalized = sql_text.replace("\r\n", "\n")

    alpha_rows: list[dict[str, Any]] = []
    level_rows: list[dict[str, Any]] = []
    cat_q_rows: list[dict[str, Any]] = []
    cat_beta_rows: list[dict[str, Any]] = []
    chemical_rows: list[dict[str, Any]] = []

    alpha_rows.extend(_parse_values_blocks(normalized, "gb18218_alpha_rules", _map_alpha_tuple))
    level_rows.extend(_parse_values_blocks(normalized, "gb18218_level_rules", _map_level_tuple))
    cat_q_rows.extend(
        _parse_values_blocks(normalized, "gb18218_category_thresholds", _map_category_threshold_tuple)
    )
    cat_beta_rows.extend(
        _parse_values_blocks(normalized, "gb18218_category_betas", _map_category_beta_tuple)
    )

    # chemicals statements include "ON DUPLICATE KEY UPDATE ... VALUES(xxx)" which contains extra parentheses,
    # so we parse chemicals with a dedicated pattern that only captures the first VALUES(...) tuple.
    chemical_rows.extend(_parse_chemicals_inserts(normalized))

    # de-dup within a single import run
    chemical_rows = _dedup_chemicals(chemical_rows)

    return {
        "alpha_rules": alpha_rows,
        "level_rules": level_rows,
        "category_thresholds": cat_q_rows,
        "category_betas": cat_beta_rows,
        "chemicals": chemical_rows,
    }


def _parse_chemicals_inserts(sql_text: str) -> list[dict[str, Any]]:
    rows, _stats = _parse_chemicals_inserts_with_stats(sql_text, max_samples=0)
    return rows


def validate_gb18218_full_seed_sql(sql_text: str, *, max_samples: int = 10) -> ValidationReport:
    normalized = sql_text.replace("\r\n", "\n")
    chemicals, stats = _parse_chemicals_inserts_with_stats(normalized, max_samples=max_samples)
    parsed = parse_gb18218_full_seed_sql(normalized)
    return ValidationReport(
        chemicals_total_inserts=stats["total_inserts"],
        chemicals_unique=len(chemicals),
        chemicals_importable=len(chemicals),
        chemicals_skipped=stats["skipped"],
        skipped_samples=tuple(stats["samples"]),
        alpha_rules=len(parsed["alpha_rules"]),
        level_rules=len(parsed["level_rules"]),
        category_thresholds=len(parsed["category_thresholds"]),
        category_betas=len(parsed["category_betas"]),
    )


def _parse_chemicals_inserts_with_stats(
    sql_text: str, *, max_samples: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pattern = re.compile(
        r"INSERT\s+(?:IGNORE\s+)?INTO\s+chemicals\s*\((?P<cols>[^)]+)\)\s*VALUES\s*(?P<vals>.+?)\s*(?:ON\s+DUPLICATE\s+KEY\s+UPDATE|;)",
        re.IGNORECASE | re.DOTALL,
    )
    out: list[dict[str, Any]] = []
    skipped = 0
    samples: list[str] = []
    total_rows = 0

    for m in pattern.finditer(sql_text):
        cols = [c.strip(" `\n\t") for c in m.group("cols").split(",")]
        tuples = _split_top_level_tuples(m.group("vals"))
        total_rows += len(tuples)
        for t in tuples:
            fields = _split_csv_fields(t)
            if len(fields) != len(cols):
                skipped += 1
                if max_samples and len(samples) < max_samples:
                    samples.append("化学品行解析失败：字段数量不匹配（可能存在逗号/括号问题）")
                continue
            row = {cols[i]: _parse_sql_value(fields[i]) for i in range(len(cols))}
            mapped, reason = _try_map_chemicals_tuple(row)
            if mapped is None:
                skipped += 1
                if reason and max_samples and len(samples) < max_samples:
                    name = str(row.get("name") or "").strip()
                    samples.append(f"跳过：{name[:40]}（{reason}）")
                continue
            out.append(mapped)

    out = _dedup_chemicals(out)
    return out, {"total_inserts": total_rows, "skipped": skipped, "samples": samples}


def _normalize_source_standard(src: str) -> str:
    s = (src or "").strip()
    if not s:
        return f"{GB_18218_2018}"
    s = (
        s.replace("GB18218-2018", GB_18218_2018)
        .replace("GB 18218-2018", GB_18218_2018)
        .replace("GB 18218—2018", GB_18218_2018)
        .replace("GB 18218―2018", GB_18218_2018)
    )
    s = (
        s.replace("Table1", "表1")
        .replace("Table2", "表2")
        .replace("Table3", "表3")
        .replace("Table4", "表4")
    )
    return s


def _dedup_chemicals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str | None]] = set()
    out: list[dict[str, Any]] = []
    for r in rows:
        key = (str(r.get("name") or "").strip(), (r.get("cas_no") or None))
        if not key[0]:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _parse_values_blocks(sql_text: str, table: str, mapper):
    pattern = re.compile(
        rf"INSERT\s+(?:IGNORE\s+)?INTO\s+{re.escape(table)}\s*\((?P<cols>[^)]+)\)\s*VALUES\s*(?P<vals>.+?);",
        re.IGNORECASE | re.DOTALL,
    )
    out: list[dict[str, Any]] = []
    for m in pattern.finditer(sql_text):
        cols = [c.strip(" `\n\t") for c in m.group("cols").split(",")]
        tuples = _split_top_level_tuples(m.group("vals"))
        for t in tuples:
            fields = _split_csv_fields(t)
            if len(fields) != len(cols):
                continue
            row = {cols[i]: _parse_sql_value(fields[i]) for i in range(len(cols))}
            mapped = mapper(row)
            if mapped:
                out.append(mapped)
    return out


def _split_top_level_tuples(vals: str) -> list[str]:
    s = vals.strip()
    out: list[str] = []
    in_str = False
    esc = False
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == "'":
                in_str = False
            continue
        else:
            if ch == "'":
                in_str = True
                continue
            if ch == "(":
                if depth == 0:
                    start = i + 1
                depth += 1
                continue
            if ch == ")":
                depth -= 1
                if depth == 0 and start is not None:
                    out.append(s[start:i])
                    start = None
                continue
    return out


def _split_csv_fields(tuple_body: str) -> list[str]:
    s = tuple_body.strip()
    out: list[str] = []
    in_str = False
    esc = False
    buf: list[str] = []
    for ch in s:
        if in_str:
            buf.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == "'":
                in_str = False
            continue
        else:
            if ch == "'":
                in_str = True
                buf.append(ch)
                continue
            if ch == ",":
                out.append("".join(buf).strip())
                buf = []
                continue
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return out


def _parse_sql_value(token: str) -> Any:
    t = token.strip()
    if not t or t.upper() == "NULL":
        return None
    if t.upper() == "NOW()":
        return datetime.utcnow()
    if t.startswith("'") and t.endswith("'"):
        inner = t[1:-1]
        inner = inner.replace("\\'", "'")
        inner = inner.replace("''", "'")
        return inner
    # number?
    try:
        if "." in t:
            return float(t)
        return int(t)
    except Exception:
        return t


def _map_alpha_tuple(row: dict[str, Any]) -> dict[str, Any] | None:
    if "min_people" not in row or "alpha" not in row:
        return None
    return {
        "min_people": int(row["min_people"]),
        "max_people": int(row["max_people"]) if row.get("max_people") is not None else None,
        "alpha": float(row["alpha"]),
    }


def _map_level_tuple(row: dict[str, Any]) -> dict[str, Any] | None:
    # seed columns: level, r_min, r_max
    if "level" not in row or "r_min" not in row:
        return None
    return {
        "level": str(row["level"]),
        "min_r": float(row["r_min"]),
        "max_r": float(row["r_max"]) if row.get("r_max") is not None else None,
    }


def _map_category_threshold_tuple(row: dict[str, Any]) -> dict[str, Any] | None:
    if "symbol" not in row or "threshold_qty" not in row:
        return None
    return {
        "category_symbol": str(row["symbol"]),
        "threshold_quantity": float(row["threshold_qty"]),
        "unit": str(row.get("unit") or "t"),
    }


def _map_category_beta_tuple(row: dict[str, Any]) -> dict[str, Any] | None:
    symbol = row.get("symbol") or row.get("category_symbol")
    if symbol is None or row.get("beta") is None:
        return None
    return {
        "category_symbol": str(symbol),
        "beta": float(row["beta"]),
        "beta_source": str(row.get("source") or "TABLE4"),
    }


def _try_map_chemicals_tuple(row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    # seed columns: name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at
    if "name" not in row or "critical_quantity" not in row:
        return None, "缺少必要字段"
    name = str(row.get("name") or "").strip()
    if not name:
        return None, "名称为空"
    if row.get("critical_quantity") is None:
        return None, "临界量为空（不满足当前表结构：critical_quantity NOT NULL）"
    try:
        critical = float(row["critical_quantity"])
    except Exception:
        return None, "临界量不是数字"
    return (
        {
            "name": name,
            "category": row.get("category"),
            "cas_no": row.get("cas_no"),
            "critical_quantity": critical,
            "unit": row.get("unit") or "t",
            "source_standard": row.get("source_standard") or "",
        },
        None,
    )


def _map_chemicals_tuple(row: dict[str, Any]) -> dict[str, Any] | None:
    mapped, _reason = _try_map_chemicals_tuple(row)
    return mapped
