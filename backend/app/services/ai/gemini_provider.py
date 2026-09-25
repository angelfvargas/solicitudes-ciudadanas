import httpx

from app.core.errors import AIUnavailableError

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider:
    """Cliente HTTP mínimo de la API de Gemini (Google AI Studio).

    La llave va en una cabecera (no en la URL, para que no quede en logs) y se lee de
    la variable de entorno GEMINI_API_KEY; nunca está en el código.
    """

    def __init__(self, api_key: str, model_name: str, timeout: float):
        self._api_key = api_key
        self.model_name = model_name
        self._timeout = timeout

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> str:
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
                f"{BASE_URL}/models/{self.model_name}:generateContent",
                headers={"x-goog-api-key": self._api_key},
                json=body, timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        except httpx.TimeoutException:
            raise AIUnavailableError("El servicio de IA tardó demasiado. Clasifique manualmente.")
        except (httpx.HTTPError, KeyError, IndexError, ValueError):
            raise AIUnavailableError("El servicio de IA no está disponible. Clasifique manualmente.")
