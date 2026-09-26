from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user, get_request_service, require_roles
from app.models import User
from app.repositories.request_repository import RequestFilters
from app.schemas.catalog import CatalogItem
from app.schemas.request import (AssignIn, HistoryItem, ObservationIn, RequestCreate, RequestDetail,
                                 RequestPage, StatusChangeIn)
from app.services import roles
from app.services.request_service import RequestService

router = APIRouter(prefix="/requests", tags=["Solicitudes"])


@router.get("", response_model=RequestPage)
def list_requests(
    status_code: str | None = Query(None, alias="status", description="Código del estado"),
    category: str | None = Query(None, description="Código de la categoría"),
    number: str | None = Query(None, description="Número de solicitud, con o sin ceros"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: RequestService = Depends(get_request_service),
):
    """Ciudadano: sus solicitudes. Funcionario: las asignadas. Administrador: todas."""
    parsed_number = int(number) if number and number.strip().isdigit() else None
    if number and parsed_number is None:
        return RequestPage(items=[], total=0, page=page, size=size)
    filters = RequestFilters(status=status_code, category=category, number=parsed_number)
    items, total = service.search(user, filters, page, size)
    return RequestPage(items=items, total=total, page=page, size=size)


@router.post("", response_model=RequestDetail, status_code=status.HTTP_201_CREATED)
def create_request(data: RequestCreate,
                   user: User = Depends(require_roles(roles.CITIZEN)),
                   service: RequestService = Depends(get_request_service)):
    return service.create(user, data)


@router.get("/{request_id}", response_model=RequestDetail)
def get_request(request_id: int, user: User = Depends(get_current_user),
                service: RequestService = Depends(get_request_service)):
    return service.get_visible(user, request_id)


@router.put("/{request_id}/status", response_model=RequestDetail)
def change_status(request_id: int, data: StatusChangeIn,
                  user: User = Depends(require_roles(roles.OFFICIAL, roles.ADMIN)),
                  service: RequestService = Depends(get_request_service)):
    return service.change_status(user, request_id, data)


@router.put("/{request_id}/assign", response_model=RequestDetail)
def assign(request_id: int, data: AssignIn,
           user: User = Depends(require_roles(roles.ADMIN)),
           service: RequestService = Depends(get_request_service)):
    return service.assign(user, request_id, data)


@router.post("/{request_id}/observations", response_model=HistoryItem, status_code=status.HTTP_201_CREATED)
def add_observation(request_id: int, data: ObservationIn,
                    user: User = Depends(require_roles(roles.OFFICIAL, roles.ADMIN)),
                    service: RequestService = Depends(get_request_service)):
    """Agrega una observación sin cambiar el estado. Queda en el historial."""
    return service.add_observation(user, request_id, data)


@router.get("/{request_id}/history", response_model=list[HistoryItem])
def history(request_id: int, user: User = Depends(get_current_user),
            service: RequestService = Depends(get_request_service)):
    return service.history_of(user, request_id)


@router.get("/{request_id}/transitions", response_model=list[CatalogItem])
def allowed_transitions(request_id: int, user: User = Depends(get_current_user),
                        service: RequestService = Depends(get_request_service)):
    """Estados a los que el usuario actual puede mover la solicitud. La interfaz solo ofrece
    estos; aun así, PUT /status vuelve a validar todo."""
    return service.allowed_statuses(user, request_id)
