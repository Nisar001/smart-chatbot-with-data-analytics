from pydantic import BaseModel


class QueryStat(BaseModel):
    query: str
    count: int


class DatasetUsageStat(BaseModel):
    dataset_id: str
    dataset_name: str
    conversation_count: int


class LatencyStat(BaseModel):
    average_ms: float | None
    max_ms: float | None
    min_ms: float | None


class AnalyticsOverviewResponse(BaseModel):
    most_asked_queries: list[QueryStat]
    dataset_usage: list[DatasetUsageStat]
    response_latency: LatencyStat
