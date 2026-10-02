from sqlmodel import Field, SQLModel


class Coordinator(SQLModel, table=True):
    coordinator_id: int | None = Field(default=None, primary_key=True)

    # STUDENT CODE START
    user_id: int = Field(foreign_key="user.id", unique=True)
    first_name: str
    last_name: str
    department: str
    # STUDENT CODE END