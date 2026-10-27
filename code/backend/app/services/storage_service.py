"""Local file storage for avatars and resumes.

Files land on disk under MEDIA_ROOT and only the relative path is stored in the
database, so swapping in object storage later is a change to this module alone.

ponytail: local disk is right for one process; move to S3/MinIO the moment there
is a second app instance, because these files would not be shared between them.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import FileTooLarge, UnsupportedFileType

# Magic bytes, not the client-supplied content type. A browser will happily
# label a .exe as image/png; the first bytes of the file will not lie.
IMAGE_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)
PDF_SIGNATURE = b"%PDF-"

CHUNK = 64 * 1024


def _detect_image(head: bytes) -> str | None:
    for signature, extension in IMAGE_SIGNATURES:
        if head.startswith(signature):
            return extension
    # WEBP is "RIFF....WEBP"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def _media_root() -> Path:
    return Path(settings.media_root)


def public_url(relative_path: str | None) -> str | None:
    return f"/media/{relative_path}" if relative_path else None


def _save(upload: UploadFile, folder: str, extension: str, max_bytes: int) -> str:
    directory = _media_root() / folder
    directory.mkdir(parents=True, exist_ok=True)

    # The client's filename is never used: it is attacker-controlled and can
    # carry path separators or a second extension.
    relative = f"{folder}/{uuid.uuid4().hex}.{extension}"
    destination = _media_root() / relative

    written = 0
    upload.file.seek(0)
    with destination.open("wb") as out:
        while chunk := upload.file.read(CHUNK):
            written += len(chunk)
            if written > max_bytes:
                out.close()
                destination.unlink(missing_ok=True)
                raise FileTooLarge(f"File must be at most {max_bytes // (1024 * 1024)} MB.")
            out.write(chunk)

    return relative


def save_avatar(upload: UploadFile) -> str:
    head = upload.file.read(16)
    extension = _detect_image(head)
    if extension is None:
        raise UnsupportedFileType("Profile picture must be a JPEG, PNG, GIF or WEBP image.")
    return _save(upload, "avatars", extension, settings.max_avatar_bytes)


def save_resume(upload: UploadFile) -> str:
    head = upload.file.read(8)
    if not head.startswith(PDF_SIGNATURE):
        raise UnsupportedFileType("Resume must be a PDF file.")
    return _save(upload, "resumes", "pdf", settings.max_resume_bytes)


def delete(relative_path: str | None) -> None:
    """Best effort. A leftover file is harmless; a crash mid-replace is not."""
    if not relative_path:
        return
    (_media_root() / relative_path).unlink(missing_ok=True)
