from sqlmodel import create_engine, SQLModel, Session

from app.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

def SessionLocal():
    return Session(engine)

def init_db() -> None:
    SQLModel.metadata.create_all(bind=engine)

def get_db():
    with Session(engine) as session:
        yield session