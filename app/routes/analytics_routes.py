from fastapi import APIRouter, Depends

from app.controllers.analytics_controller import AnalyticsController
from app.dependencies import get_analytics_service, get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsOverviewResponse
from app.schemas.common import SuccessResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_controller(analytics_service: AnalyticsService = Depends(get_analytics_service)):
    return AnalyticsController(analytics_service)


@router.get("/overview", response_model=SuccessResponse[AnalyticsOverviewResponse])
async def analytics_overview(
    _: User = Depends(get_current_user),
    controller: AnalyticsController = Depends(get_analytics_controller),
):
    return SuccessResponse(data=await controller.overview())
