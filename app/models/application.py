from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Application(SQLModel, table=True):
    __tablename__ = "application"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "position_id",
            "semester",
            name="uq_application_student_position",
        ),
    )

    application_id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id", index=True)
    position_id: int = Field(foreign_key="internship_position.position_id", index=True)
    coordinator_id: int = Field(foreign_key="coordinator.coordinator_id", index=True)
    applied_at: datetime = Field(default_factory=datetime.now)
    resume_path: str
    cover_letter: str
    semester: str
    status: str = Field(default="pending", index=True)

  