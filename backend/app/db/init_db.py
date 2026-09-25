"""Crea las tablas, el trigger de inmutabilidad y los datos iniciales.

Uso:  python -m app.db.init_db          (catálogos + usuarios de prueba)
      python -m app.db.init_db --demo   (además, 40 solicitudes de ejemplo)
"""
import sys

from sqlalchemy import text

from app import models  # noqa: F401  (registra los modelos en Base.metadata)
from app.db.seed import seed_catalogs, seed_demo_requests, seed_users
from app.db.session import Base, SessionLocal, engine

# Segunda barrera para la regla "el historial no se puede borrar": aunque alguien
# saltara la API, la base de datos rechaza UPDATE y DELETE sobre el historial.
IMMUTABLE_HISTORY_SQL = """
CREATE OR REPLACE FUNCTION forbid_history_change() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'El historial de solicitudes es inmutable (operación % rechazada)', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_history_immutable ON request_status_history;
CREATE TRIGGER trg_history_immutable
    BEFORE UPDATE OR DELETE ON request_status_history
    FOR EACH ROW EXECUTE FUNCTION forbid_history_change();
"""


def init_db(demo: bool = False) -> None:
    Base.metadata.create_all(engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text(IMMUTABLE_HISTORY_SQL))
    with SessionLocal() as db:
        seed_catalogs(db)
        seed_users(db)
        if demo:
            seed_demo_requests(db)


if __name__ == "__main__":
    init_db(demo="--demo" in sys.argv)
    print("Base de datos lista.")
