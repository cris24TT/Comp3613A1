from sqlmodel import Session, func, select

from app.models.application import Application
from app.models.application_status_change import ApplicationStatusChange
from app.models.coordinator import Coordinator
from app.models.internship_position import Company, InternshipPosition
from app.models.student import Student


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_open_positions(
        self, search: str = ""
    ) -> list[tuple[InternshipPosition, str]]:
        # STUDENT CODE START
        has_coordinator = select(Coordinator.coordinator_id).where(
        Coordinator.department == InternshipPosition.department).exists()
        # STUDENT CODE END

        statement = (
            select(InternshipPosition, Company.name)
            .join(Company)
           .where(InternshipPosition.status == "open",has_coordinator,)
            .order_by(InternshipPosition.posted_at.desc())
        )
        if search.strip():
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                InternshipPosition.title.ilike(pattern)
                | InternshipPosition.description.ilike(pattern)
                | InternshipPosition.location.ilike(pattern)
                | Company.name.ilike(pattern)
            )
        return list(self.db.exec(statement).all())

    def get_student_by_user_id(self, user_id: int) -> Student | None:
        statement = select(Student).where(Student.user_id == user_id)
        return self.db.exec(statement).one_or_none()

    def get_position(self, position_id: int) -> InternshipPosition | None:
        return self.db.get(InternshipPosition, position_id)

    def get_position_details(
        self, position_id: int
    ) -> tuple[InternshipPosition, Company] | None:
        statement = (
            select(InternshipPosition, Company)
            .join(Company)
            .where(InternshipPosition.position_id == position_id)
        )
        return self.db.exec(statement).one_or_none()

    def get_coordinator_by_user_id(self, user_id: int) -> Coordinator | None:
        # STUDENT CODE START
        statement = select(Coordinator).where(Coordinator.user_id == user_id)
        return self.db.exec(statement).one_or_none()
        # STUDENT CODE END

    def get_coordinator_for_department(
        self, department: str
    ) -> Coordinator | None:
        # STUDENT CODE START
        selector = select(Coordinator).where(Coordinator.department == department)
        matching_coordinators = self.db.exec(selector).all()
        if not matching_coordinators:
            return None
            
        def workload_key(coordinator: Coordinator) -> tuple[int, int, int]:
            return (
            self.count_pending_applications(coordinator.coordinator_id),
            self.count_total_applications(coordinator.coordinator_id),
            coordinator.coordinator_id,
            )
        return min(matching_coordinators, key=workload_key)
        # STUDENT CODE END

    def count_pending_applications(self, coordinator_id: int) -> int:
        # STUDENT CODE START
        statement = select(func.count(Application.application_id)).where(
            Application.coordinator_id == coordinator_id,
            Application.status == "pending"
        )
        return self.db.exec(statement).one()

    def count_total_applications(self, coordinator_id: int) -> int:

        statement = select(func.count(Application.application_id)).where(
            Application.coordinator_id == coordinator_id,
        )
        return self.db.exec(statement).one()
        # STUDENT CODE END

    def has_application(self, student_id: int, position_id: int, semester: str) -> bool:
        statement = select(Application.application_id).where(
            Application.student_id == student_id,
            Application.position_id == position_id,
            Application.semester == semester
        )
        return self.db.exec(statement).first() is not None

    def get_application_for_coordinator(
        self, application_id: int, coordinator_id: int
    ) -> Application | None:
    
        # STUDENT CODE START
        statement = select(Application).where(
            Application.application_id == application_id,
            Application.coordinator_id == coordinator_id,
        )
        return self.db.exec(statement).one_or_none()
        # STUDENT CODE END

    def get_applications_for_coordinator(
        self, coordinator_id: int
    ) -> list[tuple[Application, Student, InternshipPosition, Company]]:
        statement = (
            select(Application, Student, InternshipPosition, Company)
            .join(Student, Application.student_id == Student.student_id)
            .join(
                InternshipPosition,
                Application.position_id == InternshipPosition.position_id,
            )
            .join(Company, InternshipPosition.company_id == Company.company_id)
            .where(Application.coordinator_id == coordinator_id)
            .order_by(
                Application.semester.desc(),
                Application.applied_at.desc(),
            )
        )
        return list(self.db.exec(statement).all())

    def get_applications_for_student(
        self, student_id: int
    ) -> list[tuple[Application, InternshipPosition, Company]]:
        statement = (
            select(Application, InternshipPosition, Company)
            .join(
                InternshipPosition,
                Application.position_id == InternshipPosition.position_id,
            )
            .join(Company, InternshipPosition.company_id == Company.company_id)
            .where(Application.student_id == student_id)
            .order_by(Application.applied_at.desc())
        )
        return list(self.db.exec(statement).all())

    def get_application_for_student(
        self, application_id: int, student_id: int
    ) -> tuple[Application, InternshipPosition, Company] | None:
        statement = (
            select(Application, InternshipPosition, Company)
            .join(
                InternshipPosition,
                Application.position_id == InternshipPosition.position_id,
            )
            .join(Company, InternshipPosition.company_id == Company.company_id)
            .where(
                Application.application_id == application_id,
                Application.student_id == student_id,
            )
        )
        return self.db.exec(statement).one_or_none()
        # STUDENT CODE END

    def get_status_history_for_application(
        self, application_id: int, coordinator_id: int
    ) -> list[ApplicationStatusChange]:
        # STUDENT CODE START
        application = self.get_application_for_coordinator(application_id, coordinator_id)
        if application is None:
            return []
        selector = select(ApplicationStatusChange).where(
            ApplicationStatusChange.application_id == application_id
        ).order_by(ApplicationStatusChange.changed_at.asc())
        return list(self.db.exec(selector).all())
        # STUDENT CODE END

    def record_status_change(
        self,
        *,
        application: Application,
        coordinator_id: int,
        new_status: str,
        reason: str,
    ) -> Application:
        # STUDENT CODE START
        previous_status = application.status
        status_change = ApplicationStatusChange(
            previous_status=previous_status,
            coordinator_id=coordinator_id,
            application_id=application.application_id,
            new_status=new_status,
            reason=reason.strip(),
        )
        application.status = new_status
        try:
            self.db.add(status_change)
            self.db.add(application)
            self.db.commit()
            self.db.refresh(application)
            return application
        except Exception:
            self.db.rollback()
            raise
        # STUDENT CODE END

    def create_application(
        self,
        *,
        user_id: int,
        profile: dict[str, str | int],
        position_id: int,
        resume_path: str,
        cover_letter: str,
        coordinator_id: int,
        semester: str,

        
    ) -> Application:
        try:
            student = self.get_student_by_user_id(user_id)
            if student is None:
                student = Student(user_id=user_id, **profile)
                self.db.add(student)
                self.db.flush()
            else:
                for field, value in profile.items():
                    setattr(student, field, value)

            application = Application(
                student_id=student.student_id,
                position_id=position_id,
                resume_path=resume_path,
                cover_letter=cover_letter,
                coordinator_id=coordinator_id,
                semester=semester,
            )
            self.db.add(application)
            self.db.commit()
            self.db.refresh(application)
            return application
        except Exception:
            self.db.rollback()
            raise