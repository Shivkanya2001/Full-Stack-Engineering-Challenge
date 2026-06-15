from pydantic import BaseModel, Field


class ConversionRequest(BaseModel):
    source_wallet_id: str
    target_wallet_id: str
    amount_minor_units: int = Field(gt=0)


class ConversionResponse(BaseModel):
    source_wallet: dict
    target_wallet: dict
    exchange_rate: str
    provider: str
    source_transaction: dict
    target_transaction: dict
