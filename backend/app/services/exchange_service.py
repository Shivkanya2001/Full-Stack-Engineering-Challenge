import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ExchangeRateError, NotFoundError
from app.core.logging import log_event
from app.integrations.exchange.frankfurter import FrankfurterProvider
from app.repositories import ExchangeRateRepository

logger = logging.getLogger(__name__)


class ExchangeService:
    def __init__(self, session: AsyncSession, provider: FrankfurterProvider | None = None):
        self.session = session
        self.rates = ExchangeRateRepository(session)
        self.provider = provider or FrankfurterProvider()
        self.settings = get_settings()

    async def refresh_rates(self, base_currency: str | None = None) -> list[dict]:
        base = (base_currency or self.settings.default_currency).upper()
        targets = [c for c in self.settings.supported_currencies if c != base]

        fetched = await self.provider.fetch_latest_rates(base, targets)
        if not fetched:
            raise ExchangeRateError("No rates returned from provider")

        stored = await self.rates.store_rates(
            [
                (r.base_currency, r.target_currency, r.rate, r.provider, r.fetched_at)
                for r in fetched
            ]
        )
        await self.session.commit()

        log_event(logger, "exchange.refresh", base=base, count=len(stored), provider=self.provider.name)
        return [self._rate_response(r) for r in stored]

    async def get_latest_rates(self, base_currency: str | None = None) -> list[dict]:
        base = (base_currency or self.settings.default_currency).upper()
        rates = await self.rates.list_latest_for_base(base)
        if not rates:
            rates = await self.refresh_rates(base)
            return rates
        return [self._rate_response(r) for r in rates]

    async def get_rate_for_conversion(
        self, source_currency: str, target_currency: str
    ) -> tuple[UUID | None, Decimal, str, datetime]:
        source = source_currency.upper()
        target = target_currency.upper()

        if source == target:
            return None, Decimal("1"), "identity", datetime.now(UTC)  # type: ignore[return-value]

        direct = await self.rates.get_latest(source, target)
        if direct and self._is_fresh(direct.fetched_at):
            return direct.id, direct.rate, direct.provider, direct.fetched_at

        inverse = await self.rates.get_latest(target, source)
        if inverse and self._is_fresh(inverse.fetched_at):
            rate = Decimal("1") / inverse.rate
            return inverse.id, rate, inverse.provider, inverse.fetched_at

        try:
            await self.refresh_rates(source)
            direct = await self.rates.get_latest(source, target)
            if direct:
                return direct.id, direct.rate, direct.provider, direct.fetched_at
        except Exception as exc:
            logger.warning("Live rate fetch failed: %s", exc)

        if direct:
            return direct.id, direct.rate, direct.provider, direct.fetched_at
        if inverse:
            rate = Decimal("1") / inverse.rate
            return inverse.id, rate, inverse.provider, inverse.fetched_at

        raise ExchangeRateError(f"No exchange rate available for {source}/{target}")

    async def list_history(
        self,
        base_currency: str | None,
        target_currency: str | None,
        page: int,
        page_size: int,
    ) -> dict:
        items, total = await self.rates.list_history(base_currency, target_currency, page, page_size)
        return {
            "items": [self._rate_response(r) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def health_check(self) -> bool:
        return await self.provider.health_check()

    def _is_fresh(self, fetched_at: datetime) -> bool:
        max_age = timedelta(hours=self.settings.exchange_max_stale_hours)
        return datetime.now(UTC) - fetched_at.replace(tzinfo=UTC) <= max_age

    @staticmethod
    def _rate_response(rate) -> dict:
        return {
            "id": str(rate.id),
            "base_currency": rate.base_currency,
            "target_currency": rate.target_currency,
            "rate": str(rate.rate),
            "provider": rate.provider,
            "fetched_at": rate.fetched_at.isoformat(),
            "valid_from": rate.valid_from.isoformat(),
            "valid_until": rate.valid_until.isoformat() if rate.valid_until else None,
        }
