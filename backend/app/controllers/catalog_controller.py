from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, get_stats_service
from app.models import User
from app.repositories.catalog_repository import CatalogRepository
from app.schemas.catalog import CatalogsOut
from app.schemas.request import StatsOut
from app.services.stats_service import StatsService

router = APIRouter(tags=["Catálogos y tablero"])


@router.get("/catalogs", response_model=CatalogsOut)
def catalogs(db: Session = Depends(get_db)):
    """Categorías y estados para los formularios y filtros (públicos: el registro no los necesita,
    pero no contienen información sensible)."""
    repo = CatalogRepository(db)
    return CatalogsOut(categories=repo.categories(), statuses=repo.statuses())


@router.get("/stats", response_model=StatsOut)
def stats(user: User = Depends(get_current_user), service: StatsService = Depends(get_stats_service)):
    return service.for_user(user)
