from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, utcnow
from app.models.catalogs import Category, RequestStatus
from app.models.user import User

PRIORITIES = ("baja", "media", "alta")
# Qué ocurrió en cada registro del historial (RF07: "debe ser evidente qué ocurrió").
HISTORY_ACTIONS = ("created", "status_change", "assignment", "observation")


class CitizenRequest(Base):
    """Solicitud ciudadana (tabla `requests`).

    El número visible (000123) NO se guarda: se deriva del id para no duplicar información.
    El estado actual sí se guarda (status_id) para poder filtrar rápido; el historial
    es el registro de cómo se llegó a él. Ambos se escriben en la misma transacción.
    """
    __tablename__ = "requests"
    __table_args__ = (
        CheckConstraint("length(subject) >= 5", name="ck_requests_subject_len"),
        CheckConstraint("length(description) >= 20", name="ck_requests_description_len"),
        CheckConstraint(f"priority IS NULL OR priority IN {PRIORITIES}", name="ck_requests_priority"),
        Index("ix_requests_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("request_statuses.id"), index=True)
    official_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(String(10))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), onupdate=utcnow
    )

    citizen: Mapped[User] = relationship(foreign_keys=[citizen_id], lazy="joined")
    official: Mapped[User | None] = relationship(foreign_keys=[official_id], lazy="joined")
    category: Mapped[Category] = relationship(lazy="joined")
    status: Mapped[RequestStatus] = relationship(lazy="joined")

    @property
    def number(self) -> str:
        return format_request_number(self.id)


def format_request_number(request_id: int) -> str:
    return f"{request_id:06d}"


class RequestStatusHistory(Base):
    """Historial inmutable: solo se inserta. No hay endpoint para editar ni borrar, y en
    PostgreSQL un trigger rechaza UPDATE/DELETE (ver database/schema.sql).

    Cada registro dice qué ocurrió (action): creación, cambio de estado, asignación u observación.
    En una asignación u observación sin cambio de estado, el estado anterior y el nuevo son iguales.
    """
    __tablename__ = "request_status_history"
    __table_args__ = (
        Index("ix_history_request_changed", "request_id", "changed_at"),
        CheckConstraint(f"action IN {HISTORY_ACTIONS}", name="ck_history_action"),
        # Solo el registro de creación no tiene estado anterior.
        CheckConstraint("(action = 'created') = (previous_status_id IS NULL)", name="ck_history_previous"),
        # El funcionario se guarda solo en las asignaciones (como en el ejemplo del PDF).
        CheckConstraint("(action = 'assignment') = (assigned_official_id IS NOT NULL)", name="ck_history_official"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    previous_status_id: Mapped[int | None] = mapped_column(ForeignKey("request_statuses.id"))
    new_status_id: Mapped[int] = mapped_column(ForeignKey("request_statuses.id"))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(20))
    # Solo en asignaciones: a quién se asignó. No es redundante con requests.official_id,
    # porque la solicitud puede reasignarse después y el historial debe conservar lo que pasó.
    assigned_official_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    observation: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())

    previous_status: Mapped[RequestStatus | None] = relationship(
        foreign_keys=[previous_status_id], lazy="joined")
    new_status: Mapped[RequestStatus] = relationship(foreign_keys=[new_status_id], lazy="joined")
    changed_by: Mapped[User] = relationship(foreign_keys=[changed_by_id], lazy="joined")
    assigned_official: Mapped[User | None] = relationship(
        foreign_keys=[assigned_official_id], lazy="joined")
