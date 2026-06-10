"""products.hero_image -> hero_images JSON array

Revision ID: 007
Revises: 006
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("hero_images", sa.JSON(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE products SET hero_images = JSON_ARRAY(hero_image) WHERE hero_image IS NOT NULL"
        )
    )
    op.execute(sa.text("UPDATE products SET hero_images = JSON_ARRAY() WHERE hero_images IS NULL"))
    op.alter_column("products", "hero_images", existing_type=sa.JSON(), nullable=False)
    op.drop_column("products", "hero_image")


def downgrade() -> None:
    op.add_column("products", sa.Column("hero_image", sa.String(512), nullable=True))
    op.execute(
        sa.text(
            "UPDATE products SET hero_image = JSON_UNQUOTE(JSON_EXTRACT(hero_images, '$[0]')) "
            "WHERE JSON_LENGTH(hero_images) > 0"
        )
    )
    op.execute(sa.text("UPDATE products SET hero_image = '' WHERE hero_image IS NULL"))
    op.alter_column("products", "hero_image", existing_type=sa.String(512), nullable=False)
    op.drop_column("products", "hero_images")
