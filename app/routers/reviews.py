from fastapi import Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.dependencies import SessionDep
from app.dependencies.auth import CoordinatorDep
from app.repositories.application import ApplicationRepository
from app.services.application_service import ApplicationService

from . import router, templates


@router.get(
    "/coordinator/review",
    response_class=HTMLResponse,
    name="coordinator_review_view",
)
async def coordinator_review_view(
    request: Request,
    user: CoordinatorDep,
    db: SessionDep,
):
    service = ApplicationService(ApplicationRepository(db))

    try:
        applications = service.get_review_queue(user.id)
    except ValueError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error

    return templates.TemplateResponse(
        request=request,
        name="coordinator-review.html",
        context={
            "user": user,
            "applications": applications,
        },
    )


@router.get(
    "/coordinator/review/{application_id}",
    response_class=HTMLResponse,
    name="coordinator_review_detail_view",
)
async def coordinator_review_detail_view(
    request: Request,
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
        raise HTTPException(status_code=404, detail=str(error)) from error
    return templates.TemplateResponse(
        request=request,
        name="coordinator-review-detail.html",
        context={
            "user": user,
            "application": application,
            "history": history,
            "position": position,
            "company": company,
        },
    )


@router.get(
    "/coordinator/review/{application_id}/resume",
    name="coordinator_review_resume",
)
async def coordinator_review_resume(
    application_id: int,
    user: CoordinatorDep,
    db: SessionDep,
):
    service = ApplicationService(ApplicationRepository(db))
    try:
        path = service.get_review_resume(user.id, application_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return FileResponse(path, media_type="application/pdf", filename="resume.pdf")


@router.post(
    "/coordinator/review/{application_id}/status",
    name="coordinator_review_status_action",
)
async def coordinator_review_status_action(
    request: Request,
    application_id: int,
    user: CoordinatorDep,
    db: SessionDep,
    new_status: str = Form(),
    reason: str = Form(),
):
    service = ApplicationService(ApplicationRepository(db))
    try:
        service.change_application_status_for_user(
            user_id=user.id,
            application_id=application_id,
            new_status=new_status,
            reason=reason,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return RedirectResponse(
        url=request.url_for(
            "coordinator_review_detail_view", application_id=application_id
        ),
        status_code=303,
    )