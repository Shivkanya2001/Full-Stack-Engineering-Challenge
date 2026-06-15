import logging

from app.database import AsyncSessionLocal
from app.services.exchange_service import ExchangeService

logger = logging.getLogger(__name__)


async def refresh_exchange_rates() -> None:
    async with AsyncSessionLocal() as session:
        try:
            service = ExchangeService(session)
            rates = await service.refresh_rates()
            logger.info("Scheduled rate refresh completed: %s rates", len(rates))
        except Exception as exc:
            logger.error("Scheduled rate refresh failed: %s", exc)
