import logging
from datetime import UTC, datetime
from decimal import Decimal

import httpx

from app.core.config import get_settings
from app.integrations.exchange.base import ExchangeRateProvider, FetchedRate

logger = logging.getLogger(__name__)


class FrankfurterProvider(ExchangeRateProvider):
    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        settings = get_settings()
        self.base_url = base_url or settings.exchange_base_url
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "frankfurter"

    async def fetch_latest_rates(self, base_currency: str, targets: list[str]) -> list[FetchedRate]:
        if not targets:
            return []

        symbols = ",".join(sorted(set(targets)))
        url = f"{self.base_url}/latest"
        params = {"from": base_currency.upper(), "to": symbols}

        async with httpx.AsyncClient(timeout=self.timeout,follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        fetched_at = datetime.now(UTC)
        rates: list[FetchedRate] = []
        for target, rate_value in data.get("rates", {}).items():
            rates.append(
                FetchedRate(
                    base_currency=base_currency.upper(),
                    target_currency=target.upper(),
                    rate=Decimal(str(rate_value)),
                    provider=self.name,
                    fetched_at=fetched_at,
                )
            )
        logger.info("Fetched %s rates from Frankfurter", len(rates))
        return rates

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0,follow_redirects=True) as client:
                response = await client.get(f"{self.base_url}/latest", params={"from": "USD", "to": "EUR"})
                return response.status_code == 200
        except Exception:
            return False
