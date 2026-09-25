from pydantic import BaseModel, ConfigDict


class CatalogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str


class StatusItem(CatalogItem):
    sort_order: int
    is_final: bool
    allows_assignment: bool


class CatalogsOut(BaseModel):
    categories: list[CatalogItem]
    statuses: list[StatusItem]
