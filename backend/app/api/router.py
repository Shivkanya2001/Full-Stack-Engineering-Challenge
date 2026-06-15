from fastapi import APIRouter

from app.api.v1 import auth, conversions, exchange_rates, transactions, transfers, wallets

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(wallets.router, prefix="/wallets", tags=["wallets"])
api_router.include_router(conversions.router, prefix="/conversions", tags=["conversions"])
api_router.include_router(exchange_rates.router, prefix="/exchange-rates", tags=["exchange-rates"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
