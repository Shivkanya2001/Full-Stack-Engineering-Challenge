from pydantic import BaseModel


class ExchangeRateResponse(BaseModel):
    id: str
    base_currency: str
    target_currency: str
    rate: str
    provider: str
    fetched_at: str
    valid_from: str
    valid_until: str | None


class ExchangeRateListResponse(BaseModel):
    items: list[ExchangeRateResponse]
    total: int
    page: int
    page_size: int
