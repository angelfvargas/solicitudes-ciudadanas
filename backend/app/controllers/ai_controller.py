from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.dependencies import get_classifier, get_current_user, require_roles
from app.schemas.ai import ClassificationOut, ClassifyIn
from app.services import roles
from app.services.ai.classifier import RequestClassifier

router = APIRouter(prefix="/ai", tags=["IA"])


@router.post("/classify", response_model=ClassificationOut,
             dependencies=[Depends(require_roles(roles.CITIZEN))])
def classify(data: ClassifyIn, classifier: RequestClassifier = Depends(get_classifier)):
    """Sugiere categoría, prioridad y resumen. No guarda nada: el ciudadano revisa y decide."""
    return classifier.suggest(data)


@router.get("/status", dependencies=[Depends(get_current_user)])
def ai_status():
    """Indica si la IA está configurada, para que la interfaz lo muestre. Nunca devuelve la llave."""
    settings = get_settings()
    enabled = bool(settings.gemini_api_key)
    return {"enabled": enabled, "provider": "Google Gemini" if enabled else None,
            "model": settings.gemini_model if enabled else None}
