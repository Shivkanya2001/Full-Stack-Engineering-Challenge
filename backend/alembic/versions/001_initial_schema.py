"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("profile_photo_url", sa.String(length=512), nullable=True),
        sa.Column("default_currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "exchange_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("target_currency", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exchange_rates")),
        sa.UniqueConstraint(
            "base_currency", "target_currency", "fetched_at",
            name=op.f("uq_exchange_rates_pair_fetched"),
        ),
    )
    op.create_index(op.f("ix_exchange_rates_base_currency"), "exchange_rates", ["base_currency"], unique=False)
    op.create_index(op.f("ix_exchange_rates_target_currency"), "exchange_rates", ["target_currency"], unique=False)
    op.create_index(op.f("ix_exchange_rates_fetched_at"), "exchange_rates", ["fetched_at"], unique=False)

    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("balance_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_wallets_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wallets")),
        sa.UniqueConstraint("user_id", "currency", name=op.f("uq_wallets_user_currency")),
        sa.CheckConstraint("balance_minor_units >= 0", name=op.f("ck_wallets_balance_non_negative")),
    )
    op.create_index(op.f("ix_wallets_user_id"), "wallets", ["user_id"], unique=False)

    op.create_table(
        "transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receiver_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receiver_wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_amount_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("receiver_amount_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("sender_currency", sa.String(length=3), nullable=False),
        sa.Column("receiver_currency", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exchange_rate_id"], ["exchange_rates.id"], name=op.f("fk_transfers_exchange_rate_id_exchange_rates")),
        sa.ForeignKeyConstraint(["receiver_user_id"], ["users.id"], name=op.f("fk_transfers_receiver_user_id_users")),
        sa.ForeignKeyConstraint(["receiver_wallet_id"], ["wallets.id"], name=op.f("fk_transfers_receiver_wallet_id_wallets")),
        sa.ForeignKeyConstraint(["sender_user_id"], ["users.id"], name=op.f("fk_transfers_sender_user_id_users")),
        sa.ForeignKeyConstraint(["sender_wallet_id"], ["wallets.id"], name=op.f("fk_transfers_sender_wallet_id_wallets")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transfers")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_transfers_idempotency_key")),
    )
    op.create_index(op.f("ix_transfers_sender_user_id"), "transfers", ["sender_user_id"], unique=False)
    op.create_index(op.f("ix_transfers_receiver_user_id"), "transfers", ["receiver_user_id"], unique=False)
    op.create_index(op.f("ix_transfers_idempotency_key"), "transfers", ["idempotency_key"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("amount_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("balance_after_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exchange_rate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exchange_rate_id"], ["exchange_rates.id"], name=op.f("fk_transactions_exchange_rate_id_exchange_rates")),
        sa.ForeignKeyConstraint(["transfer_id"], ["transfers.id"], name=op.f("fk_transactions_transfer_id_transfers")),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], name=op.f("fk_transactions_wallet_id_wallets"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index(op.f("ix_transactions_wallet_id"), "transactions", ["wallet_id"], unique=False)
    op.create_index(op.f("ix_transactions_type"), "transactions", ["type"], unique=False)
    op.create_index(op.f("ix_transactions_currency"), "transactions", ["currency"], unique=False)
    op.create_index(op.f("ix_transactions_transfer_id"), "transactions", ["transfer_id"], unique=False)
    op.create_index(op.f("ix_transactions_created_at"), "transactions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("transfers")
    op.drop_table("wallets")
    op.drop_table("exchange_rates")
    op.drop_table("users")
