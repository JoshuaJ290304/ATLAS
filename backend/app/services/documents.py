from __future__ import annotations

import asyncio
import hashlib
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

import fitz
from docx import Document as DocxDocument
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

CHUNK_SIZE = 1024 * 1024
MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass(frozen=True)
class StoredUpload:
    original_filename: str
    stored_filename: str
    storage_path: Path
    media_type: str
    extension: str
    size_bytes: int
    checksum_sha256: str


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    page_count: int | None


def clean_filename(filename: str | None) -> str:
    cleaned = Path((filename or "").replace("\\", "/")).name.strip()
    if not cleaned or cleaned in {".", ".."}:
        raise HTTPException(status_code=400, detail="A valid filename is required")
    return cleaned


def allowed_extensions() -> set[str]:
    return {
        extension.strip().lower()
        for extension in settings.ALLOWED_DOCUMENT_EXTENSIONS.split(",")
        if extension.strip()
    }


def validate_extension(filename: str, extensions: set[str] | None = None) -> str:
    configured = extensions or allowed_extensions()
    extension = Path(filename).suffix.lower()
    if extension not in configured:
        allowed = ", ".join(sorted(configured))
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed extensions: {allowed}",
        )
    return extension


def upload_root() -> Path:
    root = Path(settings.UPLOAD_ROOT).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def project_upload_directory(project_id: UUID) -> Path:
    directory = upload_root() / str(project_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def resolve_stored_path(storage_path: str) -> Path:
    root = upload_root()
    candidate = Path(storage_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Invalid document storage path") from exc
    return candidate


def validate_file_signature(path: Path, extension: str) -> None:
    if extension == ".pdf":
        with path.open("rb") as source:
            if source.read(5) != b"%PDF-":
                raise HTTPException(status_code=422, detail="The file is not a valid PDF")
        return

    if extension == ".docx":
        if not zipfile.is_zipfile(path):
            raise HTTPException(status_code=422, detail="The file is not a valid DOCX document")
        with zipfile.ZipFile(path) as archive:
            if "word/document.xml" not in archive.namelist():
                raise HTTPException(status_code=422, detail="The file is not a valid DOCX document")
        return

    raise HTTPException(status_code=415, detail="Unsupported document type")


def remove_project_upload_directory(project_id: UUID) -> None:
    directory = upload_root() / str(project_id)
    if directory.is_dir():
        shutil.rmtree(directory)


async def store_upload(
    upload: UploadFile,
    project_id: UUID,
    *,
    max_size_mb: int | None = None,
    extensions: set[str] | None = None,
) -> StoredUpload:
    original_filename = clean_filename(upload.filename)
    extension = validate_extension(original_filename, extensions)
    stored_filename = f"{uuid4().hex}{extension}"
    destination = project_upload_directory(project_id) / stored_filename
    effective_max_mb = max_size_mb or settings.MAX_UPLOAD_SIZE_MB
    max_bytes = effective_max_mb * 1024 * 1024
    size_bytes = 0
    checksum = hashlib.sha256()

    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(CHUNK_SIZE):
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds the {effective_max_mb} MB limit",
                    )
                checksum.update(chunk)
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    if size_bytes == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    return StoredUpload(
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=destination,
        media_type=MEDIA_TYPES[extension],
        extension=extension,
        size_bytes=size_bytes,
        checksum_sha256=checksum.hexdigest(),
    )


def _extract_pdf(path: Path) -> ExtractionResult:
    with fitz.open(path) as pdf:
        text = "\n\n".join(page.get_text("text").strip() for page in pdf).strip()
        return ExtractionResult(text=text, page_count=pdf.page_count)


def _extract_docx(path: Path) -> ExtractionResult:
    document = DocxDocument(path)
    parts: list[str] = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)

    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            line = " | ".join(value for value in cells if value)
            if line:
                parts.append(line)

    return ExtractionResult(text="\n".join(parts).strip(), page_count=None)


async def extract_document(path: Path, extension: str) -> ExtractionResult:
    if extension == ".pdf":
        return await asyncio.to_thread(_extract_pdf, path)
    if extension == ".docx":
        return await asyncio.to_thread(_extract_docx, path)
    raise ValueError(f"Unsupported extension: {extension}")
