from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, auth

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["Health & Diagnostics"])
api_v1_router.include_router(auth.router, tags=["Authentication & Identity"])
