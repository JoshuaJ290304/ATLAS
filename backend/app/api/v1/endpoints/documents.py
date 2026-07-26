from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.projects import get_owned_project
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentRead, DocumentTextRead
from app.services.admin import get_platform_settings
from app.services.documents import (
    extract_document,
    resolve_stored_path,
    store_upload,
    validate_file_signature,
)

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


async def get_owned_document(
    db: DbSession,
    project_id: UUID,
    document_id: UUID,
    owner_id: UUID,
) -> Document:
    result = await db.execute(
        select(Document)
        .join(Document.project)
        .where(
            Document.id == document_id,
            Document.project_id == project_id,
            Document.project.has(owner_id=owner_id),
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    file: Annotated[UploadFile, File()],
) -> Document:
    await get_owned_project(db, project_id, current_user.id)
    platform = await get_platform_settings(db)
    stored = await store_upload(
        file,
        project_id,
        max_size_mb=platform.max_upload_size_mb,
        extensions=set(platform.allowed_document_extensions),
    )
    try:
        validate_file_signature(stored.storage_path, stored.extension)
    except HTTPException:
        stored.storage_path.unlink(missing_ok=True)
        raise

    document = Document(
        project_id=project_id,
        original_filename=stored.original_filename,
        stored_filename=stored.stored_filename,
        storage_path=str(stored.storage_path),
        media_type=stored.media_type,
        file_extension=stored.extension,
        size_bytes=stored.size_bytes,
        checksum_sha256=stored.checksum_sha256,
        status=DocumentStatus.UPLOADED,
    )
    db.add(document)

    try:
        extraction = await extract_document(stored.storage_path, stored.extension)
        document.extracted_text = extraction.text
        document.character_count = len(extraction.text)
        document.page_count = extraction.page_count
        document.status = DocumentStatus.EXTRACTED
    except Exception as exc:  # Parser errors must be visible without exposing internals.
        document.status = DocumentStatus.FAILED
        document.extraction_error = f"Text extraction failed: {type(exc).__name__}"

    await db.commit()
    await db.refresh(document)
    return document


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[Document]:
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentRead)
async def read_document(
    project_id: UUID,
    document_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Document:
    return await get_owned_document(db, project_id, document_id, current_user.id)


@router.get("/{document_id}/text", response_model=DocumentTextRead)
async def read_document_text(
    project_id: UUID,
    document_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> DocumentTextRead:
    document = await get_owned_document(db, project_id, document_id, current_user.id)
    if document.status != DocumentStatus.EXTRACTED or document.extracted_text is None:
        raise HTTPException(status_code=409, detail="Extracted text is not available")
    return DocumentTextRead(
        document_id=document.id,
        original_filename=document.original_filename,
        character_count=document.character_count,
        extracted_text=document.extracted_text,
    )


@router.get("/{document_id}/download")
async def download_document(
    project_id: UUID,
    document_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> FileResponse:
    document = await get_owned_document(db, project_id, document_id, current_user.id)
    path = resolve_stored_path(document.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored file not found")
    return FileResponse(
        path=path,
        media_type=document.media_type,
        filename=document.original_filename,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    document = await get_owned_document(db, project_id, document_id, current_user.id)
    path = resolve_stored_path(document.storage_path)
    await db.delete(document)
    await db.commit()
    path.unlink(missing_ok=True)
    _remove_empty_parent(path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _remove_empty_parent(path: Path) -> None:
    try:
        path.parent.rmdir()
    except OSError:
        pass
