from typing import Annotated

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies import SessionDep
from app.dependencies.auth import StudentDep
from app.repositories.application import ApplicationRepository
from app.services.application_service import ApplicationService
from app.utilities.flash import flash

from . import router, templates


@router.get("/app/applications", response_class=HTMLResponse, name="apply_view")
async def apply_view(request: Request, user: StudentDep, db: SessionDep, q: str = ""):
    service = ApplicationService(ApplicationRepository(db))
    positions, student = service.get_application_form_data(user.id, q)
    return templates.TemplateResponse(
        request=request,
        name="apply.html",
        context={
            "user": user,
            "positions": positions,
            "student": student,
            "search_query": q,
        },
    )


@router.post("/app/applications", name="submit_application")
async def submit_application_view(
    request: Request,
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

    # STUDENT CODE START
    profile = {
    "first_name": first_name,
    "last_name": last_name,
    "major": major,
    "graduation_year": graduation_year,
    }
    try:
        await service.submit_application(
            user_id=user.id,
            profile=profile,
            position_id=position_id,
            resume_file=resume_file,
            cover_letter=cover_letter,
        )
        flash(request, "Application submitted successfully.", "success")
    except ValueError as error:
        flash(request, str(error), "danger")
    # STUDENT CODE END

    return RedirectResponse(
        url=request.url_for("apply_view"),
        status_code=303,
    )