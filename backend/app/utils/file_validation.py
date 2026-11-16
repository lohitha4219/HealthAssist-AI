from pathlib import Path
import re
from typing import Tuple

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}

EXTENSION_MIME_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class FileValidationError(ValueError):
    pass


def sanitize_filename(filename: str) -> str:
    base = Path(filename or "report").name
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", base).strip(" .")
    return (cleaned[:180] or "report")


def detect_magic_type(data: bytes) -> str:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "unknown"


def validate_upload_bytes(
    filename: str,
    content_type: str | None,
    data: bytes,
    max_bytes: int,
) -> Tuple[str, str, str]:
    """Validate uploaded file extension, size, and magic header.

    Returns (sanitized_filename, extension, canonical_mime_type).
    """
    if not data:
        raise FileValidationError("Uploaded file is empty")
    if len(data) > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise FileValidationError(f"File exceeds maximum allowed size of {max_mb} MB")

    safe_name = sanitize_filename(filename)
    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            "Unsupported file extension. Allowed formats: PDF, PNG, JPG, JPEG, WEBP"
        )

    expected_mime = EXTENSION_MIME_MAP[ext]
    detected_mime = detect_magic_type(data)
    if detected_mime != expected_mime:
        raise FileValidationError(
            "File contents do not match the declared file format"
        )

    if content_type:
        norm_ct = content_type.split(";")[0].strip().lower()
        allowed_aliases = {expected_mime}
        if expected_mime == "image/jpeg":
            allowed_aliases.add("image/jpg")
        if norm_ct not in allowed_aliases and norm_ct != "application/octet-stream":
            raise FileValidationError(
                f"Content type '{norm_ct}' does not match '{expected_mime}'"
            )

    return safe_name, ext, expected_mime
