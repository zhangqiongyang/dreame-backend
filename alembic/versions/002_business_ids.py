"""add user_no and business id rules

Revision ID: 002
Revises: 001
"""

import secrets
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _gen_user_no() -> str:
    day = datetime.now().strftime("%Y%m%d")
    suffix = "".join(secrets.choice("0123456789") for _ in range(8))
    return f"U{day}{suffix}"


def upgrade() -> None:
    op.add_column("users", sa.Column("user_no", sa.String(32), nullable=True))
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id FROM users WHERE user_no IS NULL")).fetchall()
    used: set[str] = set()
    for (uid,) in rows:
        while True:
            candidate = _gen_user_no()
            if candidate not in used:
                used.add(candidate)
                break
        conn.execute(
            sa.text("UPDATE users SET user_no = :no WHERE id = :id"),
            {"no": candidate, "id": uid},
        )
    op.alter_column("users", "user_no", existing_type=sa.String(32), nullable=False)
    op.create_index("ix_users_user_no", "users", ["user_no"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_user_no", table_name="users")
    op.drop_column("users", "user_no")
