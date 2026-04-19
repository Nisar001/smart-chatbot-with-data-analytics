from app.schemas.analytics import AnalyticsOverviewResponse
from app.services.analytics_service import AnalyticsService


class AnalyticsController:
    def __init__(self, analytics_service: AnalyticsService):
        self.analytics_service = analytics_service

    async def overview(self) -> AnalyticsOverviewResponse:
        return await self.analytics_service.get_overview()
