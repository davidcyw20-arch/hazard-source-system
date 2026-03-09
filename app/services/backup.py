from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.sql import text

from ..extensions import db


def export_db_to_json() -> dict[str, Any]:
    payload: dict[str, Any] = {"exported_at": datetime.utcnow().isoformat() + "Z", "tables": {}}
    insp = inspect(db.engine)
    for table_name in insp.get_table_names():
        rows = db.session.execute(text(f"SELECT * FROM `{table_name}`")).mappings().all()
        payload["tables"][table_name] = [dict(r) for r in rows]
    return payload


def export_db_to_xlsx() -> io.BytesIO:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Excel 导出依赖未就绪：请先安装 openpyxl。") from e

    insp = inspect(db.engine)
    wb = Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True)
    header_alignment = Alignment(horizontal="center", vertical="center")

    def cell_value(v: Any):
        if v is None:
            return None
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False, default=str)
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v

    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table_names = sorted(insp.get_table_names())

    # Overview sheet (helps users who only see a single column/sheet in some viewers)
    ws0 = wb.create_sheet(title="00_导出说明")
    ws0.append(["导出时间", exported_at])
    ws0.append(["说明", "每个工作表对应一张数据表；第一行是字段名；支持筛选/冻结表头。"])
    ws0.append(["提示", "如只看到“日期”，请切换工作表或向右滚动查看其他列。"])
    ws0.append([])
    ws0.append(["表名", "记录数"])
    for col_idx in range(1, 3):
        c = ws0.cell(row=5, column=col_idx)
        c.font = header_font
        c.alignment = header_alignment
    ws0.freeze_panes = "A6"
    ws0.column_dimensions["A"].width = 26
    ws0.column_dimensions["B"].width = 16

    for table_name in table_names:
        rows = db.session.execute(text(f"SELECT * FROM `{table_name}`")).mappings().all()
        ws0.append([table_name, len(rows)])
        if rows:
            columns = list(rows[0].keys())
        else:
            columns = [c["name"] for c in insp.get_columns(table_name)]

        ws = wb.create_sheet(title=table_name[:31])
        ws.append(columns)
        for col_idx in range(1, len(columns) + 1):
            c = ws.cell(row=1, column=col_idx)
            c.font = header_font
            c.alignment = header_alignment

        for r in rows:
            row_dict = dict(r)
            # Avoid leaking password hashes in "viewing" export.
            if table_name == "users" and "password_hash" in row_dict:
                row_dict["password_hash"] = "***"
            ws.append([cell_value(row_dict.get(c)) for c in columns])

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        for idx, col in enumerate(columns, start=1):
            max_len = len(str(col))
            for row in ws.iter_rows(
                min_row=2, min_col=idx, max_col=idx, max_row=min(ws.max_row, 2000)
            ):
                v = row[0].value
                if v is None:
                    continue
                max_len = max(max_len, min(len(str(v)), 60))
            ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(
                max_len + 2, 70
            )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def import_db_from_json(payload: dict[str, Any], *, truncate_first: bool = True) -> None:
    tables: dict[str, list[dict[str, Any]]] = payload.get("tables", {}) or {}
    insp = inspect(db.engine)
    insert_order = _toposort_tables(list(tables.keys()), insp)
    delete_order = list(reversed(insert_order))

    def normalize(v: Any):
        if v is None:
            return None
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False, default=str)
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v

    # IMPORTANT: FOREIGN_KEY_CHECKS is per-connection in MySQL, so pin one connection.
    with db.engine.begin() as conn:
        _set_fk_checks_conn(conn, False)

        if truncate_first:
            for table_name in delete_order:
                conn.execute(text(f"DELETE FROM `{table_name}`"))

        for table_name in insert_order:
            rows = tables.get(table_name, [])
            if not rows:
                continue
            cols = list(rows[0].keys())
            col_list = ", ".join([f"`{c}`" for c in cols])
            val_list = ", ".join([f":{c}" for c in cols])
            stmt = text(f"INSERT INTO `{table_name}` ({col_list}) VALUES ({val_list})")
            cooked = [{k: normalize(v) for k, v in r.items()} for r in rows]
            conn.execute(stmt, cooked)

        _set_fk_checks_conn(conn, True)


def _set_fk_checks_conn(conn, enabled: bool) -> None:
    try:
        conn.execute(text(f"SET FOREIGN_KEY_CHECKS={'1' if enabled else '0'}"))
    except Exception:
        return


def _toposort_tables(table_names: list[str], insp) -> list[str]:
    # Parents before children (insert order), reverse for delete order.
    table_set = set(table_names)
    deps: dict[str, set[str]] = {t: set() for t in table_names}
    rdeps: dict[str, set[str]] = {t: set() for t in table_names}
    try:
        for t in table_names:
            for fk in insp.get_foreign_keys(t) or []:
                ref = fk.get("referred_table")
                if ref and ref in table_set:
                    deps[t].add(ref)
                    rdeps[ref].add(t)
    except Exception:
        return table_names

    ready = [t for t in table_names if not deps[t]]
    out: list[str] = []
    while ready:
        n = ready.pop(0)
        out.append(n)
        for child in list(rdeps[n]):
            deps[child].discard(n)
            if not deps[child]:
                ready.append(child)
    remaining = [t for t in table_names if t not in out]
    return out + remaining


def dumps_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


def loads_json(text_in: str) -> dict[str, Any]:
    return json.loads(text_in)
