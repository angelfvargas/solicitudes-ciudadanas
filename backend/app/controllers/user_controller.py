from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_roles
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserAdminOut
from app.services import roles

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("", response_model=list[UserAdminOut],
            dependencies=[Depends(require_roles(roles.ADMIN))])
def list_users(role: str | None = Query(None, description="citizen | official | admin"),
               db: Session = Depends(get_db)):
    return UserRepository(db).list(role)
