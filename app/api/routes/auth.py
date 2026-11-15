from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import AdminUser, CurrentUser, DbSession
from app.auth.models import User
from app.auth.schemas import RoleUpdate, TokenResponse, UserCreate, UserRead
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["authentication"])
admin_router = APIRouter(prefix="/admin", tags=["administration"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(request: UserCreate, db: DbSession) -> User:
    user = User(email=request.email, password_hash=hash_password(request.password), role="user")
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    db.refresh(user)
    return user


@router.post("/token", response_model=TokenResponse)
def login(
    db: DbSession,
    form: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    settings = get_settings()
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.id, settings)
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserRead)
def get_profile(user: CurrentUser) -> User:
    return user


@admin_router.get("/users", response_model=list[UserRead])
def list_users(_: AdminUser, db: DbSession) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


@admin_router.patch("/users/{user_id}/role", response_model=UserRead)
def update_user_role(user_id: int, request: RoleUpdate, _: AdminUser, db: DbSession) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = request.role.value
    db.commit()
    db.refresh(user)
    return user
