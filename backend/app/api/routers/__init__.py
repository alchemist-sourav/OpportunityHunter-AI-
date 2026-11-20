from fastapi import APIRouter

from app.api.routers import auth, credentials, discovery, health, matching, opportunity, profile, public_opportunities, application

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(credentials.router)
api_router.include_router(discovery.router)
api_router.include_router(opportunity.router)
api_router.include_router(matching.router)
api_router.include_router(public_opportunities.router)
api_router.include_router(application.router)

__all__ = ["api_router"]
