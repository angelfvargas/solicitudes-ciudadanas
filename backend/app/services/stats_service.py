from app.models import User
from app.repositories.request_repository import RequestFilters, RequestRepository
from app.schemas.request import StatsOut
from app.services.access_policy import RequestAccessPolicy


class StatsService:
    """Cifras del tablero, siempre dentro del alcance del usuario que las pide."""

    def __init__(self, requests: RequestRepository, access: RequestAccessPolicy):
        self.requests = requests
        self.access = access

    def for_user(self, actor: User) -> StatsOut:
        scope = self.access.scope(actor, RequestFilters())
        by_status = [{"code": c, "name": n, "count": k}
                     for c, n, k in self.requests.count_by_status(scope)]
        by_category = [{"code": c, "name": n, "count": k}
                       for c, n, k in self.requests.count_by_category(scope)]
        return StatsOut(
            total=sum(s["count"] for s in by_status),
            by_status=by_status,
            by_category=by_category,
            unassigned=self.requests.count_unassigned(scope),
        )
