import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.exceptions import InsufficientFundsError, ValidationError
from app.domain.value_objects.money import convert_amount, to_minor_units
from app.services.exchange_service import ExchangeService


def test_convert_amount_same_currency():
    assert convert_amount(1000, "USD", "USD", Decimal("1.2")) == 1000


def test_convert_amount_usd_to_eur():
    result = convert_amount(10000, "USD", "EUR", Decimal("0.85"))
    assert result == 8500


def test_to_minor_units_jpy():
    assert to_minor_units(Decimal("1000"), "JPY") == 1000


@pytest.mark.asyncio
async def test_exchange_service_refresh_rates(session, monkeypatch):
    from datetime import UTC, datetime
    from app.integrations.exchange.base import FetchedRate

    mock_provider = AsyncMock()
    mock_provider.name = "mock"
    mock_provider.fetch_latest_rates.return_value = [
        FetchedRate("USD", "EUR", Decimal("0.92"), "mock", datetime.now(UTC))
    ]

    service = ExchangeService(session, provider=mock_provider)
    rates = await service.refresh_rates("USD")
    assert len(rates) == 1
    assert rates[0]["base_currency"] == "USD"
    assert rates[0]["target_currency"] == "EUR"
