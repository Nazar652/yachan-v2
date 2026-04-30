from sqlmodel import SQLModel, create_engine
import os

# Import models so SQLModel metadata includes all tables.
from src import models  # noqa: F401

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./yachan.db")
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
