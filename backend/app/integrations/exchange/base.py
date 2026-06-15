from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class FetchedRate:
    base_currency: str
    target_currency: str
    rate: Decimal
    provider: str
    fetched_at: datetime


class ExchangeRateProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def fetch_latest_rates(self, base_currency: str, targets: list[str]) -> list[FetchedRate]:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
