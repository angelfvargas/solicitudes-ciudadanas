from fastapi import APIRouter, Depends, status

from app.dependencies import get_auth_service, get_current_user
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, auth: AuthService = Depends(get_auth_service)):
    return auth.register_citizen(data)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, auth: AuthService = Depends(get_auth_service)):
    token, user = auth.login(data)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
