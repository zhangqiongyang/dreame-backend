"""user addresses table

Revision ID: 005
Revises: 004
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_addresses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("address_no", sa.String(32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("province", sa.String(32), nullable=False, server_default=""),
        sa.Column("city", sa.String(32), nullable=False, server_default=""),
        sa.Column("district", sa.String(32), nullable=False, server_default=""),
        sa.Column("detail", sa.String(255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("address_no"),
    )
    op.create_index("ix_user_addresses_user_id", "user_addresses", ["user_id"])
    op.create_index("ix_user_addresses_address_no", "user_addresses", ["address_no"])


def downgrade() -> None:
    op.drop_index("ix_user_addresses_address_no", table_name="user_addresses")
    op.drop_index("ix_user_addresses_user_id", table_name="user_addresses")
    op.drop_table("user_addresses")
