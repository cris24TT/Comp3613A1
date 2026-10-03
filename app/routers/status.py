from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies import SessionDep
from app.dependencies.auth import StudentDep
from app.repositories.application import ApplicationRepository
from app.services.application_service import ApplicationService

from . import router, templates


@router.get(
    "/app/status",
    response_class=HTMLResponse,
    name="application_status_view",
)
async def application_status_view(
    request: Request,
    user: StudentDep,
    db: SessionDep,
):
    # STUDENT CODE START
    # Bind the request dependencies and call the service method that returns
    # this student's applications. Keep persistence logic out of this route.
   service = ApplicationService(ApplicationRepository(db))
   applications = service.get_student_applications(user.id)
   return templates.TemplateResponse(
       request=request,
       name="application-status.html",
       context={"user": user, "applications": applications},
   )
    # STUDENT CODE END


@router.get(
    "/app/status/{application_id}",
    response_class=HTMLResponse,
    name="application_details_view",
)
async def application_details_view(
    request: Request,
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
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=str(error)) from error
    return templates.TemplateResponse(
        request=request,
        name="application-details.html",
        context={
            "user": user,
            "application": application,
            "position": position,
            "company": company,
            "history": history,
        },
    )
