from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Category, CitizenRequest, RequestStatus, RequestStatusHistory


@dataclass
class RequestFilters:
    status: str | None = None
    category: str | None = None
    number: int | None = None
    citizen_id: int | None = None   # alcance del ciudadano
    official_id: int | None = None  # alcance del funcionario


class RequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, request_id: int, for_update: bool = False) -> CitizenRequest | None:
        """for_update=True bloquea la fila (SELECT ... FOR UPDATE) hasta el commit: si dos personas
        cambian la misma solicitud a la vez, la segunda espera y valida sobre el estado ya actualizado."""
        if for_update:
            self.db.execute(select(CitizenRequest.id).where(CitizenRequest.id == request_id).with_for_update())
            return self.db.get(CitizenRequest, request_id, populate_existing=True)  # datos frescos, ya bloqueados
        return self.db.get(CitizenRequest, request_id)

    def add(self, request: CitizenRequest) -> CitizenRequest:
        self.db.add(request)
        self.db.flush()  # asigna el id sin cerrar la transacción
        return request

    def _filtered(self, stmt: Select, f: RequestFilters) -> Select:
        if f.citizen_id is not None:
            stmt = stmt.where(CitizenRequest.citizen_id == f.citizen_id)
        if f.official_id is not None:
            stmt = stmt.where(CitizenRequest.official_id == f.official_id)
        if f.number is not None:
            stmt = stmt.where(CitizenRequest.id == f.number)
        if f.status:
            stmt = stmt.where(CitizenRequest.status.has(RequestStatus.code == f.status))
        if f.category:
            stmt = stmt.where(CitizenRequest.category.has(Category.code == f.category))
        return stmt

    def search(self, f: RequestFilters, page: int, size: int) -> tuple[list[CitizenRequest], int]:
        total = self.db.scalar(self._filtered(select(func.count(CitizenRequest.id)), f)) or 0
        stmt = (self._filtered(select(CitizenRequest), f)
                .order_by(CitizenRequest.created_at.desc(), CitizenRequest.id.desc())
                .offset((page - 1) * size).limit(size))
        return list(self.db.scalars(stmt).unique()), total

    def count_by_status(self, f: RequestFilters) -> list[tuple[str, str, int]]:
        stmt = (select(RequestStatus.code, RequestStatus.name, func.count(CitizenRequest.id))
                .select_from(RequestStatus)
                .outerjoin(CitizenRequest, self._scope_join(CitizenRequest.status_id == RequestStatus.id, f))
                .group_by(RequestStatus.code, RequestStatus.name, RequestStatus.sort_order)
                .order_by(RequestStatus.sort_order))
        return [tuple(r) for r in self.db.execute(stmt)]

    def count_by_category(self, f: RequestFilters) -> list[tuple[str, str, int]]:
        stmt = (select(Category.code, Category.name, func.count(CitizenRequest.id))
                .select_from(Category)
                .outerjoin(CitizenRequest, self._scope_join(CitizenRequest.category_id == Category.id, f))
                .group_by(Category.code, Category.name)
                .order_by(Category.name))
        return [tuple(r) for r in self.db.execute(stmt)]

    def count_unassigned(self, f: RequestFilters) -> int:
        stmt = self._filtered(select(func.count(CitizenRequest.id)), f).where(
            CitizenRequest.official_id.is_(None))
        return self.db.scalar(stmt) or 0

    @staticmethod
    def _scope_join(condition, f: RequestFilters):
        # En un LEFT JOIN el alcance va en la condición del join, para que los estados sin
        # solicitudes sigan apareciendo con 0.
        if f.citizen_id is not None:
            condition = condition & (CitizenRequest.citizen_id == f.citizen_id)
        if f.official_id is not None:
            condition = condition & (CitizenRequest.official_id == f.official_id)
        return condition


class HistoryRepository:
    """Solo lectura e inserción. Deliberadamente no existe un método de borrado."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, entry: RequestStatusHistory) -> RequestStatusHistory:
        self.db.add(entry)
        self.db.flush()
        return entry

    def for_request(self, request_id: int) -> list[RequestStatusHistory]:
        stmt = (select(RequestStatusHistory)
                .where(RequestStatusHistory.request_id == request_id)
                .order_by(RequestStatusHistory.changed_at, RequestStatusHistory.id))
        return list(self.db.scalars(stmt).unique())
