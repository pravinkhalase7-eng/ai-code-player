from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.orm import Base, Concept, User

connect_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(Engine, "connect")
def _sqlite_fk(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SEED_CONCEPTS = (
    ("for_loop", "For Loop", "java"),
    ("while_loop", "While Loop", "java"),
    ("if_statement", "If Statement", "java"),
    ("variables", "Variables", "java"),
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if not db.get(User, settings.default_user_id):
            db.add(User(id=settings.default_user_id, display_name="Student"))
        for concept_id, name, language in SEED_CONCEPTS:
            if not db.get(Concept, concept_id):
                db.add(Concept(id=concept_id, name=name, language=language))
        db.commit()


def db_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
