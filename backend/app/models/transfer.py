import uuid
from enum import StrEnum

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class TransferStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TransferModel(Base, TimestampMixin):
    __tablename__ = "transfers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    sender_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    receiver_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    sender_wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False
    )
    receiver_wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False
    )
    sender_amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)
    receiver_amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    receiver_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exchange_rates.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=TransferStatus.COMPLETED)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)

    transactions: Mapped[list["TransactionModel"]] = relationship(back_populates="transfer")
