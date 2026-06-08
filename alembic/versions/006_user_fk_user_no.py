"""orders/refunds/addresses user_id references users.user_no

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("orders", "refunds", "user_addresses")


def _drop_user_fk(conn, table: str) -> None:
    rows = conn.execute(
        sa.text(
            """
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND REFERENCED_TABLE_NAME = 'users'
              AND COLUMN_NAME = 'user_id'
            """
        ),
        {"table": table},
    ).fetchall()
    for (name,) in rows:
        conn.execute(sa.text(f"ALTER TABLE `{table}` DROP FOREIGN KEY `{name}`"))


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        sa.text(
            """
            SELECT COUNT(*) AS c
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND COLUMN_NAME = :column
            """
        ),
        {"table": table, "column": column},
    ).one()
    return int(row.c) > 0


def upgrade() -> None:
    conn = op.get_bind()

    for table in _TABLES:
        if not _column_exists(conn, table, "user_biz_id"):
            op.add_column(table, sa.Column("user_biz_id", sa.String(32), nullable=True))
        conn.execute(
            sa.text(
                f"""
                UPDATE `{table}` t
                INNER JOIN users u ON t.user_id = u.id
                SET t.user_biz_id = u.user_no
                WHERE t.user_biz_id IS NULL
                """
            )
        )

    conn.execute(sa.text("SET FOREIGN_KEY_CHECKS=0"))

    for table in _TABLES:
        if _column_exists(conn, table, "user_id"):
            _drop_user_fk(conn, table)
            op.drop_column(table, "user_id")
        op.alter_column(
            table,
            "user_biz_id",
            new_column_name="user_id",
            existing_type=sa.String(32),
            nullable=False,
        )
        fk_kw = {"ondelete": "CASCADE"} if table == "user_addresses" else {}
        op.create_foreign_key(
            f"fk_{table}_user_no",
            table,
            "users",
            ["user_id"],
            ["user_no"],
            **fk_kw,
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])

    conn.execute(sa.text("SET FOREIGN_KEY_CHECKS=1"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("SET FOREIGN_KEY_CHECKS=0"))

    for table in _TABLES:
        _drop_user_fk(conn, table)
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_constraint(f"fk_{table}_user_no", table, type_="foreignkey")
        op.alter_column(table, "user_id", new_column_name="user_biz_id", existing_type=sa.String(32))

        op.add_column(table, sa.Column("user_int_id", sa.Integer(), nullable=True))
        conn.execute(
            sa.text(
                f"""
                UPDATE `{table}` t
                INNER JOIN users u ON t.user_biz_id = u.user_no
                SET t.user_int_id = u.id
                """
            )
        )
        op.drop_column(table, "user_biz_id")
        op.alter_column(
            table,
            "user_int_id",
            new_column_name="user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        fk_kw = {"ondelete": "CASCADE"} if table == "user_addresses" else {}
        op.create_foreign_key(
            f"fk_{table}_users_id",
            table,
            "users",
            ["user_id"],
            ["id"],
            **fk_kw,
        )
        if table == "orders":
            op.create_index("ix_orders_user_id", table, ["user_id"])
        elif table == "user_addresses":
            op.create_index("ix_user_addresses_user_id", table, ["user_id"])

    conn.execute(sa.text("SET FOREIGN_KEY_CHECKS=1"))
