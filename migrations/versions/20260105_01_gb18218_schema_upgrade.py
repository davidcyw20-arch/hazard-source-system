"""GB18218-2018 schema upgrade

Revision ID: 20260105_01
Revises: 
Create Date: 2026-01-05
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260105_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    gb_default = sa.text("'GB 18218-2018'")

    # chemicals
    with op.batch_alter_table("chemicals") as b:
        b.add_column(sa.Column("gb_version", sa.String(length=30), nullable=False, server_default=gb_default))
        b.add_column(sa.Column("hazard_category_symbol", sa.String(length=20), nullable=True))
        b.add_column(sa.Column("beta", sa.Float(), nullable=True))
        b.add_column(sa.Column("beta_source", sa.String(length=100), nullable=True))

    # storage_records
    with op.batch_alter_table("storage_records") as b:
        b.add_column(sa.Column("unit_name", sa.String(length=120), nullable=True))
        b.add_column(sa.Column("unit_type", sa.String(length=50), nullable=True))
        b.add_column(sa.Column("qty_basis", sa.String(length=30), nullable=True))
        b.add_column(sa.Column("material_type", sa.String(length=30), nullable=True))
        b.add_column(sa.Column("mixture_name", sa.String(length=120), nullable=True))
        b.add_column(sa.Column("mixture_category_symbol", sa.String(length=20), nullable=True))

    # evaluation_results
    with op.batch_alter_table("evaluation_results") as b:
        b.add_column(sa.Column("gb_version", sa.String(length=30), nullable=False, server_default=gb_default))
        b.add_column(sa.Column("s_value", sa.Float(), nullable=False, server_default=sa.text("0")))
        b.add_column(sa.Column("exposure_people_500m", sa.Integer(), nullable=False, server_default=sa.text("0")))
        b.add_column(sa.Column("alpha_used", sa.Float(), nullable=False, server_default=sa.text("1")))
        b.add_column(sa.Column("level_by_gb", sa.String(length=20), nullable=True))

    # New parameter tables
    op.create_table(
        "alpha_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gb_version", sa.String(length=30), nullable=False),
        sa.Column("min_people", sa.Integer(), nullable=False),
        sa.Column("max_people", sa.Integer(), nullable=True),
        sa.Column("alpha", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False, server_default=gb_default),
        sa.Column("note", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_alpha_rules_gb", "alpha_rules", ["gb_version"])
    op.create_index("ix_alpha_rules_range", "alpha_rules", ["min_people", "max_people"])

    op.create_table(
        "level_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gb_version", sa.String(length=30), nullable=False),
        sa.Column("min_r", sa.Float(), nullable=False),
        sa.Column("max_r", sa.Float(), nullable=True),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False, server_default=gb_default),
        sa.Column("note", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_level_rules_gb", "level_rules", ["gb_version"])

    op.create_table(
        "category_thresholds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gb_version", sa.String(length=30), nullable=False),
        sa.Column("category_symbol", sa.String(length=20), nullable=False),
        sa.Column("threshold_quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False, server_default=sa.text("'t'")),
        sa.Column("source", sa.String(length=100), nullable=False, server_default=gb_default),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("gb_version", "category_symbol", name="uq_cat_threshold"),
    )
    op.create_index("ix_cat_threshold_symbol", "category_thresholds", ["category_symbol"])

    op.create_table(
        "category_betas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gb_version", sa.String(length=30), nullable=False),
        sa.Column("category_symbol", sa.String(length=20), nullable=False),
        sa.Column("beta", sa.Float(), nullable=False),
        sa.Column("beta_source", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False, server_default=gb_default),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("gb_version", "category_symbol", name="uq_cat_beta"),
    )
    op.create_index("ix_cat_beta_symbol", "category_betas", ["category_symbol"])


def downgrade() -> None:
    op.drop_index("ix_cat_beta_symbol", table_name="category_betas")
    op.drop_table("category_betas")
    op.drop_index("ix_cat_threshold_symbol", table_name="category_thresholds")
    op.drop_table("category_thresholds")
    op.drop_index("ix_level_rules_gb", table_name="level_rules")
    op.drop_table("level_rules")
    op.drop_index("ix_alpha_rules_range", table_name="alpha_rules")
    op.drop_index("ix_alpha_rules_gb", table_name="alpha_rules")
    op.drop_table("alpha_rules")

    with op.batch_alter_table("evaluation_results") as b:
        b.drop_column("level_by_gb")
        b.drop_column("alpha_used")
        b.drop_column("exposure_people_500m")
        b.drop_column("s_value")
        b.drop_column("gb_version")

    with op.batch_alter_table("storage_records") as b:
        b.drop_column("mixture_category_symbol")
        b.drop_column("mixture_name")
        b.drop_column("material_type")
        b.drop_column("qty_basis")
        b.drop_column("unit_type")
        b.drop_column("unit_name")

    with op.batch_alter_table("chemicals") as b:
        b.drop_column("beta_source")
        b.drop_column("beta")
        b.drop_column("hazard_category_symbol")
        b.drop_column("gb_version")

