from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.projects import get_owned_project
from app.core.config import settings
from app.models.artifact import Artifact
from app.models.assistant import (
    AssistantConversation,
    AssistantIndex,
    AssistantIndexStatus,
    AssistantMessage,
    AssistantMessageRole,
    KnowledgeChunk,
)
from app.models.document import Document, DocumentStatus
from app.models.impact import ImpactAnalysis
from app.models.requirement import Requirement
from app.schemas.assistant import (
    AssistantAskRead,
    AssistantAskRequest,
    AssistantCitationRead,
    AssistantConversationDetailRead,
    AssistantConversationRead,
    AssistantIndexRead,
    AssistantMessageRead,
    AssistantStatusRead,
    SemanticSearchRead,
    SemanticSearchRequest,
)
from app.services.admin import get_platform_settings
from app.services.assistant import (
    build_project_drafts,
    build_retrieval_fallback,
    citation_to_dict,
    delete_project_vectors,
    encode_documents,
    generate_ollama_answer,
    new_chunk_id,
    ollama_status,
    query_project,
    replace_project_vectors,
)

router = APIRouter(prefix="/projects/{project_id}/assistant", tags=["AI project assistant"])


async def get_or_create_index(db: DbSession, project_id: UUID) -> AssistantIndex:
    result = await db.execute(select(AssistantIndex).where(AssistantIndex.project_id == project_id))
    index = result.scalar_one_or_none()
    if index is None:
        index = AssistantIndex(
            project_id=project_id,
            status=AssistantIndexStatus.NOT_INDEXED,
            embedding_model=settings.EMBEDDING_MODEL,
        )
        db.add(index)
        await db.flush()
    return index


async def get_owned_conversation(
    db: DbSession,
    project_id: UUID,
    conversation_id: UUID,
    owner_id: UUID,
    *,
    load_messages: bool = False,
) -> AssistantConversation:
    query = select(AssistantConversation).where(
        AssistantConversation.id == conversation_id,
        AssistantConversation.project_id == project_id,
        AssistantConversation.owner_id == owner_id,
    )
    if load_messages:
        query = query.options(selectinload(AssistantConversation.messages))
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Assistant conversation not found")
    return conversation


async def ensure_ready_index(db: DbSession, project_id: UUID) -> AssistantIndex:
    index = await get_or_create_index(db, project_id)
    if index.status != AssistantIndexStatus.READY or index.chunk_count == 0:
        raise HTTPException(
            status_code=409,
            detail="Build the project knowledge index before using semantic search or chat",
        )
    return index


async def ensure_ai_enabled(db: DbSession) -> None:
    platform = await get_platform_settings(db)
    if not platform.ai_generation_enabled:
        raise HTTPException(
            status_code=503, detail="AI generation is disabled by a platform administrator"
        )


@router.get("/status", response_model=AssistantStatusRead)
async def read_assistant_status(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AssistantStatusRead:
    await get_owned_project(db, project_id, current_user.id)
    index = await get_or_create_index(db, project_id)
    await db.commit()
    await db.refresh(index)
    available, model_available, message = await ollama_status()
    return AssistantStatusRead(
        index=AssistantIndexRead.model_validate(index),
        ollama_available=available,
        model_available=model_available,
        model_name=settings.OLLAMA_MODEL,
        embedding_model=settings.EMBEDDING_MODEL,
        retrieval_fallback_enabled=settings.ASSISTANT_ALLOW_RETRIEVAL_FALLBACK,
        status_message=message,
    )


@router.post("/index", response_model=AssistantIndexRead)
async def rebuild_project_index(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AssistantIndex:
    await get_owned_project(db, project_id, current_user.id)
    await ensure_ai_enabled(db)
    index = await get_or_create_index(db, project_id)
    index.status = AssistantIndexStatus.INDEXING
    index.last_error = None
    index.embedding_model = settings.EMBEDDING_MODEL
    await db.commit()

    try:
        documents_result = await db.execute(
            select(Document).where(
                Document.project_id == project_id,
                Document.status == DocumentStatus.EXTRACTED,
                Document.extracted_text.is_not(None),
            )
        )
        requirements_result = await db.execute(
            select(Requirement).where(Requirement.project_id == project_id)
        )
        artifacts_result = await db.execute(
            select(Artifact).where(Artifact.project_id == project_id)
        )
        impacts_result = await db.execute(
            select(ImpactAnalysis).where(ImpactAnalysis.project_id == project_id)
        )
        drafts = build_project_drafts(
            list(documents_result.scalars().all()),
            list(requirements_result.scalars().all()),
            list(artifacts_result.scalars().all()),
            list(impacts_result.scalars().all()),
        )
        if not drafts:
            raise ValueError("No extracted documents or project records are available to index")

        embeddings = await encode_documents([draft.content for draft in drafts])
        chunk_ids = [new_chunk_id() for _ in drafts]
        await replace_project_vectors(project_id, drafts, chunk_ids, embeddings)

        await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.project_id == project_id))
        now = datetime.now(UTC)
        db.add_all(
            [
                KnowledgeChunk(
                    id=chunk_id,
                    project_id=project_id,
                    source_type=draft.source_type,
                    source_id=draft.source_id,
                    source_label=draft.source_label,
                    chunk_index=draft.chunk_index,
                    content=draft.content,
                    content_hash=draft.content_hash,
                    token_estimate=draft.token_estimate,
                    vector_id=draft.vector_id,
                    source_metadata=draft.source_metadata,
                    created_at=now,
                )
                for draft, chunk_id in zip(drafts, chunk_ids, strict=True)
            ]
        )
        index = await get_or_create_index(db, project_id)
        index.status = AssistantIndexStatus.READY
        index.source_count = len({(draft.source_type, draft.source_id) for draft in drafts})
        index.chunk_count = len(drafts)
        index.embedding_model = settings.EMBEDDING_MODEL
        index.last_indexed_at = now
        index.last_error = None
        await db.commit()
        await db.refresh(index)
        return index
    except Exception as exc:
        await db.rollback()
        failed_index = await get_or_create_index(db, project_id)
        failed_index.status = AssistantIndexStatus.FAILED
        failed_index.last_error = f"Indexing failed: {type(exc).__name__}: {str(exc)[:300]}"
        await db.commit()
        raise HTTPException(status_code=503, detail=failed_index.last_error) from exc


@router.post("/search", response_model=SemanticSearchRead)
async def semantic_search(
    project_id: UUID,
    payload: SemanticSearchRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> SemanticSearchRead:
    await get_owned_project(db, project_id, current_user.id)
    await ensure_ai_enabled(db)
    await ensure_ready_index(db, project_id)
    results = await query_project(project_id, payload.query.strip(), payload.top_k)
    return SemanticSearchRead(
        query=payload.query.strip(),
        results=[AssistantCitationRead(**citation_to_dict(item)) for item in results],
    )


@router.post("/ask", response_model=AssistantAskRead, status_code=status.HTTP_201_CREATED)
async def ask_project_assistant(
    project_id: UUID,
    payload: AssistantAskRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> AssistantAskRead:
    await get_owned_project(db, project_id, current_user.id)
    await ensure_ai_enabled(db)
    await ensure_ready_index(db, project_id)
    question = payload.question.strip()
    citations = await query_project(project_id, question, payload.top_k)

    if payload.conversation_id is None:
        title = question if len(question) <= 80 else f"{question[:77].rstrip()}..."
        conversation = AssistantConversation(
            project_id=project_id,
            owner_id=current_user.id,
            title=title,
            model_name=settings.OLLAMA_MODEL,
        )
        db.add(conversation)
        await db.flush()
        history: list[tuple[str, str]] = []
    else:
        conversation = await get_owned_conversation(
            db,
            project_id,
            payload.conversation_id,
            current_user.id,
        )
        history_result = await db.execute(
            select(AssistantMessage)
            .where(AssistantMessage.conversation_id == conversation.id)
            .order_by(AssistantMessage.created_at.desc())
            .limit(8)
        )
        recent = list(reversed(list(history_result.scalars().all())))
        history = [(item.role.value, item.content) for item in recent]

    used_fallback = False
    latency_ms: int | None = None
    try:
        answer, latency_ms = await generate_ollama_answer(question, citations, history)
    except Exception as exc:
        if not settings.ASSISTANT_ALLOW_RETRIEVAL_FALLBACK:
            await db.rollback()
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Ollama generation failed: {type(exc).__name__}. "
                    "Start Ollama and pull the configured model."
                ),
            ) from exc
        answer = build_retrieval_fallback(question, citations)
        used_fallback = True

    citation_payload = [citation_to_dict(item) for item in citations]
    now = datetime.now(UTC)
    user_message = AssistantMessage(
        conversation_id=conversation.id,
        role=AssistantMessageRole.USER,
        content=question,
        citations=[],
        created_at=now,
    )
    assistant_message = AssistantMessage(
        conversation_id=conversation.id,
        role=AssistantMessageRole.ASSISTANT,
        content=answer,
        citations=citation_payload,
        model_name=("retrieval-fallback" if used_fallback else settings.OLLAMA_MODEL),
        latency_ms=latency_ms,
        created_at=datetime.now(UTC),
    )
    conversation.model_name = settings.OLLAMA_MODEL
    conversation.updated_at = datetime.now(UTC)
    db.add_all([user_message, assistant_message])
    await db.commit()
    await db.refresh(conversation)
    await db.refresh(user_message)
    await db.refresh(assistant_message)

    return AssistantAskRead(
        conversation=AssistantConversationRead.model_validate(conversation),
        user_message=AssistantMessageRead.model_validate(user_message),
        assistant_message=AssistantMessageRead.model_validate(assistant_message),
        citations=[AssistantCitationRead(**item) for item in citation_payload],
        model_name=settings.OLLAMA_MODEL,
        used_retrieval_fallback=used_fallback,
    )


@router.get("/conversations", response_model=list[AssistantConversationRead])
async def list_conversations(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[AssistantConversation]:
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(AssistantConversation)
        .where(
            AssistantConversation.project_id == project_id,
            AssistantConversation.owner_id == current_user.id,
        )
        .order_by(AssistantConversation.updated_at.desc())
    )
    return list(result.scalars().all())


@router.get(
    "/conversations/{conversation_id}",
    response_model=AssistantConversationDetailRead,
)
async def read_conversation(
    project_id: UUID,
    conversation_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AssistantConversation:
    await get_owned_project(db, project_id, current_user.id)
    return await get_owned_conversation(
        db,
        project_id,
        conversation_id,
        current_user.id,
        load_messages=True,
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    project_id: UUID,
    conversation_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    await get_owned_project(db, project_id, current_user.id)
    conversation = await get_owned_conversation(
        db,
        project_id,
        conversation_id,
        current_user.id,
    )
    await db.delete(conversation)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/index", status_code=status.HTTP_204_NO_CONTENT)
async def clear_project_index(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    await get_owned_project(db, project_id, current_user.id)
    await delete_project_vectors(project_id)
    await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.project_id == project_id))
    index = await get_or_create_index(db, project_id)
    index.status = AssistantIndexStatus.NOT_INDEXED
    index.source_count = 0
    index.chunk_count = 0
    index.last_indexed_at = None
    index.last_error = None
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
