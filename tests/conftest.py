"""Shared pytest setup.

Points the app at a throwaway SQLite database *before* the app is imported,
so the tests never touch database.db or the Render Postgres database.
"""
import os
import tempfile
from pathlib import Path

_TEST_DIR = Path(tempfile.mkdtemp(prefix="internship-tests-"))
os.environ["DATABASE_URI"] = f"sqlite:///{(_TEST_DIR / 'test.db').as_posix()}"
os.environ["ENV"] = "testing-quiet"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-not-for-production")

import pytest  # noqa: E402

# A tiny but genuine PDF: starts with the %PDF- signature the app checks for.
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"


@pytest.fixture
def pdf_bytes():
    return VALID_PDF_BYTES


@pytest.fixture
def resume_dir(tmp_path, monkeypatch):
    """Save uploaded résumés into a temp folder instead of var/resumes."""
    from app.utilities import resume_storage

    folder = tmp_path / "resumes"
    monkeypatch.setattr(resume_storage, "RESUME_DIRECTORY", folder)
    return folder
