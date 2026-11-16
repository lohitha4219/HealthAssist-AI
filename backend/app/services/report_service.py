from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple
import uuid

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

from app.core.config import Settings, get_settings
from app.utils.file_validation import FileValidationError, validate_upload_bytes


class ReportStorageResult:
    def __init__(
        self,
        *,
        original_filename: str,
        stored_filename: str,
        storage_path: str,
        content_type: str,
        file_size: int,
        processing_status: str,
        extracted_text: Optional[str],
        page_count: Optional[int],
        image_width: Optional[int],
        image_height: Optional[int],
    ):
        self.original_filename = original_filename
        self.stored_filename = stored_filename
        self.storage_path = storage_path
        self.content_type = content_type
        self.file_size = file_size
        self.processing_status = processing_status
        self.extracted_text = extracted_text
        self.page_count = page_count
        self.image_width = image_width
        self.image_height = image_height


def _extract_pdf_info(data: bytes) -> Tuple[str, Optional[str], Optional[int]]:
    try:
        reader = PdfReader(BytesIO(data))
        page_count = len(reader.pages)
        extracted_parts = []
        for idx, page in enumerate(reader.pages[:30]):
            text = (page.extract_text() or "").strip()
            if text:
                extracted_parts.append(f"--- Page {idx + 1} ---\n{text}")
        combined = "\n\n".join(extracted_parts).strip()
        if combined:
            return "extracted", combined[:50000], page_count
        return (
            "scanned_no_text",
            None,
            page_count,
        )
    except Exception:
        return "extraction_failed", None, None


def _inspect_image_info(data: bytes) -> Tuple[str, Optional[int], Optional[int]]:
    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
        with Image.open(BytesIO(data)) as img:
            width, height = img.size
        return "image_stored", width, height
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise FileValidationError("Uploaded image file is corrupted or unreadable") from exc


def store_and_process_report(
    *,
    user_id: int,
    filename: str,
    content_type: Optional[str],
    data: bytes,
    settings: Optional[Settings] = None,
) -> ReportStorageResult:
    cfg = settings or get_settings()
    safe_name, ext, canonical_mime = validate_upload_bytes(
        filename=filename,
        content_type=content_type,
        data=data,
        max_bytes=cfg.max_upload_bytes,
    )

    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None

    if canonical_mime == "application/pdf":
        processing_status, extracted_text, page_count = _extract_pdf_info(data)
    else:
        processing_status, image_width, image_height = _inspect_image_info(data)

    user_dir = (cfg.upload_path / str(user_id)).resolve()
    if cfg.upload_path not in user_dir.parents:
        raise FileValidationError("Invalid storage directory path")
    user_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = (user_dir / stored_filename).resolve()
    if user_dir not in dest_path.parents:
        raise FileValidationError("Invalid file destination path")

    dest_path.write_bytes(data)

    return ReportStorageResult(
        original_filename=safe_name,
        stored_filename=stored_filename,
        storage_path=str(dest_path),
        content_type=canonical_mime,
        file_size=len(data),
        processing_status=processing_status,
        extracted_text=extracted_text,
        page_count=page_count,
        image_width=image_width,
        image_height=image_height,
    )


def resolve_safe_report_path(storage_path: str, settings: Optional[Settings] = None) -> Path:
    cfg = settings or get_settings()
    target = Path(storage_path).resolve()
    base = cfg.upload_path.resolve()
    if base not in target.parents:
        raise FileValidationError("Access to file path denied")
    return target
