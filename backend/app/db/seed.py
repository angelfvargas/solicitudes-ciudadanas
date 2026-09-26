"""Datos de referencia (catálogos) y usuarios de prueba.

Es idempotente: se puede correr varias veces sin duplicar nada.
"""
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import PasswordHasher
from app.models import (Category, CitizenRequest, RequestStatus, RequestStatusHistory, Role,
                        StatusTransition, User)

ROLES = [("citizen", "Ciudadano"), ("official", "Funcionario"), ("admin", "Administrador")]

CATEGORIES = [("informacion", "Información"), ("queja", "Queja"), ("reclamo", "Reclamo"),
              ("peticion", "Petición"), ("sugerencia", "Sugerencia")]

# code, nombre, orden, inicial, final, requiere funcionario, permite asignar
STATUSES = [
    ("registered", "Registrada", 1, True, False, False, False),
    ("in_review", "En revisión", 2, False, False, False, True),
    ("assigned", "Asignada", 3, False, False, True, True),
    ("in_progress", "En proceso", 4, False, False, True, True),
    ("resolved", "Resuelta", 5, False, False, True, False),
    ("closed", "Cerrada", 6, False, True, True, False),
]

# (desde, hacia, rol). Lista blanca: lo que no está aquí no se permite.
# Registrada → Cerrada NO está, por eso el sistema la rechaza.
TRANSITIONS = [
    ("registered", "in_review", "admin"),
    ("in_review", "assigned", "admin"),       # normalmente ocurre al asignar funcionario
    ("assigned", "in_progress", "official"),
    ("assigned", "in_progress", "admin"),
    ("in_progress", "resolved", "official"),
    ("in_progress", "resolved", "admin"),
    ("resolved", "closed", "admin"),
    ("resolved", "in_progress", "admin"),     # reabrir si la respuesta no fue suficiente
]

DEMO_PASSWORD = {"admin": "Admin12345", "official": "Funcionario123", "citizen": "Ciudadano123"}
DEMO_USERS = [
    # nombre, apellido, tipo doc, número, correo, rol
    ("Laura", "Méndez", "CC", "1100000001", "admin@example.com", "admin"),
    ("Juan", "Pérez", "CC", "1100000002", "juan.perez@example.com", "official"),
    ("María", "Gómez", "CC", "1100000003", "maria.gomez@example.com", "official"),
    ("Ana", "Torres", "CC", "1100000004", "ana.torres@example.org", "citizen"),
    ("Carlos", "Ruiz", "CE", "E1234567", "carlos.ruiz@example.org", "citizen"),
]

DEMO_REQUESTS = [
    ("Fuga de agua frente a mi vivienda", "Desde hace tres semanas existe una fuga de agua frente a mi vivienda y todavía no ha sido atendida.", "reclamo", "alta"),
    ("Horario de atención de la sede", "Quisiera saber cuál es el horario de atención presencial de la sede principal y si se requiere cita previa.", "informacion", "baja"),
    ("Mal trato en ventanilla", "El funcionario de la ventanilla 3 me atendió de forma grosera y se negó a recibir mis documentos.", "queja", "media"),
    ("Poda de árbol en el parque", "Solicito la poda de un árbol en el parque del barrio porque sus ramas están tocando los cables eléctricos.", "peticion", "alta"),
    ("Más bancas en el parque", "Sugiero instalar más bancas y canecas en el parque central para las personas mayores que lo visitan.", "sugerencia", "baja"),
    ("Hueco en la vía principal", "En la calle principal del barrio hay un hueco muy grande que ya causó dos accidentes de motos.", "reclamo", "alta"),
    ("Certificado de residencia", "Necesito que me expidan un certificado de residencia para un trámite de estudio de mi hijo.", "peticion", "media"),
    ("Alumbrado público dañado", "Las lámparas del alumbrado público de la cuadra llevan un mes apagadas y la zona está muy oscura.", "reclamo", "media"),
]


def _get_or_create(db: Session, model, lookup: dict, **values):
    obj = db.scalar(select(model).filter_by(**lookup))
    if obj is None:
        obj = model(**lookup, **values)
        db.add(obj)
        db.flush()
    return obj


def seed_catalogs(db: Session) -> None:
    for code, name in ROLES:
        _get_or_create(db, Role, {"code": code}, name=name)
    for code, name in CATEGORIES:
        _get_or_create(db, Category, {"code": code}, name=name)
    for code, name, order, initial, final, needs_official, assignable in STATUSES:
        _get_or_create(db, RequestStatus, {"code": code}, name=name, sort_order=order,
                       is_initial=initial, is_final=final, requires_official=needs_official,
                       allows_assignment=assignable)
    status = {s.code: s.id for s in db.scalars(select(RequestStatus))}
    role = {r.code: r.id for r in db.scalars(select(Role))}
    for src, dst, rol in TRANSITIONS:
        _get_or_create(db, StatusTransition, {"from_status_id": status[src],
                       "to_status_id": status[dst], "role_id": role[rol]})
    db.commit()


def seed_users(db: Session) -> None:
    hasher = PasswordHasher()
    role = {r.code: r.id for r in db.scalars(select(Role))}
    for first, last, doc_type, doc, email, rol in DEMO_USERS:
        _get_or_create(db, User, {"email": email}, first_name=first, last_name=last,
                       document_type=doc_type, document_number=doc, role_id=role[rol],
                       password_hash=hasher.hash(DEMO_PASSWORD[rol]))
    db.commit()


def seed_demo_requests(db: Session, total: int = 40) -> None:
    """Solicitudes de ejemplo con historial coherente, para el tablero y las consultas SQL."""
    if db.scalar(select(CitizenRequest.id).limit(1)) is not None:
        return
    rng = random.Random(42)
    st = {s.code: s for s in db.scalars(select(RequestStatus))}
    cat = {c.code: c for c in db.scalars(select(Category))}
    users = {u.email: u for u in db.scalars(select(User))}
    admin = users["admin@example.com"]
    officials = [users["juan.perez@example.com"], users["maria.gomez@example.com"]]
    citizens = [users["ana.torres@example.org"], users["carlos.ruiz@example.org"]]
    path = ["registered", "in_review", "assigned", "in_progress", "resolved", "closed"]
    now = datetime.now(timezone.utc)

    for i in range(total):
        subject, description, category, priority = DEMO_REQUESTS[i % len(DEMO_REQUESTS)]
        citizen = citizens[i % 2]
        created = now - timedelta(days=rng.randint(1, 60), hours=rng.randint(0, 23))
        final_step = rng.choice([0, 0, 1, 2, 3, 3, 4, 4, 5])  # hasta qué estado llegó
        request = CitizenRequest(citizen_id=citizen.id, category_id=cat[category].id,
                                 status_id=st["registered"].id, subject=subject,
                                 description=description, priority=priority,
                                 created_at=created, updated_at=created)
        db.add(request)
        db.flush()
        db.add(RequestStatusHistory(request_id=request.id, action="created", new_status_id=st["registered"].id,
                                    changed_by_id=citizen.id, changed_at=created,
                                    observation="Solicitud registrada por el ciudadano."))
        moment, official = created, None
        for step in range(1, final_step + 1):
            moment += timedelta(hours=rng.randint(2, 48))
            code = path[step]
            actor = admin
            note = None
            if code == "assigned":
                official = rng.choice(officials)
                note = f"Solicitud asignada a {official.full_name}."
            elif code in ("in_progress", "resolved"):
                actor = official
                note = ("Se inició la validación de la información." if code == "in_progress"
                        else "Se atendió la solicitud y se informó al ciudadano.")
            db.add(RequestStatusHistory(
                request_id=request.id, action="assignment" if code == "assigned" else "status_change",
                previous_status_id=st[path[step - 1]].id, new_status_id=st[code].id, changed_by_id=actor.id,
                assigned_official_id=official.id if code == "assigned" else None,
                observation=note, changed_at=moment))
        request.status_id = st[path[final_step]].id
        request.official_id = official.id if official else None
        request.updated_at = moment
    db.commit()
