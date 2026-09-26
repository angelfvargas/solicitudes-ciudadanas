from app.core.errors import BusinessRuleError, NotFoundError, PermissionDeniedError
from app.models import CitizenRequest, RequestStatusHistory, User
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.request_repository import HistoryRepository, RequestFilters, RequestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.request import AssignIn, RequestCreate, StatusChangeIn
from app.services import roles
from app.services.access_policy import RequestAccessPolicy
from app.services.workflow import StatusWorkflow


class RequestService:
    """Casos de uso de la solicitud. Cada operación que cambia el estado o el funcionario
    escribe la solicitud y su registro de historial en la MISMA transacción: o quedan
    los dos, o ninguno."""

    def __init__(self, requests: RequestRepository, history: HistoryRepository,
                 users: UserRepository, catalogs: CatalogRepository,
                 workflow: StatusWorkflow, access: RequestAccessPolicy):
        self.requests = requests
        self.history = history
        self.users = users
        self.catalogs = catalogs
        self.workflow = workflow
        self.access = access

    # --- consultas ---------------------------------------------------------------

    def search(self, actor: User, filters: RequestFilters, page: int, size: int):
        return self.requests.search(self.access.scope(actor, filters), page, size)

    def get_visible(self, actor: User, request_id: int, for_update: bool = False) -> CitizenRequest:
        request = self.requests.get(request_id, for_update=for_update)
        # 404 (y no 403) si no le pertenece: no se confirma que la solicitud exista.
        if request is None or not self.access.can_view(actor, request):
            raise NotFoundError("Solicitud no encontrada.")
        return request

    def history_of(self, actor: User, request_id: int) -> list[RequestStatusHistory]:
        self.get_visible(actor, request_id)
        return self.history.for_request(request_id)

    def allowed_statuses(self, actor: User, request_id: int):
        """Estados a los que ESTE usuario puede mover la solicitud ahora (para armar la interfaz)."""
        request = self.get_visible(actor, request_id)
        targets = self.workflow.allowed_targets(request.status, actor.role.code)
        return [t for t in targets if not (t.requires_official and request.official_id is None)]

    # --- comandos ----------------------------------------------------------------

    def create(self, actor: User, data: RequestCreate) -> CitizenRequest:
        if actor.role.code != roles.CITIZEN:
            raise PermissionDeniedError("Solo los ciudadanos registran solicitudes.")
        category = self.catalogs.category_by_code(data.category)
        if category is None:
            raise BusinessRuleError("La categoría seleccionada no existe.")
        initial = self.catalogs.initial_status()
        request = self.requests.add(CitizenRequest(
            citizen_id=actor.id, category_id=category.id, status_id=initial.id,
            subject=data.subject, description=data.description,
            priority=data.priority, ai_summary=data.ai_summary,
        ))
        self.history.add(RequestStatusHistory(
            request_id=request.id, previous_status_id=None, new_status_id=initial.id,
            changed_by_id=actor.id, observation="Solicitud registrada por el ciudadano.",
        ))
        self.requests.db.commit()
        return self.requests.get(request.id)

    def change_status(self, actor: User, request_id: int, data: StatusChangeIn) -> CitizenRequest:
        request = self.get_visible(actor, request_id, for_update=True)
        target = self.catalogs.status_by_code(data.status)
        if target is None:
            raise BusinessRuleError("El estado indicado no existe.")
        self.workflow.ensure_can_move(request, target, actor)

        previous_id = request.status_id
        request.status_id = target.id
        self.history.add(RequestStatusHistory(
            request_id=request.id, previous_status_id=previous_id, new_status_id=target.id,
            changed_by_id=actor.id, assigned_official_id=request.official_id,
            observation=_clean(data.observation),
        ))
        self.requests.db.commit()
        self.requests.db.refresh(request)
        return request

    def assign(self, actor: User, request_id: int, data: AssignIn) -> CitizenRequest:
        if actor.role.code != roles.ADMIN:
            raise PermissionDeniedError("Solo el administrador asigna solicitudes.")
        request = self.get_visible(actor, request_id, for_update=True)
        if not request.status.allows_assignment:
            raise BusinessRuleError(
                f"No se puede asignar una solicitud en estado {request.status.name}.")
        official = self.users.get(data.official_id)
        if official is None or official.role.code != roles.OFFICIAL or not official.is_active:
            raise BusinessRuleError("El usuario seleccionado no es un funcionario activo.")
        if request.official_id == official.id:
            raise BusinessRuleError(f"La solicitud ya está asignada a {official.full_name}.")

        previous = request.status
        request.official_id = official.id
        # Si está "En revisión", asignar la mueve a "Asignada" (validado por el flujo como
        # cualquier otra transición). Si ya estaba en curso, es una reasignación sin cambio de estado.
        target = previous
        assigned = self.catalogs.status_by_code("assigned")
        if assigned and assigned.id in {t.to_status_id for t in self.catalogs.transitions_from(previous.id)}:
            self.workflow.ensure_can_move(request, assigned, actor)
            target = assigned
            request.status_id = assigned.id

        default_note = ("Solicitud asignada a " if target.id != previous.id else "Reasignada a ")
        self.history.add(RequestStatusHistory(
            request_id=request.id, previous_status_id=previous.id, new_status_id=target.id,
            changed_by_id=actor.id, assigned_official_id=official.id,
            observation=_clean(data.observation) or default_note + official.full_name + ".",
        ))
        self.requests.db.commit()
        self.requests.db.refresh(request)
        return request


def _clean(text: str | None) -> str | None:
    text = (text or "").strip()
    return text or None
