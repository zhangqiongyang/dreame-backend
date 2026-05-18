"""backfill order status for pending refunds

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE orders o
            INNER JOIN refunds r ON r.order_id = o.id
            SET o.status = 'refund_pending'
            WHERE r.status = 'pending' AND o.status = 'pending_shipping'
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE orders o
            INNER JOIN refunds r ON r.order_id = o.id
            SET o.status = 'pending_shipping'
            WHERE r.status = 'pending' AND o.status = 'refund_pending'
            """
        )
    )
