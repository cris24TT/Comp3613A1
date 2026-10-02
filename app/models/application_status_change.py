from datetime import datetime

from sqlmodel import Field, SQLModel


class ApplicationStatusChange(SQLModel, table=True):
    __tablename__ = "application_status_change"

    change_id: int | None = Field(default=None, primary_key=True)

    # STUDENT CODE START
    coordinator_id: int = Field(foreign_key="coordinator.coordinator_id", index=True)
    application_id: int = Field(foreign_key="application.application_id", index=True)
    previous_status: str
    new_status: str
    reason: str 
    changed_at: datetime = Field(default_factory=datetime.now)
    # STUDENT CODE END