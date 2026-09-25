from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    name: str


class UserOut(BaseModel):
    """Lo que el frontend necesita saber del usuario autenticado. Sin hash ni documento."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    full_name: str
    email: str
    role: RoleOut


class UserAdminOut(UserOut):
    """Vista de administración: el documento va enmascarado (solo últimos 4 dígitos)."""
    document_type: str
    document_masked: str
    is_active: bool
    created_at: datetime


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str


class ActorBrief(UserBrief):
    """Quién hizo un cambio en el historial, con su rol."""
    role: RoleOut
