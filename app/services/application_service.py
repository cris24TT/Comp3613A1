from fastapi import UploadFile

from app.models.application import Application
from app.repositories.application import ApplicationRepository
from app.utilities.resume_storage import delete_resume, save_resume


class ApplicationService:
    def __init__(self, application_repo: ApplicationRepository):
        self.application_repo = application_repo

    def get_application_form_data(self, user_id: int, search: str = ""):
        return (
            self.application_repo.get_open_positions(search),
            self.application_repo.get_student_by_user_id(user_id),
        )

    async def submit_application(
        self,
        *,
        user_id: int,
        profile: dict[str, str | int],
        position_id: int,
        resume_file: UploadFile,
        cover_letter: str,
    ) -> Application:
        if not cover_letter.strip():
            raise ValueError("Add a cover letter before submitting.")

        position = self.application_repo.get_position(position_id)
        if position is None or position.status != "open":
            raise ValueError("That internship is no longer open.")

        student = self.application_repo.get_student_by_user_id(user_id)
        if student and self.application_repo.has_application(
            student.student_id, position_id
        ):
            raise ValueError("You have already applied for this internship.")

        # STUDENT CODE START
        coordinator = self.application_repo.get_coordinator_for_department(
            department=position.department)
        if coordinator is None:
            raise ValueError("No coordinator available for this department.")
        # STUDENT CODE END

        resume_path = await save_resume(resume_file)
        try:
            return self.application_repo.create_application(
                user_id=user_id,
                profile=profile,
                position_id=position_id,
                resume_path=resume_path,
                cover_letter=cover_letter.strip(),
                coordinator_id=coordinator.coordinator_id,
            )
            
        except Exception:
            delete_resume(resume_path)
            raise

    def change_application_status(
        self,
        *,
        application_id: int,
        coordinator_id: int,
        new_status: str,
        reason: str,

    ) -> Application:
        # STUDENT CODE START
        application = self.application_repo.get_application_for_coordinator(
            application_id=application_id,
            coordinator_id=coordinator_id,
        )
        if application is None:
            raise ValueError("Application not found or not assigned to this coordinator.")

        if not reason.strip():
            raise ValueError("A reason is required for a status change.")
        allowed_transitions = {
            "pending": {"accepted", "denied"},
            "denied": {"accepted"},
            "accepted": {"denied", "revoked"},
            "revoked": set(),
}
        if new_status not in allowed_transitions.get(application.status, set()):
             raise ValueError("This status change is not allowed.")
        # STUDENT CODE END