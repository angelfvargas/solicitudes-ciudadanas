"""Tablas de catálogo: datos de referencia que cambian poco.

Roles, categorías, estados y transiciones viven en la base de datos (no en el código)
para que agregar una categoría, un estado o una transición sea insertar una fila,
sin modificar ni volver a desplegar el backend (principio Abierto/Cerrado).
"""
from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # citizen | official | admin
    name: Mapped[str] = mapped_column(String(50))


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class RequestStatus(Base):
    __tablename__ = "request_statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer)
    # Reglas del estado expresadas como datos:
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_official: Mapped[bool] = mapped_column(Boolean, default=False)  # no se entra sin funcionario
    allows_assignment: Mapped[bool] = mapped_column(Boolean, default=False)  # se puede (re)asignar aquí


class StatusTransition(Base):
    """Una fila = "el rol X puede mover una solicitud del estado A al estado B".

    Lo que no está en esta tabla no está permitido (lista blanca).
    """
    __tablename__ = "status_transitions"
    __table_args__ = (UniqueConstraint("from_status_id", "to_status_id", "role_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    from_status_id: Mapped[int] = mapped_column(ForeignKey("request_statuses.id"))
    to_status_id: Mapped[int] = mapped_column(ForeignKey("request_statuses.id"))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))

    from_status: Mapped[RequestStatus] = relationship(foreign_keys=[from_status_id])
    to_status: Mapped[RequestStatus] = relationship(foreign_keys=[to_status_id])
    role: Mapped[Role] = relationship()
