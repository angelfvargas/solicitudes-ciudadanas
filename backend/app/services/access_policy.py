"""Quién puede VER qué solicitud. Una sola responsabilidad, un solo lugar.

Aquí se resuelve la situación de la sustentación: cambiar el id en la URL no sirve,
porque el backend verifica la pertenencia de cada solicitud, no solo que haya sesión.
"""
from app.models import CitizenRequest, User
from app.repositories.request_repository import RequestFilters
from app.services import roles


class RequestAccessPolicy:
    def can_view(self, user: User, request: CitizenRequest) -> bool:
        role = user.role.code
        if role == roles.ADMIN:
            return True
        if role == roles.OFFICIAL:
            return request.official_id == user.id
        return request.citizen_id == user.id

    def scope(self, user: User, filters: RequestFilters) -> RequestFilters:
        """Restringe cualquier listado al alcance del usuario, sin importar los filtros pedidos."""
        role = user.role.code
        if role == roles.CITIZEN:
            filters.citizen_id = user.id
        elif role == roles.OFFICIAL:
            filters.official_id = user.id
        return filters
