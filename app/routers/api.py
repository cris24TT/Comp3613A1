
from typing import Annotated

from fastapi import File, Form, HTTPException, UploadFile, status

from app.dependencies import SessionDep
from app.dependencies.auth import CoordinatorDep, StudentDep
from app.repositories.application import ApplicationRepository
from app.repositories.user import UserRepository
from app.services.application_service import ApplicationService
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

@api_router.post("/applications", status_code=status.HTTP_201_CREATED)
async def api_apply(
    user: StudentDep,
    db: SessionDep,
    resume_file: Annotated[UploadFile, File()],
    position_id: int = Form(),
    first_name: str = Form(),
    last_name: str = Form(),
    major: str = Form(),
    graduation_year: int = Form(),
    cover_letter: str = Form(),
):
    service = ApplicationService(ApplicationRepository(db))
    profile = {
        "first_name": first_name,
        "last_name": last_name,
        "major": major,
        "graduation_year": graduation_year,
    }
    try:
        application = await service.submit_application(
            user_id=user.id,
            profile=profile,
            position_id=position_id,
            resume_file=resume_file,
            cover_letter=cover_letter,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return {
        "application_id": application.application_id,
        "position_id": application.position_id,
        "semester": application.semester,
        "status": application.status,
    }

@api_router.get("/review/applications")
async def api_review_queue(
    user:CoordinatorDep,
    db: SessionDep,
):
    service = ApplicationService(ApplicationRepository(db))
    try:
        queue = service.get_review_queue(user.id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error

    return [
        {
            "application_id": application.application_id,
            "student_id": student.student_id,
            "student_name": f"{student.first_name} {student.last_name}",
            "position_title": position.title,
            "company": company.name,
            "semester": application.semester,
            "status": application.status,
        }
        for application, student, position, company in queue
    ]

@api_router.get("/review/applications/{application_id}")
async def api_review_detail(
    application_id: int,
    user: CoordinatorDep,
    db: SessionDep,
):
    service = ApplicationService(ApplicationRepository(db))
    try:
        application, history, position, company = service.get_review_detail(
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

@api_router.patch("/review/applications/{application_id}/status")
async def api_change_status(
    application_id: int,
    user: CoordinatorDep,
    db: SessionDep,
    new_status: str = Form(),
    reason: str = Form(),
):
    service = ApplicationService(ApplicationRepository(db))
    try:
        application = service.change_application_status_for_user(
            user_id=user.id,
            application_id=application_id,
            new_status=new_status,
            reason=reason,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return {
        "application_id": application.application_id,
        "status": application.status,
    }