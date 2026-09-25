"""Máquina de estados de la solicitud.

Las transiciones permitidas NO están escritas en el código: se leen de la tabla
status_transitions (lista blanca por rol). Agregar un paso nuevo al flujo, o dar
permiso a otro rol, es insertar una fila; esta clase no cambia (Abierto/Cerrado).
"""
from app.core.errors import BusinessRuleError, PermissionDeniedError
from app.models import CitizenRequest, RequestStatus, User
from app.repositories.catalog_repository import CatalogRepository


class StatusWorkflow:
    def __init__(self, catalogs: CatalogRepository):
        self.catalogs = catalogs

    def allowed_targets(self, current: RequestStatus, role_code: str) -> list[RequestStatus]:
        return [t.to_status for t in self.catalogs.transitions_from(current.id)
                if t.role.code == role_code]

    def ensure_can_move(self, request: CitizenRequest, target: RequestStatus, actor: User) -> None:
        current = request.status
        if target.id == current.id:
            raise BusinessRuleError(f"La solicitud ya está en estado {current.name}.")

        transitions = self.catalogs.transitions_from(current.id)
        valid_targets = {t.to_status_id for t in transitions}
        if target.id not in valid_targets:
            options = sorted({t.to_status.name for t in transitions}) or ["ninguno (estado final)"]
            raise BusinessRuleError(
                f"Transición no permitida: {current.name} → {target.name}. "
                f"Desde {current.name} solo se puede pasar a: {', '.join(options)}.")

        if not any(t.to_status_id == target.id and t.role_id == actor.role_id for t in transitions):
            raise PermissionDeniedError(
                f"Su rol no puede mover solicitudes de {current.name} a {target.name}.")

        if target.requires_official and request.official_id is None:
            raise BusinessRuleError(
                f"Para pasar a {target.name} la solicitud debe tener un funcionario asignado.")
