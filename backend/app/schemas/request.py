from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.catalog import CatalogItem
from app.schemas.user import ActorBrief, UserBrief

Priority = Literal["baja", "media", "alta"]


def _clean(v: str) -> str:
    return " ".join(v.split())


class RequestCreate(BaseModel):
    subject: str = Field(min_length=5, max_length=150)
    description: str = Field(min_length=20, max_length=2000)
    category: str = Field(description="Código de la categoría, p. ej. 'queja'")
    # Datos opcionales que vienen de la sugerencia de IA, ya revisados por el ciudadano.
    priority: Priority | None = None
    ai_summary: str | None = Field(default=None, max_length=500)

    @field_validator("subject")
    @classmethod
    def clean_subject(cls, v: str) -> str:
        v = _clean(v)
        if len(v) < 5:
            raise ValueError("El asunto debe tener al menos 5 caracteres")
        return v

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: str) -> str:
        v = v.strip()
        if len(_clean(v)) < 20:
            raise ValueError("La descripción debe tener al menos 20 caracteres")
        return v


class StatusChangeIn(BaseModel):
    status: str = Field(description="Código del estado destino, p. ej. 'in_progress'")
    observation: str | None = Field(default=None, max_length=1000)


class AssignIn(BaseModel):
    official_id: int = Field(gt=0)
    observation: str | None = Field(default=None, max_length=1000)


class RequestListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    number: str
    subject: str
    category: CatalogItem
    status: CatalogItem
    priority: str | None
    official: UserBrief | None
    created_at: datetime
    updated_at: datetime


class RequestDetail(RequestListItem):
    description: str
    ai_summary: str | None
    citizen: UserBrief


class RequestPage(BaseModel):
    items: list[RequestListItem]
    total: int
    page: int
    size: int


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    previous_status: CatalogItem | None
    new_status: CatalogItem
    changed_by: ActorBrief
    assigned_official: UserBrief | None
    observation: str | None
    changed_at: datetime


class StatsOut(BaseModel):
    total: int
    by_status: list[dict]
    by_category: list[dict]
    unassigned: int
