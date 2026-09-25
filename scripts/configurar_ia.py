"""Guarda y prueba la llave de Gemini. Lo usa ./configurar_ia.sh (ver ese archivo)."""
import getpass
import re
import sys
from pathlib import Path

import httpx

ENV_FILE = Path(__file__).resolve().parent.parent / "backend" / ".env"
BASE = "https://generativelanguage.googleapis.com/v1beta"


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


def pick_model(key: str) -> str:
    """Elige el modelo 'flash' más reciente disponible para esta llave (los nombres cambian)."""
    r = httpx.get(f"{BASE}/models", headers={"x-goog-api-key": key}, timeout=20)
    r.raise_for_status()
    names = [m["name"].removeprefix("models/") for m in r.json().get("models", [])
             if "generateContent" in m.get("supportedGenerationMethods", [])]
    flash = [n for n in names if re.fullmatch(r"gemini-[\d.]+-flash", n)]
    if not flash:
        raise RuntimeError("La llave funciona, pero no tiene modelos 'flash' disponibles.")
    return max(flash, key=lambda n: [float(x) for x in re.findall(r"[\d.]+", n)[:1]])


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
        model = pick_model(key)
        test = httpx.post(f"{BASE}/models/{model}:generateContent", headers={"x-goog-api-key": key},
                          json={"contents": [{"parts": [{"text": "Responde solo: ok"}]}]}, timeout=30)
        test.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"✗ Google rechazó la llave (error {e.response.status_code}). No se guardó.")
        print("  Revise que la copió completa, o cree otra en https://aistudio.google.com/apikey")
        sys.exit(1)
    except Exception as e:  # sin internet, sin modelos, etc.
        print(f"✗ No se pudo probar: {e}. No se guardó.")
        sys.exit(1)

    set_env({"GEMINI_API_KEY": key, "GEMINI_MODEL": model})
    print(f"✓ Llave válida y guardada en backend/.env (modelo {model}).")
    print("  Si la app ya estaba abierta: Ctrl+C y vuelva a correr ./iniciar.sh")


if __name__ == "__main__":
    main()
