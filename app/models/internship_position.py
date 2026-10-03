from datetime import date

from sqlmodel import Field, SQLModel


class Company(SQLModel, table=True):
    __tablename__ = "company"

    company_id: int | None = Field(default=None, primary_key=True)
    name: str
    industry: str
    contact_email: str


class InternshipPosition(SQLModel, table=True):
    __tablename__ = "internship_position"

    position_id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.company_id")
    title: str = Field(index=True)

    # STUDENT CODE START
    department: str = Field(index=True)
    # STUDENT CODE END

    # STUDENT CODE START
    offering_year: int = Field(index=True)
    # STUDENT CODE END

    description: str
    location: str
    work_type: str
    posted_at: date = Field(default_factory=date.today)
    status: str = Field(default="open", index=True)