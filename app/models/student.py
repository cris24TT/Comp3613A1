from sqlmodel import Field, SQLModel


class Student(SQLModel, table=True):
    student_id: int | None = Field(default=None, primary_key=True)

    # STUDENT CODE START
    user_id: int = Field(foreign_key="user.id", unique=True)
    first_name: str
    last_name: str  
    major: str
    graduation_year: int
    # STUDENT CODE END