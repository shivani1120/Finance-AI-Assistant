from sqlalchemy import select
from app.auth.models import User
from app.auth.schemas import UserCreate, UserRole
from app.auth.security import hash_password
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.history import models as _history_models  # noqa: F401


def initialize_auth_storage(settings: Settings) -> None:
    session_factory = get_session_factory()
    Base.metadata.create_all(bind=get_engine())
    if not settings.bootstrap_admin_email:
        return

    normalized_email = UserCreate(
        email=settings.bootstrap_admin_email,
        password=settings.bootstrap_admin_password,
    ).email
    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == normalized_email))
        if user is None:
            user = User(
                email=normalized_email,
                password_hash=hash_password(settings.bootstrap_admin_password),
                role=UserRole.ADMIN.value,
            )
            db.add(user)
            db.commit()
