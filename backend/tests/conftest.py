"""Las pruebas usan SQLite en memoria: son rápidas y no necesitan PostgreSQL.
Cada prueba arranca con una base limpia con los catálogos y usuarios de prueba."""
import os

os.environ.setdefault("JWT_SECRET", "secreto-solo-para-pruebas-no-usar-en-produccion")
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["GEMINI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import models  # noqa: E402,F401
from app.db.seed import seed_catalogs, seed_users  # noqa: E402
from app.db.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with TestSession() as db:
        seed_catalogs(db)
        seed_users(db)
    yield TestSession
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def login(client, email: str, password: str) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def citizen(client):
    return login(client, "ana.torres@example.org", "Ciudadano123")


@pytest.fixture()
def other_citizen(client):
    return login(client, "carlos.ruiz@example.org", "Ciudadano123")


@pytest.fixture()
def admin(client):
    return login(client, "admin@example.com", "Admin12345")


@pytest.fixture()
def official(client):  # Juan Pérez, id 2
    return login(client, "juan.perez@example.com", "Funcionario123")


@pytest.fixture()
def other_official(client):  # María Gómez, id 3
    return login(client, "maria.gomez@example.com", "Funcionario123")


def create_request(client, headers, **overrides) -> dict:
    body = {"subject": "Fuga de agua", "category": "reclamo",
            "description": "Hay una fuga de agua frente a mi casa desde hace tres semanas."}
    body.update(overrides)
    r = client.post("/api/requests", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()
