#!/usr/bin/env bash
# Arranca la aplicación completa (base de datos + API + página web) en http://localhost:8000
#
#   ./iniciar.sh          con IA (usa la llave guardada con ./configurar_ia.sh)
#   ./iniciar.sh sin-ia   sin IA (la categoría se elige a mano)
#
# Para detenerla: Ctrl+C. Para cambiar de modo: detener y volver a arrancar.
set -e
cd "$(dirname "$0")"

# Base de datos de desarrollo (solo si backend/.env apunta a la de scripts/dev_postgres.py)
if grep -q "\.pgdata" backend/.env 2>/dev/null; then
  .venv/bin/python scripts/dev_postgres.py > /dev/null
fi

# Página web compilada (la sirve el mismo backend: monolito)
[ -f frontend/dist/index.html ] || (cd frontend && npm run build)

# La llave de IA se toma de backend/.env; se ignora cualquier otra que haya en la terminal.
unset GEMINI_API_KEY
if [ "$1" = "sin-ia" ]; then
  export GEMINI_API_KEY=""
  echo "Modo: SIN IA"
elif grep -qE "^GEMINI_API_KEY=.+" backend/.env; then
  echo "Modo: CON IA"
else
  echo "Modo: SIN IA (no hay llave guardada; use ./configurar_ia.sh)"
fi

echo "Abra http://localhost:8000   —   Ctrl+C para detener"
cd backend
exec ../.venv/bin/uvicorn app.main:app --port 8000
