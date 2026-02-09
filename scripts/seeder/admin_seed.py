from sqlmodel import Session, select

from app.database import engine
from app.config import get_settings

from app.security.passwords import hash_password
from app.models import User, Role, UserRole, Document

settings = get_settings()

DEFAULT_ADMIN = [
    {
        "username": f"admin{i}",
        "email": email,
        "hashed_password": hash_password(password),
        "fullname": f"admin{i}"
    } for i, (email, password) in enumerate(zip(settings.ADMIN_EMAILS, settings.ADMIN_PASS))
]

def run():
    with Session(engine) as session:
        admin_role = session.exec(
            select(Role).where(Role.name == "superadmin")
        ).one_or_none()

        existing_emails = {user.email for user in session.exec(select(User)).all()}
        for data in DEFAULT_ADMIN:
            if data["email"] not in existing_emails:
                session.add(User(
                    username=data["username"],
                    email=data["email"],
                    hashed_password=data["hashed_password"],
                    full_name=data["fullname"],
                    roles=[admin_role],
                    token_version=1,
                    is_active=True
                ))
            else:
                admin = session.exec(
                    select(User).where(User.email == data["email"])
                ).one()
                
                admin.roles = [admin_role]
                session.add(admin)

        session.commit()


if __name__ == "__main__":
    run()