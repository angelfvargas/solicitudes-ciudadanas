"""Levanta un PostgreSQL local sin instalar nada en el sistema (paquete pgserver).

Solo para desarrollo, si no tienes PostgreSQL instalado. Si ya tienes uno, no lo necesitas:
pon su URL en backend/.env (DATABASE_URL).

Uso:  python scripts/dev_postgres.py          → arranca y muestra la DATABASE_URL
      python scripts/dev_postgres.py stop     → lo detiene
"""
import sys
from pathlib import Path

import pgserver

DATA_DIR = Path(__file__).resolve().parent.parent / ".pgdata"

if len(sys.argv) > 1 and sys.argv[1] == "stop":
    pgserver.get_server(DATA_DIR, cleanup_mode="stop").cleanup()
    print("PostgreSQL detenido.")
    sys.exit(0)

server = pgserver.get_server(DATA_DIR, cleanup_mode=None)  # queda corriendo en segundo plano
exists = server.psql("SELECT 1 FROM pg_database WHERE datname = 'vennex';")
if "1 row" not in exists:
    server.psql("CREATE DATABASE vennex;")
print("PostgreSQL corriendo. Pon esta línea en backend/.env:")
print(f"DATABASE_URL=postgresql+psycopg://postgres:@/vennex?host={DATA_DIR}")
