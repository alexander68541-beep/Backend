from fastapi import APIRouter

from app.api.v1.routes import account, health, portfolio, username

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(account.router)
api_router.include_router(portfolio.router)
api_router.include_router(username.router)
