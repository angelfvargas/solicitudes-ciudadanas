"""Composición: aquí se arma cada servicio con sus dependencias (inyección de dependencias).

Es el único archivo que sabe qué implementación concreta usa cada servicio.
"""
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.security import PasswordHasher, TokenService
from app.db.session import get_db
from app.models import User
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.request_repository import HistoryRepository, RequestRepository
from app.repositories.user_repository import UserRepository
from app.services.access_policy import RequestAccessPolicy
from app.services.ai.classifier import RequestClassifier
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.provider import LLMProvider
from app.services.auth_service import AuthService
from app.services.request_service import RequestService
from app.services.stats_service import StatsService
from app.services.workflow import StatusWorkflow

_bearer = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db), CatalogRepository(db), PasswordHasher(), TokenService())


def get_request_service(db: Session = Depends(get_db)) -> RequestService:
    catalogs = CatalogRepository(db)
    return RequestService(RequestRepository(db), HistoryRepository(db), UserRepository(db),
                          catalogs, StatusWorkflow(catalogs), RequestAccessPolicy())


def get_stats_service(db: Session = Depends(get_db)) -> StatsService:
    return StatsService(RequestRepository(db), RequestAccessPolicy())


def get_llm_provider() -> LLMProvider | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    return GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.ai_timeout_seconds)


def get_classifier(db: Session = Depends(get_db),
                   provider: LLMProvider | None = Depends(get_llm_provider)) -> RequestClassifier:
    return RequestClassifier(provider, CatalogRepository(db))


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
                     auth: AuthService = Depends(get_auth_service)) -> User:
    if credentials is None:
        raise AuthenticationError("Debe iniciar sesión.")
    return auth.user_from_token(credentials.credentials)


def require_roles(*role_codes: str) -> Callable[..., User]:
    """Protege un endpoint por rol: Depends(require_roles("admin"))."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.code not in role_codes:
            raise PermissionDeniedError("No tiene permiso para esta operación.")
        return user
    return checker
