from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, utcnow
from app.models.catalogs import Role

DOCUMENT_TYPES = ("CC", "CE", "TI", "PA")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(f"document_type IN {DOCUMENT_TYPES}", name="ck_users_document_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60))
    document_type: Mapped[str] = mapped_column(String(2))
    # Únicos: la base de datos es la última barrera contra duplicados, aunque el servicio ya lo valide.
    document_number: Mapped[str] = mapped_column(String(15), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)  # siempre en minúsculas
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())

    role: Mapped[Role] = relationship(lazy="joined")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def document_masked(self) -> str:
        return "*" * max(len(self.document_number) - 4, 0) + self.document_number[-4:]
