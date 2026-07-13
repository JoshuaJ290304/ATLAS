from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.assistant import (
    AssistantIndexStatus,
    AssistantMessageRole,
    KnowledgeSourceType,
)


class AssistantIndexRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: UUID
    status: AssistantIndexStatus
    source_count: int
    chunk_count: int
    embedding_model: str
    last_indexed_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class AssistantStatusRead(BaseModel):
    index: AssistantIndexRead
    ollama_available: bool
    model_available: bool
    model_name: str
    embedding_model: str
    retrieval_fallback_enabled: bool
    status_message: str


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)


class AssistantCitationRead(BaseModel):
    chunk_id: UUID
    source_type: KnowledgeSourceType
    source_id: UUID
    source_label: str
    chunk_index: int
    excerpt: str
    relevance_score: float = Field(ge=0, le=1)
    source_metadata: dict[str, object] = Field(default_factory=dict)


class SemanticSearchRead(BaseModel):
    query: str
    results: list[AssistantCitationRead]


class AssistantMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: AssistantMessageRole
    content: str
    citations: list[AssistantCitationRead]
    model_name: str | None
    latency_ms: int | None
    created_at: datetime


class AssistantConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    owner_id: UUID
    title: str
    model_name: str
    created_at: datetime
    updated_at: datetime


class AssistantConversationDetailRead(AssistantConversationRead):
    messages: list[AssistantMessageRead]


class AssistantAskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    conversation_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=8)


class AssistantAskRead(BaseModel):
    conversation: AssistantConversationRead
    user_message: AssistantMessageRead
    assistant_message: AssistantMessageRead
    citations: list[AssistantCitationRead]
    model_name: str
    used_retrieval_fallback: bool
