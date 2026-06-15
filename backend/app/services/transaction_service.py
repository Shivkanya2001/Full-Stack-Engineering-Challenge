from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import TransactionRepository


class TransactionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transactions = TransactionRepository(session)

    async def list_transactions(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        types: list[str] | None = None,
        currency: str | None = None,
        wallet_id: UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict:
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)

        items, total = await self.transactions.list_for_user(
            user_id=user_id,
            page=page,
            page_size=page_size,
            types=types,
            currency=currency,
            wallet_id=wallet_id,
            from_date=from_date,
            to_date=to_date,
        )
        return {
            "items": [
                {
                    "id": str(tx.id),
                    "wallet_id": str(tx.wallet_id),
                    "type": tx.type,
                    "amount_minor_units": tx.amount_minor_units,
                    "currency": tx.currency,
                    "balance_after_minor_units": tx.balance_after_minor_units,
                    "transfer_id": str(tx.transfer_id) if tx.transfer_id else None,
                    "exchange_rate_id": str(tx.exchange_rate_id) if tx.exchange_rate_id else None,
                    "metadata": tx.metadata,
                    "created_at": tx.created_at.isoformat(),
                }
                for tx in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
        }
