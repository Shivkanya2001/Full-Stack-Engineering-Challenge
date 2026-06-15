from pydantic import BaseModel, Field


class CreateWalletRequest(BaseModel):
    currency: str = Field(min_length=3, max_length=3)


class WalletResponse(BaseModel):
    id: str
    user_id: str
    currency: str
    balance_minor_units: int
    balance_display: str
    version: int
    created_at: str


class AmountRequest(BaseModel):
    amount_minor_units: int = Field(gt=0)


class WalletOperationResponse(BaseModel):
    wallet: WalletResponse
    transaction: dict
