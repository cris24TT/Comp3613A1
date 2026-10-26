from fastapi import Form, HTTPException, status

from app.dependencies import SessionDep
from app.repositories.user import UserRepository
from app.services.auth_service import AuthService
from . import api_router
from app.dependencies.auth import StudentDep
from app.repositories.application import ApplicationRepository
from app.services.application_service import ApplicationService

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

@api_router.get("/positions")
async def api_list_positions(
    user: StudentDep,
    db: SessionDep,
    q: str = "",
):
    service = ApplicationService(ApplicationRepository(db))
    positions, _student = service.get_application_form_data(user.id, q)
    return [
        {
            "position_id": position.position_id,
            "title": position.title,
            "company": company_name,
            "department": position.department,
            "location": position.location,
            "work_type": position.work_type,
            "offering_year": position.offering_year,
        }
        for position, company_name in positions
    ]
@api_router.get("/applications")
async def api_list_my_applications(
    user: StudentDep,
    db: SessionDep,
):
    service = ApplicationService(ApplicationRepository(db))
    applications = service.get_student_applications(user.id)
    return [
        {
            "application_id": application.application_id,
            "position_title": position.title,
            "company": company.name,
            "semester": application.semester,
            "status": application.status,
            "applied_at": application.applied_at,
        }
        for application, position, company in applications
    ]

@api_router.get("/applications/{application_id}")
async def api_get_my_application(
    application_id: int,
    user: StudentDep,
    db: SessionDep,
):
    service = ApplicationService(ApplicationRepository(db))
    try:
        application, position, company, history = service.get_student_application_detail(
            user.id, application_id
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return {
        "application_id": application.application_id,
        "position_title": position.title,
        "company": company.name,
        "semester": application.semester,
        "status": application.status,
        "applied_at": application.applied_at,
        "cover_letter": application.cover_letter,
        "history": [
            {
                "previous_status": change.previous_status,
                "new_status": change.new_status,
                "reason": change.reason,
                "changed_at": change.changed_at,
            }
            for change in history
        ],
    }