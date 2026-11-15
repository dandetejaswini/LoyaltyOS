from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    auth,
    accounts,
    orders,
    ledger,
    redemptions,
    returns,
    expiry,
    tiers,
    intelligence,
    corrective_actions,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["Health & Diagnostics"])
api_v1_router.include_router(auth.router, tags=["Authentication & Identity"])
api_v1_router.include_router(accounts.router)
api_v1_router.include_router(orders.router)
api_v1_router.include_router(ledger.router)
api_v1_router.include_router(redemptions.router)
api_v1_router.include_router(returns.router)
api_v1_router.include_router(expiry.router)
api_v1_router.include_router(tiers.router)
api_v1_router.include_router(intelligence.router)
api_v1_router.include_router(corrective_actions.router)
