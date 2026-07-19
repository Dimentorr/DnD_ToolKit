"""Align the existing database schema with ORM models.

Revision ID: 7b2d4e91a6c3
Revises: 85589ad63686
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "7b2d4e91a6c3"
down_revision: str | None = "85589ad63686"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "name",
        existing_type=sa.String(),
        type_=sa.String(64),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(),
        type_=sa.String(320),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_users_name_length",
        "users",
        "char_length(name) BETWEEN 3 AND 64",
    )

    op.alter_column(
        "tokens",
        "token",
        existing_type=sa.String(),
        type_=sa.String(64),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_tokens_hash_length",
        "tokens",
        "char_length(token) = 64",
    )

    op.alter_column(
        "datasheets",
        "name",
        existing_type=sa.String(),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.add_column(
        "datasheets",
        sa.Column("ruleset_uuid", sa.UUID(), nullable=True),
    )
    op.add_column(
        "datasheets",
        sa.Column("race_uuid", sa.UUID(), nullable=True),
    )

    for column_name in ("stats", "wallet", "features", "inventory"):
        op.alter_column(
            "datasheets",
            column_name,
            existing_type=postgresql.JSON(),
            type_=postgresql.JSONB(),
            existing_nullable=False,
            postgresql_using=f"{column_name}::jsonb",
        )

    op.drop_constraint(
        "datasheets_user_uuid_fkey",
        "datasheets",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "datasheets_user_uuid_fkey",
        "datasheets",
        "users",
        ["user_uuid"],
        ["uuid"],
        ondelete="CASCADE",
    )
    op.create_index("ix_datasheets_user_uuid", "datasheets", ["user_uuid"])
    op.create_index("ix_datasheets_ruleset_uuid", "datasheets", ["ruleset_uuid"])
    op.create_index("ix_datasheets_race_uuid", "datasheets", ["race_uuid"])
    op.create_check_constraint(
        "ck_datasheets_name_length",
        "datasheets",
        "char_length(name) BETWEEN 1 AND 255",
    )

    op.alter_column(
        "rulesets",
        "status",
        existing_type=sa.String(),
        type_=sa.String(24),
        existing_nullable=False,
    )
    op.create_index("ix_rulesets_owner_uuid", "rulesets", ["owner_uuid"])
    op.create_index("ix_rulesets_parent_uuid", "rulesets", ["parent_uuid"])
    op.create_check_constraint(
        "ck_rulesets_name_length",
        "rulesets",
        "char_length(name) BETWEEN 1 AND 255",
    )
    op.create_check_constraint(
        "ck_rulesets_status",
        "rulesets",
        "status IN ('inwork', 'active', 'archive')",
    )
    op.create_check_constraint(
        "ck_rulesets_parent_not_self",
        "rulesets",
        "parent_uuid IS NULL OR parent_uuid <> uuid",
    )
    op.create_table(
        "races",
        sa.Column("uuid", sa.UUID(), nullable=False),
        sa.Column("ruleset_uuid", sa.UUID(), nullable=False),
        sa.Column("parent_uuid", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(name) BETWEEN 1 AND 255",
            name="ck_races_name_length",
        ),
        sa.CheckConstraint(
            "parent_uuid IS NULL OR parent_uuid <> uuid",
            name="ck_races_parent_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["parent_uuid"],
            ["races.uuid"],
            name="races_parent_uuid_fkey",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["ruleset_uuid"],
            ["rulesets.uuid"],
            name="races_ruleset_uuid_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("uuid", name="races_pkey"),
        sa.UniqueConstraint(
            "ruleset_uuid",
            "name",
            name="uq_races_ruleset_uuid_name",
        ),
    )
    op.create_index("ix_races_ruleset_uuid", "races", ["ruleset_uuid"])
    op.create_index("ix_races_parent_uuid", "races", ["parent_uuid"])
    op.create_foreign_key(
        "datasheets_ruleset_uuid_fkey",
        "datasheets",
        "rulesets",
        ["ruleset_uuid"],
        ["uuid"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "datasheets_race_uuid_fkey",
        "datasheets",
        "races",
        ["race_uuid"],
        ["uuid"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("datasheets_race_uuid_fkey", "datasheets", type_="foreignkey")
    op.drop_constraint("datasheets_ruleset_uuid_fkey", "datasheets", type_="foreignkey")
    op.drop_index("ix_races_parent_uuid", table_name="races")
    op.drop_index("ix_races_ruleset_uuid", table_name="races")
    op.drop_table("races")

    op.drop_constraint("ck_rulesets_parent_not_self", "rulesets", type_="check")
    op.drop_constraint("ck_rulesets_status", "rulesets", type_="check")
    op.drop_constraint("ck_rulesets_name_length", "rulesets", type_="check")
    op.drop_index("ix_rulesets_parent_uuid", table_name="rulesets")
    op.drop_index("ix_rulesets_owner_uuid", table_name="rulesets")
    op.alter_column(
        "rulesets",
        "status",
        existing_type=sa.String(24),
        type_=sa.String(),
        existing_nullable=False,
    )

    op.drop_constraint("ck_datasheets_name_length", "datasheets", type_="check")
    op.drop_index("ix_datasheets_race_uuid", table_name="datasheets")
    op.drop_index("ix_datasheets_ruleset_uuid", table_name="datasheets")
    op.drop_index("ix_datasheets_user_uuid", table_name="datasheets")
    op.drop_constraint(
        "datasheets_user_uuid_fkey",
        "datasheets",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "datasheets_user_uuid_fkey",
        "datasheets",
        "users",
        ["user_uuid"],
        ["uuid"],
    )

    for column_name in ("stats", "wallet", "features", "inventory"):
        op.alter_column(
            "datasheets",
            column_name,
            existing_type=postgresql.JSONB(),
            type_=postgresql.JSON(),
            existing_nullable=False,
            postgresql_using=f"{column_name}::json",
        )

    op.drop_column("datasheets", "race_uuid")
    op.drop_column("datasheets", "ruleset_uuid")
    op.alter_column(
        "datasheets",
        "name",
        existing_type=sa.String(255),
        type_=sa.String(),
        existing_nullable=False,
    )

    op.drop_constraint("ck_tokens_hash_length", "tokens", type_="check")
    op.alter_column(
        "tokens",
        "token",
        existing_type=sa.String(64),
        type_=sa.String(),
        existing_nullable=False,
    )

    op.drop_constraint("ck_users_name_length", "users", type_="check")
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(255),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(320),
        type_=sa.String(),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "name",
        existing_type=sa.String(64),
        type_=sa.String(),
        existing_nullable=False,
    )
