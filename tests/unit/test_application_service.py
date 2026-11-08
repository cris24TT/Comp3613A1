"""Unit tests for ApplicationService (UT-01 to UT-03, UT-05 to UT-08).

The repository is replaced with a MagicMock, so these tests check the
business rules in the service on their own, with no database.
"""
import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.services import application_service as service_module
from app.services.application_service import ApplicationService


PDF_BYTES = b"%PDF-1.4\n%%EOF\n"


def make_pdf_upload(name="cv.pdf", content=PDF_BYTES):
    return UploadFile(filename=name, file=io.BytesIO(content))


def make_open_position(**overrides):
    values = dict(
        position_id=2,
        status="open",
        department="Computer Science",
        offering_year=2027,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    return ApplicationService(repo)


@pytest.fixture
def fake_resume_storage(monkeypatch):
    """Stop submit_application from writing files during unit tests."""
    save = AsyncMock(return_value="stored-key.pdf")
    delete = MagicMock()
    monkeypatch.setattr(service_module, "save_resume", save)
    monkeypatch.setattr(service_module, "delete_resume", delete)
    return save


SUBMIT_ARGS = dict(
    user_id=1,
    profile={
        "first_name": "Bob",
        "last_name": "Sterling",
        "major": "Computer Science",
        "graduation_year": 2027,
    },
    position_id=2,
    cover_letter="I am interested",
)


# ---------- submit_application (Apply for Internship) ----------

async def test_ut01_valid_application_is_submitted(service, repo, fake_resume_storage):
    repo.get_position.return_value = make_open_position()
    repo.get_student_by_user_id.return_value = SimpleNamespace(student_id=1)
    repo.has_application.return_value = False
    repo.get_coordinator_for_department.return_value = SimpleNamespace(coordinator_id=7)
    repo.create_application.return_value = SimpleNamespace(application_id=10, status="pending")

    result = await service.submit_application(resume_file=make_pdf_upload(), **SUBMIT_ARGS)

    assert result.application_id == 10
    repo.get_coordinator_for_department.assert_called_once_with(department="Computer Science")
    kwargs = repo.create_application.call_args.kwargs
    assert kwargs["semester"] == "Summer 2027"
    assert kwargs["coordinator_id"] == 7
    assert kwargs["resume_path"] == "stored-key.pdf"


async def test_ut02_duplicate_application_is_blocked(service, repo, fake_resume_storage):
    repo.get_position.return_value = make_open_position()
    repo.get_student_by_user_id.return_value = SimpleNamespace(student_id=1)
    repo.has_application.return_value = True

    with pytest.raises(ValueError, match="You have already applied for this internship."):
        await service.submit_application(resume_file=make_pdf_upload(), **SUBMIT_ARGS)

    repo.create_application.assert_not_called()
    fake_resume_storage.assert_not_called()


async def test_ut03_no_coordinator_for_department(service, repo, fake_resume_storage):
    repo.get_position.return_value = make_open_position(department="Philosophy")
    repo.get_student_by_user_id.return_value = None
    repo.get_coordinator_for_department.return_value = None

    with pytest.raises(ValueError, match="No coordinator available for this department."):
        await service.submit_application(resume_file=make_pdf_upload(), **SUBMIT_ARGS)

    repo.create_application.assert_not_called()
    fake_resume_storage.assert_not_called()


# ---------- change_application_status (Review Internship Applications) ----------

def test_ut05_pending_application_is_accepted(service, repo):
    application = SimpleNamespace(application_id=5, status="pending")
    repo.get_application_for_coordinator.return_value = application
    repo.record_status_change.return_value = SimpleNamespace(application_id=5, status="accepted")

    result = service.change_application_status(
        application_id=5, coordinator_id=7, new_status="accepted", reason="Strong candidate"
    )

    assert result.status == "accepted"
    repo.record_status_change.assert_called_once_with(
        application=application,
        coordinator_id=7,
        new_status="accepted",
        reason="Strong candidate",
    )


def test_ut06_revoked_is_final(service, repo):
    repo.get_application_for_coordinator.return_value = SimpleNamespace(
        application_id=5, status="revoked"
    )

    with pytest.raises(ValueError, match="This status change is not allowed."):
        service.change_application_status(
            application_id=5, coordinator_id=7, new_status="accepted", reason="Reconsidered"
        )

    repo.record_status_change.assert_not_called()


def test_ut07_reason_is_required(service, repo):
    repo.get_application_for_coordinator.return_value = SimpleNamespace(
        application_id=5, status="pending"
    )

    with pytest.raises(ValueError, match="A reason is required for a status change."):
        service.change_application_status(
            application_id=5, coordinator_id=7, new_status="accepted", reason="   "
        )

    repo.record_status_change.assert_not_called()


def test_ut08_application_not_assigned_to_coordinator(service, repo):
    repo.get_application_for_coordinator.return_value = None

    with pytest.raises(
        ValueError, match="Application not found or not assigned to this coordinator."
    ):
        service.change_application_status(
            application_id=5, coordinator_id=99, new_status="accepted", reason="Strong candidate"
        )

    repo.record_status_change.assert_not_called()
