from typing import Literal

from pydantic import BaseModel, Field


class ClassifyIn(BaseModel):
    subject: str = Field(default="", max_length=150)
    description: str = Field(min_length=20, max_length=2000)


class ClassificationOut(BaseModel):
    """Sugerencia de la IA. Es solo una propuesta: el ciudadano la revisa y puede cambiarla."""
    category: str
    priority: Literal["baja", "media", "alta"]
    summary: str = Field(min_length=10, max_length=500)
    model: str
