from fastapi import UploadFile

from app.models.application import Application
from app.repositories.application import ApplicationRepository
from app.utilities.resume_storage import delete_resume, resume_path, save_resume


class ApplicationService:
    def __init__(self, application_repo: ApplicationRepository):
        self.application_repo = application_repo

    def get_review_queue(self, user_id: int) -> list[tuple[Application, object, object, object]]:
        # STUDENT CODE START
        coordinator = self.application_repo.get_coordinator_by_user_id(user_id)
        if coordinator is None:
            raise ValueError("You are not a coordinator.")
        return self.application_repo.get_applications_for_coordinator(
            coordinator.coordinator_id
        )
        # STUDENT CODE END

    def get_review_detail(
        self, user_id: int, application_id: int
    ) -> tuple[Application, list, object, object]:
        coordinator = self.application_repo.get_coordinator_by_user_id(user_id)
        if coordinator is None:
            raise ValueError("You are not a coordinator.")
        application = self.application_repo.get_application_for_coordinator(
            application_id=application_id,
            coordinator_id=coordinator.coordinator_id,
        )
        if application is None:
            raise ValueError("Application not found or not assigned to this coordinator.")
        history = self.application_repo.get_status_history_for_application(
            application_id=application_id,
            coordinator_id=coordinator.coordinator_id,
        )
        position_details = self.application_repo.get_position_details(
            application.position_id
        )
        if position_details is None:
            raise ValueError("Internship position not found.")
        position, company = position_details
        return application, history, position, company

    def get_review_resume(self, user_id: int, application_id: int):
        coordinator = self.application_repo.get_coordinator_by_user_id(user_id)
        if coordinator is None:
            raise ValueError("You are not a coordinator.")
        application = self.application_repo.get_application_for_coordinator(
            application_id=application_id,
            coordinator_id=coordinator.coordinator_id,
        )
        if application is None:
            raise ValueError("Application not found or not assigned to this coordinator.")
        path = resume_path(application.resume_path)
        if path is None:
            raise FileNotFoundError("Résumé file is unavailable.")
        return path

    def get_application_form_data(self, user_id: int, search: str = ""):
        return (
            self.application_repo.get_open_positions(search),
            self.application_repo.get_student_by_user_id(user_id),
        )

    def get_student_applications(
        self, user_id: int
    ) -> list[tuple[Application, object, object]]:
        student = self.application_repo.get_student_by_user_id(user_id)
        if student is None or student.student_id is None:
            return []
        return self.application_repo.get_applications_for_student(student.student_id)

    def get_student_application_detail(
        self, user_id: int, application_id: int
    ) -> tuple[Application, object, object, list]:
        student = self.application_repo.get_student_by_user_id(user_id)
        if student is None or student.student_id is None:
            raise ValueError("Application not found.")
        application_details = self.application_repo.get_application_for_student(
            application_id=application_id,
            student_id=student.student_id,
        )
        if application_details is None:
            raise ValueError("Application not found.")
        application, position, company = application_details
        history = self.application_repo.get_status_history_for_student(
            application_id=application_id,
            student_id=student.student_id,
        )
        return application, position, company, history

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
        semester = f"Summer {position.offering_year}"

        student = self.application_repo.get_student_by_user_id(user_id)
        if student and self.application_repo.has_application(
            student.student_id, position_id, semester=semester
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
                semester=semester,
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
        return self.application_repo.record_status_change(
            application=application,
            coordinator_id=coordinator_id,
            new_status=new_status,
            reason=reason,
            )
        # STUDENT CODE END

    def change_application_status_for_user(
        self,
        *,
        user_id: int,
        application_id: int,
        new_status: str,
        reason: str,
    ) -> Application:
        coordinator = self.application_repo.get_coordinator_by_user_id(user_id)
        if coordinator is None:
            raise ValueError("You are not a coordinator.")
        return self.change_application_status(
            application_id=application_id,
            coordinator_id=coordinator.coordinator_id,
            new_status=new_status,
            reason=reason,
        )