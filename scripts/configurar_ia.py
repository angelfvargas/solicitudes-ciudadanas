"""Guarda y prueba la llave de Gemini. Lo usa ./configurar_ia.sh (ver ese archivo)."""
import getpass
import re
import sys
from pathlib import Path

import httpx

ENV_FILE = Path(__file__).resolve().parent.parent / "backend" / ".env"
BASE = "https://generativelanguage.googleapis.com/v1beta"
BUSY = {429, 500, 503, 504}  # Google saturado o cuota momentánea: no es culpa de la llave


def set_env(values: dict[str, str]) -> None:
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    for key, value in values.items():
        new = f"{key}={value}"
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = new
                break
        else:
            lines.append(new)
    ENV_FILE.write_text("\n".join(lines) + "\n")


def flash_models(key: str) -> list[str]:
    """Modelos 'flash' disponibles para esta llave, del más nuevo al más viejo (los nombres cambian)."""
    r = httpx.get(f"{BASE}/models", headers={"x-goog-api-key": key}, timeout=20)
    r.raise_for_status()  # si la llave es inválida, falla aquí (400/401/403)
    names = [m["name"].removeprefix("models/") for m in r.json().get("models", [])
             if "generateContent" in m.get("supportedGenerationMethods", [])]
    flash = [n for n in names if re.fullmatch(r"gemini-[\d.]+-flash(-lite)?", n)]

    def rank(n: str):
        version = float(re.search(r"[\d.]+", n).group().rstrip("."))
        return (version, "lite" not in n)  # más nuevo primero; a igual versión, el normal antes que lite
    return sorted(flash, key=rank, reverse=True)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "quitar":
        set_env({"GEMINI_API_KEY": ""})
        print("Llave borrada. La app arrancará sin IA.")
        return

    print("Pegue la llave de https://aistudio.google.com/apikey y presione Enter")
    print("(no se verá mientras la pega, es normal):")
    key = getpass.getpass("> ").strip()
    if not key:
        print("No se pegó nada. No se cambió nada.")
        sys.exit(1)

    print("Probando la llave con Google…")
    try:
        models = flash_models(key)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in BUSY:
            print(f"✗ Google está saturado ahora (error {e.response.status_code}). Intente en unos minutos.")
        else:
            print(f"✗ Google rechazó la llave (error {e.response.status_code}). No se guardó.")
            print("  Revise que la copió completa, o pruebe con la otra llave de la lista.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ No se pudo conectar con Google: {e}. No se guardó.")
        sys.exit(1)
    if not models:
        print("✗ La llave es válida, pero no tiene modelos 'flash' disponibles. No se guardó.")
        sys.exit(1)
    print("✓ Google reconoció la llave.")

    # Se prueba cada modelo hasta encontrar uno que responda en este momento.
    working = []
    for model in models:
        try:
            r = httpx.post(f"{BASE}/models/{model}:generateContent", headers={"x-goog-api-key": key},
                           json={"contents": [{"parts": [{"text": "Responde solo: ok"}]}]}, timeout=30)
            status = r.status_code
        except httpx.HTTPError:
            status = 0
        print(f"  {model}: {'responde ✓' if status == 200 else f'no responde ahora (error {status})'}")
        if status == 200:
            working.append(model)
        if len(working) == 2:
            break

    # Se guardan varios modelos en orden: si el primero está saturado, la app usa el siguiente.
    chosen = working + [m for m in models if m not in working]
    set_env({"GEMINI_API_KEY": key, "GEMINI_MODEL": ",".join(chosen[:4])})
    if working:
        print(f"✓ Llave guardada en backend/.env. Modelo principal: {chosen[0]}.")
    else:
        print("✓ Llave guardada en backend/.env, pero AHORA MISMO todos los modelos de Google están")
        print("  saturados (no es problema suyo ni de la llave). La app funcionará sin IA hasta que")
        print("  Google se recupere, y mostrará 'clasifique manualmente'.")
    print("  Si la app ya estaba abierta: Ctrl+C y vuelva a correr ./iniciar.sh")


if __name__ == "__main__":
    main()
