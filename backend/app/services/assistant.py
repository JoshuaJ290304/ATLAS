from __future__ import annotations

import asyncio
import hashlib
import threading
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.models.assistant import KnowledgeSourceType


@dataclass(frozen=True)
class KnowledgeDraft:
    source_type: KnowledgeSourceType
    source_id: UUID
    source_label: str
    chunk_index: int
    content: str
    content_hash: str
    token_estimate: int
    vector_id: str
    source_metadata: dict[str, object]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    source_type: KnowledgeSourceType
    source_id: UUID
    source_label: str
    chunk_index: int
    excerpt: str
    relevance_score: float
    source_metadata: dict[str, object]


_MODEL: Any | None = None
_MODEL_LOCK = threading.Lock()
_CHROMA_CLIENT: Any | None = None
_CHROMA_COLLECTION: Any | None = None
_CHROMA_LOCK = threading.Lock()


def normalize_text(value: str) -> str:
    lines = [" ".join(line.split()) for line in value.replace("\r\n", "\n").split("\n")]
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line:
            current.append(line)
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs).strip()


def chunk_text(text: str, max_chars: int = 900, overlap_chars: int = 120) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    if max_chars < 200:
        raise ValueError("max_chars must be at least 200")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be non-negative and lower than max_chars")

    chunks: list[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        proposed_end = min(start + max_chars, length)
        end = proposed_end
        if proposed_end < length:
            candidates = [
                cleaned.rfind("\n\n", start + max_chars // 2, proposed_end),
                cleaned.rfind(". ", start + max_chars // 2, proposed_end),
                cleaned.rfind(" ", start + max_chars // 2, proposed_end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + (2 if cleaned[boundary : boundary + 2] in {"\n\n", ". "} else 1)

        chunk = cleaned[start:end].strip()
        if chunk and (not chunks or chunk != chunks[-1]):
            chunks.append(chunk)
        if end >= length:
            break
        next_start = max(0, end - overlap_chars)
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def make_draft(
    *,
    source_type: KnowledgeSourceType,
    source_id: UUID,
    source_label: str,
    chunk_index: int,
    content: str,
    source_metadata: dict[str, object] | None = None,
) -> KnowledgeDraft:
    normalized = normalize_text(content)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    vector_id = f"{source_type.value}:{source_id}:{chunk_index}:{digest[:12]}"
    return KnowledgeDraft(
        source_type=source_type,
        source_id=source_id,
        source_label=source_label,
        chunk_index=chunk_index,
        content=normalized,
        content_hash=digest,
        token_estimate=estimate_tokens(normalized),
        vector_id=vector_id,
        source_metadata=source_metadata or {},
    )


def build_project_drafts(
    documents: list[Any],
    requirements: list[Any],
    artifacts: list[Any],
    impact_analyses: list[Any],
) -> list[KnowledgeDraft]:
    drafts: list[KnowledgeDraft] = []

    for document in documents:
        text = getattr(document, "extracted_text", None) or ""
        for index, chunk in enumerate(
            chunk_text(text, settings.ASSISTANT_CHUNK_SIZE, settings.ASSISTANT_CHUNK_OVERLAP)
        ):
            drafts.append(
                make_draft(
                    source_type=KnowledgeSourceType.DOCUMENT,
                    source_id=document.id,
                    source_label=document.original_filename,
                    chunk_index=index,
                    content=chunk,
                    source_metadata={
                        "filename": document.original_filename,
                        "page_count": document.page_count or 0,
                        "document_status": document.status.value,
                    },
                )
            )

    for requirement in requirements:
        category = requirement.non_functional_category or "not applicable"
        content = (
            f"Requirement {requirement.code}: {requirement.title}\n"
            f"Description: {requirement.description}\n"
            f"Type: {requirement.requirement_type.value}\n"
            f"Category: {category}\n"
            f"Status: {requirement.status.value}\n"
            f"Ambiguity score: {requirement.ambiguity_score}"
        )
        drafts.append(
            make_draft(
                source_type=KnowledgeSourceType.REQUIREMENT,
                source_id=requirement.id,
                source_label=f"{requirement.code} — {requirement.title}",
                chunk_index=0,
                content=content,
                source_metadata={
                    "code": requirement.code,
                    "requirement_type": requirement.requirement_type.value,
                    "status": requirement.status.value,
                    "version": requirement.version,
                },
            )
        )

    for artifact in artifacts:
        details = artifact.technical_details or {}
        detail_lines = ", ".join(f"{key}: {value}" for key, value in sorted(details.items()))
        content = (
            f"Software artifact {artifact.code}: {artifact.name}\n"
            f"Type: {artifact.artifact_type.value}\n"
            f"Description: {artifact.description}\n"
            f"Technical details: {detail_lines or 'None provided'}"
        )
        drafts.append(
            make_draft(
                source_type=KnowledgeSourceType.ARTIFACT,
                source_id=artifact.id,
                source_label=f"{artifact.code} — {artifact.name}",
                chunk_index=0,
                content=content,
                source_metadata={
                    "code": artifact.code,
                    "artifact_type": artifact.artifact_type.value,
                },
            )
        )

    for analysis in impact_analyses:
        direct_names = ", ".join(item.get("name", "") for item in analysis.direct_artifacts)
        transitive_names = ", ".join(
            item.get("name", "") for item in analysis.transitive_artifacts
        )
        content = (
            f"Impact analysis for {analysis.requirement_code}: {analysis.requirement_title}\n"
            f"Versions: {analysis.baseline_version} to {analysis.target_version}\n"
            f"Severity: {analysis.severity.value}; risk score: {analysis.risk_score}/100\n"
            f"Summary: {analysis.change_summary}\n"
            f"Directly affected artifacts: {direct_names or 'None'}\n"
            f"Transitively affected artifacts: {transitive_names or 'None'}"
        )
        drafts.append(
            make_draft(
                source_type=KnowledgeSourceType.IMPACT_ANALYSIS,
                source_id=analysis.id,
                source_label=(
                    f"Impact {analysis.requirement_code} v{analysis.baseline_version}→"
                    f"v{analysis.target_version}"
                ),
                chunk_index=0,
                content=content,
                source_metadata={
                    "requirement_code": analysis.requirement_code,
                    "risk_score": analysis.risk_score,
                    "severity": analysis.severity.value,
                },
            )
        )

    return [draft for draft in drafts if draft.content]


def build_grounded_prompt(
    question: str,
    citations: list[RetrievedChunk],
    history: list[tuple[str, str]],
) -> list[dict[str, str]]:
    context_blocks = []
    for index, citation in enumerate(citations, start=1):
        context_blocks.append(
            f"[{index}] {citation.source_type.value}: {citation.source_label}\n"
            f"{citation.excerpt}"
        )
    context = "\n\n".join(context_blocks) or "No project evidence was retrieved."
    system = (
        "You are ATLAS, a project knowledge assistant. Answer only from the supplied project "
        "evidence. Do not invent requirements, artifacts, APIs, database fields, test cases, or "
        "risk findings. If the evidence is insufficient, say exactly what is missing. Cite claims "
        "using the numbered markers [1], [2], and so on. Keep the answer practical and concise.\n\n"
        f"PROJECT EVIDENCE\n{context}"
    )
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for role, content in history[-6:]:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})
    return messages


def build_retrieval_fallback(question: str, citations: list[RetrievedChunk]) -> str:
    if not citations:
        return (
            "I could not find relevant indexed project evidence for this question. "
            "Rebuild the project index or add more project documents."
        )
    lines = [
        "Ollama is unavailable, so ATLAS is showing the strongest retrieved project evidence "
        f"for: {question}",
    ]
    for index, citation in enumerate(citations[:4], start=1):
        excerpt = citation.excerpt.strip()
        if len(excerpt) > 420:
            excerpt = f"{excerpt[:417].rstrip()}..."
        lines.append(f"[{index}] {citation.source_label}: {excerpt}")
    return "\n\n".join(lines)


def _get_embedding_model() -> Any:
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _MODEL_LOCK:
        if _MODEL is None:
            from sentence_transformers import SentenceTransformer

            Path(settings.MODEL_CACHE_ROOT).mkdir(parents=True, exist_ok=True)
            _MODEL = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                cache_folder=settings.MODEL_CACHE_ROOT,
                device="cpu",
            )
    return _MODEL


def _encode_documents_sync(texts: list[str]) -> list[list[float]]:
    model = _get_embedding_model()
    encoder = getattr(model, "encode_document", model.encode)
    values = encoder(
        texts,
        batch_size=settings.EMBEDDING_BATCH_SIZE,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return values.tolist()


def _encode_query_sync(text: str) -> list[float]:
    model = _get_embedding_model()
    encoder = getattr(model, "encode_query", model.encode)
    value = encoder(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return value.tolist()


async def encode_documents(texts: list[str]) -> list[list[float]]:
    return await asyncio.to_thread(_encode_documents_sync, texts)


async def encode_query(text: str) -> list[float]:
    return await asyncio.to_thread(_encode_query_sync, text)


def _get_collection() -> Any:
    global _CHROMA_CLIENT, _CHROMA_COLLECTION
    if _CHROMA_COLLECTION is not None:
        return _CHROMA_COLLECTION
    with _CHROMA_LOCK:
        if _CHROMA_COLLECTION is None:
            import chromadb

            Path(settings.CHROMA_PERSIST_ROOT).mkdir(parents=True, exist_ok=True)
            _CHROMA_CLIENT = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_ROOT)
            _CHROMA_COLLECTION = _CHROMA_CLIENT.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
    return _CHROMA_COLLECTION


def _metadata_for_draft(project_id: UUID, draft: KnowledgeDraft, chunk_id: UUID) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "project_id": str(project_id),
        "chunk_id": str(chunk_id),
        "source_type": draft.source_type.value,
        "source_id": str(draft.source_id),
        "source_label": draft.source_label,
        "chunk_index": draft.chunk_index,
    }
    for key, value in draft.source_metadata.items():
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
    return metadata


def _replace_project_vectors_sync(
    project_id: UUID,
    drafts: list[KnowledgeDraft],
    chunk_ids: list[UUID],
    embeddings: list[list[float]],
) -> None:
    collection = _get_collection()
    collection.delete(where={"project_id": str(project_id)})
    batch_size = 128
    for start in range(0, len(drafts), batch_size):
        end = min(start + batch_size, len(drafts))
        collection.upsert(
            ids=[draft.vector_id for draft in drafts[start:end]],
            embeddings=embeddings[start:end],
            documents=[draft.content for draft in drafts[start:end]],
            metadatas=[
                _metadata_for_draft(project_id, draft, chunk_id)
                for draft, chunk_id in zip(
                    drafts[start:end],
                    chunk_ids[start:end],
                    strict=True,
                )
            ],
        )


async def replace_project_vectors(
    project_id: UUID,
    drafts: list[KnowledgeDraft],
    chunk_ids: list[UUID],
    embeddings: list[list[float]],
) -> None:
    await asyncio.to_thread(
        _replace_project_vectors_sync,
        project_id,
        drafts,
        chunk_ids,
        embeddings,
    )


def _delete_project_vectors_sync(project_id: UUID) -> None:
    collection = _get_collection()
    collection.delete(where={"project_id": str(project_id)})


async def delete_project_vectors(project_id: UUID) -> None:
    try:
        await asyncio.to_thread(_delete_project_vectors_sync, project_id)
    except Exception:
        # Database cascade remains authoritative; a later reindex removes stale vectors.
        return


def _query_project_sync(
    project_id: UUID, embedding: list[float], top_k: int
) -> list[RetrievedChunk]:
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []
    result = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, count),
        where={"project_id": str(project_id)},
        include=["documents", "metadatas", "distances"],
    )
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    retrieved: list[RetrievedChunk] = []
    for document, metadata, distance in zip(documents, metadatas, distances, strict=False):
        if not metadata:
            continue
        score = max(0.0, min(1.0, 1.0 - float(distance)))
        raw_metadata = dict(metadata)
        base_keys = {
            "project_id",
            "chunk_id",
            "source_type",
            "source_id",
            "source_label",
            "chunk_index",
        }
        source_metadata = {
            key: value for key, value in raw_metadata.items() if key not in base_keys
        }
        retrieved.append(
            RetrievedChunk(
                chunk_id=UUID(str(raw_metadata["chunk_id"])),
                source_type=KnowledgeSourceType(str(raw_metadata["source_type"])),
                source_id=UUID(str(raw_metadata["source_id"])),
                source_label=str(raw_metadata["source_label"]),
                chunk_index=int(raw_metadata["chunk_index"]),
                excerpt=str(document),
                relevance_score=round(score, 4),
                source_metadata=source_metadata,
            )
        )
    return retrieved


async def query_project(project_id: UUID, question: str, top_k: int) -> list[RetrievedChunk]:
    embedding = await encode_query(question)
    return await asyncio.to_thread(_query_project_sync, project_id, embedding, top_k)


def citation_to_dict(citation: RetrievedChunk) -> dict[str, object]:
    return {
        "chunk_id": str(citation.chunk_id),
        "source_type": citation.source_type.value,
        "source_id": str(citation.source_id),
        "source_label": citation.source_label,
        "chunk_index": citation.chunk_index,
        "excerpt": citation.excerpt,
        "relevance_score": citation.relevance_score,
        "source_metadata": citation.source_metadata,
    }


async def ollama_status() -> tuple[bool, bool, str]:
    try:
        from ollama import AsyncClient

        client = AsyncClient(
            host=settings.OLLAMA_BASE_URL,
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
        )
        response = await client.list()
        models = getattr(response, "models", None)
        if models is None and isinstance(response, dict):
            models = response.get("models", [])
        names: list[str] = []
        for model in models or []:
            name = getattr(model, "model", None) or getattr(model, "name", None)
            if name is None and isinstance(model, dict):
                name = model.get("model") or model.get("name")
            if name:
                names.append(str(name))
        requested = settings.OLLAMA_MODEL
        available = requested in names or any(name.split(":")[0] == requested for name in names)
        return True, available, f"Ollama is reachable with {len(names)} installed model(s)."
    except Exception as exc:
        return False, False, f"Ollama is unavailable: {type(exc).__name__}"


async def generate_ollama_answer(
    question: str,
    citations: list[RetrievedChunk],
    history: list[tuple[str, str]],
) -> tuple[str, int]:
    from ollama import AsyncClient

    client = AsyncClient(
        host=settings.OLLAMA_BASE_URL,
        timeout=settings.OLLAMA_GENERATION_TIMEOUT_SECONDS,
    )
    started = perf_counter()
    response = await client.chat(
        model=settings.OLLAMA_MODEL,
        messages=build_grounded_prompt(question, citations, history),
        stream=False,
        options={
            "temperature": settings.OLLAMA_TEMPERATURE,
            "num_ctx": settings.OLLAMA_CONTEXT_WINDOW,
        },
    )
    latency_ms = round((perf_counter() - started) * 1000)
    message = getattr(response, "message", None)
    content = getattr(message, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("message", {}).get("content")
    if not content:
        raise RuntimeError("Ollama returned an empty response")
    return str(content).strip(), latency_ms


def new_chunk_id() -> UUID:
    return uuid4()
