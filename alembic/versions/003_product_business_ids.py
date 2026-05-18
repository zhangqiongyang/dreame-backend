"""migrate legacy product slugs to P-prefixed business ids

Revision ID: 003
Revises: 002
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.data.product_ids import LEGACY_PRODUCT_ID_MAP

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    pending = []
    for old_id, new_id in LEGACY_PRODUCT_ID_MAP.items():
        row = conn.execute(
            sa.text("SELECT 1 FROM products WHERE id = :id LIMIT 1"),
            {"id": old_id},
        ).fetchone()
        if row:
            pending.append((old_id, new_id))

    if not pending:
        return

    conn.execute(sa.text("SET FOREIGN_KEY_CHECKS = 0"))
    try:
        for old_id, new_id in pending:
            conn.execute(
                sa.text("UPDATE products SET id = :new_id WHERE id = :old_id"),
                {"new_id": new_id, "old_id": old_id},
            )
            conn.execute(
                sa.text("UPDATE order_items SET product_id = :new_id WHERE product_id = :old_id"),
                {"new_id": new_id, "old_id": old_id},
            )
    finally:
        conn.execute(sa.text("SET FOREIGN_KEY_CHECKS = 1"))


def downgrade() -> None:
    conn = op.get_bind()
    reverse = {new: old for old, new in LEGACY_PRODUCT_ID_MAP.items()}
    pending = []
    for new_id, old_id in reverse.items():
        row = conn.execute(
            sa.text("SELECT 1 FROM products WHERE id = :id LIMIT 1"),
            {"id": new_id},
        ).fetchone()
        if row:
            pending.append((new_id, old_id))

    if not pending:
        return

    conn.execute(sa.text("SET FOREIGN_KEY_CHECKS = 0"))
    try:
        for new_id, old_id in pending:
            conn.execute(
                sa.text("UPDATE products SET id = :old_id WHERE id = :new_id"),
                {"new_id": new_id, "old_id": old_id},
            )
            conn.execute(
                sa.text("UPDATE order_items SET product_id = :old_id WHERE product_id = :new_id"),
                {"new_id": new_id, "old_id": old_id},
            )
    finally:
        conn.execute(sa.text("SET FOREIGN_KEY_CHECKS = 1"))
