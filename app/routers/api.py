from fastapi import Form, HTTPException, status

from app.dependencies import SessionDep
from app.repositories.user import UserRepository
from app.services.auth_service import AuthService

from . import api_router


@api_router.post("/login")
async def api_login(
    db: SessionDep,
    username: str = Form(),
    password: str = Form(),
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    access_token = auth_service.authenticate_user(username, password)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    user = user_repo.get_by_username(username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
    }
