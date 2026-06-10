"""drop products.title, keep name as single product title

Revision ID: 008
Revises: 007
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE products SET name = title "
            "WHERE title IS NOT NULL AND title != '' "
            "AND (name IS NULL OR name = '' OR CHAR_LENGTH(title) > CHAR_LENGTH(name))"
        )
    )
    op.drop_column("products", "title")


def downgrade() -> None:
    op.add_column("products", sa.Column("title", sa.Text(), nullable=True))
    op.execute(sa.text("UPDATE products SET title = name"))
    op.alter_column("products", "title", existing_type=sa.Text(), nullable=False)
