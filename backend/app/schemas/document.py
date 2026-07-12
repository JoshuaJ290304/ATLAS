from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    original_filename: str
    media_type: str
    file_extension: str
    size_bytes: int
    checksum_sha256: str
    status: DocumentStatus
    page_count: int | None
    character_count: int
    extraction_error: str | None
    created_at: datetime
    updated_at: datetime


class DocumentTextRead(BaseModel):
    document_id: UUID
    original_filename: str
    character_count: int
    extracted_text: str
