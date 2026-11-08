"""Unit test for the résumé upload check (UT-04)."""
import io

import pytest
from fastapi import UploadFile

from app.utilities.resume_storage import save_resume


async def test_ut04_non_pdf_resume_is_rejected(resume_dir):
    upload = UploadFile(filename="photo.jpg", file=io.BytesIO(b"not a pdf"))

    with pytest.raises(ValueError, match="Upload a PDF file."):
        await save_resume(upload)

    assert not resume_dir.exists() or not any(resume_dir.iterdir())
