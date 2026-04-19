from fastapi import APIRouter

from app.routes.analytics_routes import router as analytics_router
from app.routes.auth_routes import router as auth_router
from app.routes.chat_routes import router as chat_router
from app.routes.dataset_routes import router as dataset_router
from app.routes.health_routes import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dataset_router)
api_router.include_router(chat_router)
api_router.include_router(analytics_router)
