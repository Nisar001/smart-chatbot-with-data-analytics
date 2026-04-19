from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    DatasetUsageStat,
    LatencyStat,
    QueryStat,
)


class AnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepository):
        self.analytics_repository = analytics_repository

    async def get_overview(self) -> AnalyticsOverviewResponse:
        query_rows = await self.analytics_repository.most_asked_queries()
        dataset_rows = await self.analytics_repository.dataset_usage_stats()
        latency_row = await self.analytics_repository.latency_stats()

        return AnalyticsOverviewResponse(
            most_asked_queries=[
                QueryStat(query=row[0], count=row[1]) for row in query_rows
            ],
            dataset_usage=[
                DatasetUsageStat(
                    dataset_id=str(row[0]),
                    dataset_name=row[1],
                    conversation_count=row[2],
                )
                for row in dataset_rows
            ],
            response_latency=LatencyStat(
                average_ms=float(latency_row[0]) if latency_row[0] is not None else None,
                max_ms=float(latency_row[1]) if latency_row[1] is not None else None,
                min_ms=float(latency_row[2]) if latency_row[2] is not None else None,
            ),
        )
