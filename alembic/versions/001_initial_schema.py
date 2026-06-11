"""initial schema and product seed

Revision ID: 001
Revises:
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.data.product_seed import PRODUCT_SEEDS
from app.utils.money import yuan_to_cents

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("openid", sa.String(64), nullable=False),
        sa.Column("unionid", sa.String(64), nullable=True),
        sa.Column("nickname", sa.String(64), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("session_key", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("openid"),
    )
    op.create_index("ix_users_openid", "users", ["openid"])

    op.create_table(
        "products",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("market_price_cents", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("cover_url", sa.String(512), nullable=False),
        sa.Column("is_hot", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("promo", sa.String(64), nullable=True),
        sa.Column("spec_tags", sa.JSON(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("highlights", sa.JSON(), nullable=False),
        sa.Column("hero_image", sa.String(512), nullable=False),
        sa.Column("detail_images", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("product_amount_cents", sa.Integer(), nullable=False),
        sa.Column("freight_amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pay_amount_cents", sa.Integer(), nullable=False),
        sa.Column("remark", sa.String(255), nullable=True),
        sa.Column("payment_method", sa.String(32), nullable=True),
        sa.Column("receiver_name", sa.String(64), nullable=False),
        sa.Column("receiver_phone", sa.String(20), nullable=False),
        sa.Column("receiver_address", sa.String(512), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_order_no", "orders", ["order_no"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("thumb", sa.String(512), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("line_amount_cents", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("carrier", sa.String(64), nullable=False),
        sa.Column("tracking_no", sa.String(64), nullable=False),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )

    op.create_table(
        "order_status_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("operator_type", sa.String(16), nullable=False),
        sa.Column("operator_id", sa.String(64), nullable=True),
        sa.Column("remark", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_status_logs_order_id", "order_status_logs", ["order_id"])

    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("refund_no", sa.String(32), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("reason_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("audit_remark", sa.Text(), nullable=True),
        sa.Column("audited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
        sa.UniqueConstraint("refund_no"),
    )
    op.create_index("ix_refunds_status", "refunds", ["status"])

    op.create_table(
        "refund_status_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("refund_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("remark", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["refund_id"], ["refunds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refund_status_logs_refund_id", "refund_status_logs", ["refund_id"])

    products = sa.table(
        "products",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("price_cents", sa.Integer),
        sa.column("market_price_cents", sa.Integer),
        sa.column("tags", sa.JSON),
        sa.column("cover_url", sa.String),
        sa.column("is_hot", sa.Boolean),
        sa.column("sort", sa.Integer),
        sa.column("status", sa.String),
        sa.column("title", sa.Text),
        sa.column("promo", sa.String),
        sa.column("spec_tags", sa.JSON),
        sa.column("params", sa.JSON),
        sa.column("highlights", sa.JSON),
        sa.column("hero_image", sa.String),
        sa.column("detail_images", sa.JSON),
    )
    rows = []
    for p in PRODUCT_SEEDS:
        rows.append(
            {
                "id": p["id"],
                "name": p["name"],
                "price_cents": yuan_to_cents(p["price"]),
                "market_price_cents": yuan_to_cents(p["market_price"]) if p.get("market_price") else None,
                "tags": p["tags"],
                "cover_url": p["cover_url"],
                "is_hot": p["is_hot"],
                "sort": p["sort"],
                "status": "active",
                "title": p["name"],
                "promo": p.get("promo"),
                "spec_tags": p["spec_tags"],
                "params": p["params"],
                "highlights": p["highlights"],
                "hero_image": (p.get("hero_image") or (p.get("hero_images") or [""])[0]),
                "detail_images": p["detail_images"],
            }
        )
    op.bulk_insert(products, rows)


def downgrade() -> None:
    op.drop_table("refund_status_logs")
    op.drop_table("refunds")
    op.drop_table("order_status_logs")
    op.drop_table("shipments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("users")
