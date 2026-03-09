"""Drop overly-strict chemical unique key (uq_chem_cas).

Revision ID: 20260106_01
Revises: 20260105_01
Create Date: 2026-01-06
"""

from __future__ import annotations

from alembic import op


revision = "20260106_01"
down_revision = "20260105_01"
branch_labels = None
depends_on = None


def _index_exists(conn, *, table: str, index: str) -> bool:
    rows = conn.exec_driver_sql(
        "SELECT COUNT(1) AS c FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = %s AND index_name = %s",
        (table, index),
    ).fetchone()
    return bool(rows and int(rows[0]) > 0)


def upgrade() -> None:
    conn = op.get_bind()
    if _index_exists(conn, table="chemicals", index="uq_chem_cas"):
        # This index blocks valid GB18218 Table1 rows where multiple entries share the same CAS+Qi+unit.
        conn.exec_driver_sql("DROP INDEX uq_chem_cas ON chemicals")


def downgrade() -> None:
    conn = op.get_bind()
    if not _index_exists(conn, table="chemicals", index="uq_chem_cas"):
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX uq_chem_cas ON chemicals (gb_version, cas_no, critical_quantity, unit)"
        )

