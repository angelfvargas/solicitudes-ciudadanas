import httpx

from app.core.errors import AIUnavailableError

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
BUSY_STATUS = {429, 500, 502, 503, 504}


class _ModelBusy(Exception):
    """El modelo está saturado o no respondió a tiempo: vale la pena probar el siguiente."""


class GeminiProvider:
    """Cliente HTTP mínimo de la API de Gemini (Google AI Studio).

    La llave va en una cabecera (no en la URL, para que no quede en logs) y se lee de
    la variable de entorno GEMINI_API_KEY; nunca está en el código.

    GEMINI_MODEL admite varios modelos separados por coma: si uno está saturado (429/5xx o
    tiempo agotado), se intenta con el siguiente. La capa gratuita de Gemini se satura seguido.
    """

    def __init__(self, api_key: str, model_names: str, timeout: float):
        self._api_key = api_key
        self._models = [m.strip() for m in model_names.split(",") if m.strip()]
        self.model_name = self._models[0]
        self._timeout = timeout

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> str:
        for model in self._models:
            try:
                text = self._call(model, system_prompt, user_prompt, schema)
                self.model_name = model  # el que respondió; se muestra en la sugerencia
                return text
            except _ModelBusy:
                continue
        raise AIUnavailableError("El servicio de IA está saturado en este momento. Clasifique manualmente.")

    def _call(self, model: str, system_prompt: str, user_prompt: str, schema: dict) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.1,  # clasificación: se quiere consistencia, no creatividad
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        }
        try:
            response = httpx.post(
                f"{BASE_URL}/models/{model}:generateContent",
                headers={"x-goog-api-key": self._api_key},
                json=body, timeout=self._timeout,
            )
        except httpx.TimeoutException:
            raise _ModelBusy()
        except httpx.HTTPError:
            raise AIUnavailableError("No se pudo conectar con el servicio de IA. Clasifique manualmente.")

        if response.status_code in BUSY_STATUS:
            raise _ModelBusy()
        if response.status_code != 200:
            raise AIUnavailableError("El servicio de IA rechazó la solicitud. Clasifique manualmente.")
        try:
            data = response.json()
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError, ValueError):
            raise AIUnavailableError("El servicio de IA devolvió una respuesta vacía. Clasifique manualmente.")
