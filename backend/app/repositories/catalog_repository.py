from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, RequestStatus, Role, StatusTransition


class CatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def role_by_code(self, code: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.code == code))

    def category_by_code(self, code: str) -> Category | None:
        return self.db.scalar(
            select(Category).where(Category.code == code, Category.is_active.is_(True)))

    def status_by_code(self, code: str) -> RequestStatus | None:
        return self.db.scalar(select(RequestStatus).where(RequestStatus.code == code))

    def initial_status(self) -> RequestStatus:
        return self.db.scalars(select(RequestStatus).where(RequestStatus.is_initial.is_(True))).one()

    def categories(self) -> list[Category]:
        return list(self.db.scalars(
            select(Category).where(Category.is_active.is_(True)).order_by(Category.name)))

    def statuses(self) -> list[RequestStatus]:
        return list(self.db.scalars(select(RequestStatus).order_by(RequestStatus.sort_order)))

    def transitions_from(self, status_id: int) -> list[StatusTransition]:
        return list(self.db.scalars(
            select(StatusTransition).where(StatusTransition.from_status_id == status_id)))
