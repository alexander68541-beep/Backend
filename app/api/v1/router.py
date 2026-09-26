from fastapi import APIRouter

from app.api.v1.routes import account, admin, billing, messages as messages_routes, templates as templates_routes, health, media, portfolio, portfolio_data, public, username

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(account.router)
api_router.include_router(portfolio.router)
api_router.include_router(username.router)
api_router.include_router(public.router)
api_router.include_router(media.router)
api_router.include_router(admin.router)
api_router.include_router(billing.router)
api_router.include_router(templates_routes.router)
api_router.include_router(messages_routes.router)
for r in portfolio_data.all_routers:
    api_router.include_router(r)
