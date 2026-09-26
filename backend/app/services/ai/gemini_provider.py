import logging
import re

import httpx

from app.core.errors import AIUnavailableError

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
BUSY_STATUS = {429, 500, 502, 503, 504}
log = logging.getLogger("uvicorn.error")

# Modelos descubiertos en la API cuando los configurados ya no existen (Google los retira seguido).
_discovered: list[str] | None = None


class _TryNext(Exception):
    """El modelo está saturado, tardó demasiado o ya no existe: vale la pena probar otro."""

    def __init__(self, not_found: bool = False):
        self.not_found = not_found


def rank_flash_models(names: list[str]) -> list[str]:
    """Modelos 'flash' de Gemini, del más nuevo al más viejo; a igual versión, el normal antes que lite."""
    flash = [n for n in names if re.fullmatch(r"gemini-\d+(\.\d+)?-flash(-lite)?", n)]
    return sorted(flash, key=lambda n: (float(re.search(r"\d+(\.\d+)?", n).group()), "lite" not in n),
                  reverse=True)


class GeminiProvider:
    """Cliente HTTP mínimo de la API de Gemini (Google AI Studio).

    La llave va en una cabecera (no en la URL, para que no quede en logs) y se lee de
    la variable de entorno GEMINI_API_KEY; nunca está en el código.

    GEMINI_MODEL admite varios modelos separados por coma: si uno está saturado (429/5xx o
    tiempo agotado) se intenta el siguiente. Si ninguno de los configurados existe ya, se
    consulta a Google qué modelos 'flash' hay disponibles y se usan esos.
    """

    def __init__(self, api_key: str, model_names: str, timeout: float):
        self._api_key = api_key
        self._models = [m.strip() for m in model_names.split(",") if m.strip()]
        self.model_name = self._models[0]
        self._timeout = timeout

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> str:
        global _discovered
        tried: set[str] = set()
        all_missing = True
        candidates = list(self._models)
        if _discovered:
            candidates += [m for m in _discovered if m not in candidates]
        for model in candidates:
            tried.add(model)
            try:
                return self._use(model, system_prompt, user_prompt, schema)
            except _TryNext as e:
                all_missing = all_missing and e.not_found

        if all_missing and _discovered is None:
            _discovered = self._discover()
            for model in [m for m in _discovered if m not in tried]:
                try:
                    return self._use(model, system_prompt, user_prompt, schema)
                except _TryNext:
                    continue
        raise AIUnavailableError("El servicio de IA está saturado o no disponible en este momento. "
                                 "Clasifique manualmente.")

    def _use(self, model: str, system_prompt: str, user_prompt: str, schema: dict) -> str:
        text = self._call(model, system_prompt, user_prompt, schema)
        self.model_name = model  # el que respondió; se muestra en la sugerencia
        return text

    def _discover(self) -> list[str]:
        try:
            r = httpx.get(f"{BASE_URL}/models", headers={"x-goog-api-key": self._api_key},
                          timeout=self._timeout)
            if r.status_code != 200:
                return []
            names = [m["name"].removeprefix("models/") for m in r.json().get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])]
            return rank_flash_models(names)
        except (httpx.HTTPError, KeyError, ValueError):
            return []

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
            raise _TryNext() from None
        except httpx.HTTPError:
            raise AIUnavailableError("No se pudo conectar con el servicio de IA. Clasifique manualmente.") from None

        if response.status_code != 200:
            # Se registra el código y el mensaje de Google para diagnóstico (nunca la llave).
            log.warning("Gemini %s respondió %s: %s", model, response.status_code, response.text[:300])
        if response.status_code in BUSY_STATUS:
            raise _TryNext()
        if response.status_code == 404:  # el modelo ya no existe
            raise _TryNext(not_found=True)
        if response.status_code != 200:
            raise AIUnavailableError("El servicio de IA rechazó la solicitud (revise la llave). "
                                     "Clasifique manualmente.")
        try:
            data = response.json()
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError, ValueError):
            raise AIUnavailableError("El servicio de IA devolvió una respuesta vacía. "
                                     "Clasifique manualmente.") from None
