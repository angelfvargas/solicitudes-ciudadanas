"""Capa MODELO (la M de MVC): tablas de la base de datos mapeadas con SQLAlchemy."""
from app.models.catalogs import Category, RequestStatus, Role, StatusTransition
from app.models.request import CitizenRequest, RequestStatusHistory
from app.models.user import User

__all__ = [
    "Category", "CitizenRequest", "RequestStatus", "RequestStatusHistory",
    "Role", "StatusTransition", "User",
]
