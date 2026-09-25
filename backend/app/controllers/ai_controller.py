from fastapi import APIRouter, Depends

from app.dependencies import get_classifier, require_roles
from app.schemas.ai import ClassificationOut, ClassifyIn
from app.services import roles
from app.services.ai.classifier import RequestClassifier

router = APIRouter(prefix="/ai", tags=["IA"])


@router.post("/classify", response_model=ClassificationOut,
             dependencies=[Depends(require_roles(roles.CITIZEN))])
def classify(data: ClassifyIn, classifier: RequestClassifier = Depends(get_classifier)):
    """Sugiere categoría, prioridad y resumen. No guarda nada: el ciudadano revisa y decide."""
    return classifier.suggest(data)
