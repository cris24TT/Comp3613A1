"""Unit tests for AuthService.authenticate_user (UT-09, UT-10)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.auth_service import AuthService
from app.utilities.security import encrypt_password


@pytest.fixture
def auth_service():
    repo = MagicMock()
    repo.get_by_username.return_value = SimpleNamespace(
        id=1, username="bob", role="student", password=encrypt_password("bobpass")
    )
    return AuthService(repo)


def test_ut09_correct_login_returns_token(auth_service):
    token = auth_service.authenticate_user("bob", "bobpass")

    assert isinstance(token, str) and token


def test_ut10_wrong_password_returns_none(auth_service):
    assert auth_service.authenticate_user("bob", "wrongpass") is None
