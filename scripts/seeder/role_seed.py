from sqlmodel import Session, select

from app.database import engine
from app.config import get_settings

from app.security.passwords import hash_password
from app.models import User, Role, UserRole, Document

settings = get_settings()

DEFAULT_ROLES = {
    "user": "Regular user",
    "admin": "Admin with more authority"
}

def run():
    with Session(engine) as session:
        existing_roles = {role.name for role in session.exec(select(Role)).all()}
        for name, description in DEFAULT_ROLES.items():
            if name not in existing_roles:
                session.add(Role(name=name, description=description))
        session.commit()


if __name__ == "__main__":
    run()