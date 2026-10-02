from pathlib import Path
import re
from uuid import uuid4

from fastapi import UploadFile

RESUME_DIRECTORY = Path("var/resumes")
MAX_RESUME_BYTES = 5 * 1024 * 1024
_STORAGE_KEY_PATTERN = re.compile(r"^[a-f0-9]{32}\.pdf$")


async def save_resume(upload: UploadFile) -> str:
    filename = upload.filename or ""
    if Path(filename).suffix.lower() != ".pdf":
        raise ValueError("Upload a PDF file.")

    content = await upload.read(MAX_RESUME_BYTES + 1)
    if len(content) > MAX_RESUME_BYTES:
        raise ValueError("The PDF must be 5 MB or smaller.")
    if not content.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a valid PDF.")

    RESUME_DIRECTORY.mkdir(parents=True, exist_ok=True)
    storage_key = f"{uuid4().hex}.pdf"
    (RESUME_DIRECTORY / storage_key).write_bytes(content)
    return storage_key


def delete_resume(storage_key: str) -> None:
    if not _STORAGE_KEY_PATTERN.fullmatch(storage_key):
        return
    (RESUME_DIRECTORY / storage_key).unlink(missing_ok=True)