#!/usr/bin/env bash
# Guarda la llave de Gemini en backend/.env y la prueba contra Google.
# La llave no se muestra en pantalla ni queda en el historial de la terminal.
#
#   ./configurar_ia.sh           pide la llave (péguela y presione Enter)
#   ./configurar_ia.sh quitar    borra la llave guardada
cd "$(dirname "$0")"
exec .venv/bin/python scripts/configurar_ia.py "$@"
