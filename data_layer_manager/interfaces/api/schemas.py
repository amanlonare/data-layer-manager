from typing import Any

from pydantic import BaseModel, Field

from data_layer_manager.domain.schemas.strategy import SearchStrategyConfig


class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query string")
    limit: int = Field(
        10, ge=1, le=100, description="Maximum number of results to return"
    )
    filters: dict[str, Any] | None = Field(
        None, description="Metadata filters to apply"
    )
    strategy: SearchStrategyConfig = Field(
        default_factory=SearchStrategyConfig,
        description="Structured retrieval strategy and parameters",
    )


class SearchResponse(BaseModel):
    results: list[dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    content: str = Field(..., description="The text content to ingest")
    metadata: dict[str, Any] | None = Field(
        None, description="Metadata for the document"
    )
    source: str | None = Field(None, description="Source of the content")


class IngestResponse(BaseModel):
    task_id: str
    status: str = "accepted"
    message: str | None = None
    document_id: str | None = None
    chunk_count: int | None = None
