"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.student import Student
from app.models.internship_position import Company, InternshipPosition
from app.models.application import Application
from app.models.coordinator import Coordinator
from app.models.application_status_change import ApplicationStatusChange

__all__ = [
	"User",
	"Student",
	"Coordinator",
	"ApplicationStatusChange",
	"Company",
	"InternshipPosition",
	"Application",
]
