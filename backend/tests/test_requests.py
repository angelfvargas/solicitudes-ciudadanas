from tests.conftest import create_request


def test_create_request_sets_initial_state_and_history(client, citizen):
    req = create_request(client, citizen)
    assert req["status"]["code"] == "registered"
    assert req["number"] == f"{req['id']:06d}"
    history = client.get(f"/api/requests/{req['id']}/history", headers=citizen).json()
    assert len(history) == 1
    assert history[0]["previous_status"] is None and history[0]["new_status"]["code"] == "registered"


def test_request_validation(client, citizen):
    r = client.post("/api/requests", headers=citizen,
                    json={"subject": "abc", "description": "corta", "category": "reclamo"})
    assert r.status_code == 422
    r = client.post("/api/requests", headers=citizen, json={
        "subject": "Asunto válido", "description": "x" * 30, "category": "no-existe"})
    assert r.status_code == 422


def test_only_citizens_create_requests(client, admin):
    r = client.post("/api/requests", headers=admin, json={
        "subject": "Asunto válido", "description": "x" * 30, "category": "queja"})
    assert r.status_code == 403


def test_citizen_cannot_read_other_citizens_request_by_changing_id(client, citizen, other_citizen):
    req = create_request(client, citizen)
    assert client.get(f"/api/requests/{req['id']}", headers=other_citizen).status_code == 404
    assert client.get(f"/api/requests/{req['id']}/history", headers=other_citizen).status_code == 404
    assert client.get("/api/requests", headers=other_citizen).json()["total"] == 0


def test_registered_to_closed_is_rejected(client, citizen, admin):
    req = create_request(client, citizen)
    r = client.put(f"/api/requests/{req['id']}/status", headers=admin, json={"status": "closed"})
    assert r.status_code == 422
    assert "Registrada → Cerrada" in r.json()["detail"]
    # y no dejó rastro: sigue Registrada con un solo registro de historial
    assert client.get(f"/api/requests/{req['id']}", headers=admin).json()["status"]["code"] == "registered"
    assert len(client.get(f"/api/requests/{req['id']}/history", headers=admin).json()) == 1


def test_unknown_status_is_rejected(client, citizen, admin):
    req = create_request(client, citizen)
    r = client.put(f"/api/requests/{req['id']}/status", headers=admin, json={"status": "inventado"})
    assert r.status_code == 422


def test_cannot_move_to_assigned_without_official(client, citizen, admin):
    req = create_request(client, citizen)
    client.put(f"/api/requests/{req['id']}/status", headers=admin, json={"status": "in_review"})
    r = client.put(f"/api/requests/{req['id']}/status", headers=admin, json={"status": "assigned"})
    assert r.status_code == 422 and "funcionario" in r.json()["detail"]


def test_full_lifecycle_records_every_change(client, citizen, admin, official):
    rid = create_request(client, citizen)["id"]
    assert client.put(f"/api/requests/{rid}/status", headers=admin, json={"status": "in_review"}).status_code == 200
    r = client.put(f"/api/requests/{rid}/assign", headers=admin, json={"official_id": 2})
    assert r.status_code == 200 and r.json()["status"]["code"] == "assigned"
    assert r.json()["official"]["full_name"] == "Juan Pérez"
    r = client.put(f"/api/requests/{rid}/status", headers=official,
                   json={"status": "in_progress", "observation": "Se inició la validación."})
    assert r.status_code == 200
    assert client.put(f"/api/requests/{rid}/status", headers=official, json={"status": "resolved"}).status_code == 200
    assert client.put(f"/api/requests/{rid}/status", headers=admin, json={"status": "closed"}).status_code == 200

    history = client.get(f"/api/requests/{rid}/history", headers=citizen).json()
    assert [h["action"] for h in history] == ["created", "status_change", "assignment",
                                              "status_change", "status_change", "status_change"]
    # el funcionario solo aparece en la asignación, como en el ejemplo del PDF
    assert [bool(h["assigned_official"]) for h in history] == [False, False, True, False, False, False]
    steps = [(h["previous_status"] and h["previous_status"]["code"], h["new_status"]["code"]) for h in history]
    assert steps == [(None, "registered"), ("registered", "in_review"), ("in_review", "assigned"),
                     ("assigned", "in_progress"), ("in_progress", "resolved"), ("resolved", "closed")]
    assert history[3]["observation"] == "Se inició la validación."
    assert history[3]["changed_by"]["role"]["code"] == "official"
    assert history[2]["assigned_official"]["full_name"] == "Juan Pérez"


def test_official_only_sees_and_updates_assigned_requests(client, citizen, admin, official, other_official):
    rid = create_request(client, citizen)["id"]
    client.put(f"/api/requests/{rid}/status", headers=admin, json={"status": "in_review"})
    client.put(f"/api/requests/{rid}/assign", headers=admin, json={"official_id": 2})
    assert client.get("/api/requests", headers=official).json()["total"] == 1
    assert client.get("/api/requests", headers=other_official).json()["total"] == 0
    r = client.put(f"/api/requests/{rid}/status", headers=other_official, json={"status": "in_progress"})
    assert r.status_code == 404


def test_official_cannot_close_or_assign(client, citizen, admin, official):
    rid = create_request(client, citizen)["id"]
    client.put(f"/api/requests/{rid}/status", headers=admin, json={"status": "in_review"})
    client.put(f"/api/requests/{rid}/assign", headers=admin, json={"official_id": 2})
    client.put(f"/api/requests/{rid}/status", headers=official, json={"status": "in_progress"})
    client.put(f"/api/requests/{rid}/status", headers=official, json={"status": "resolved"})
    assert client.put(f"/api/requests/{rid}/status", headers=official, json={"status": "closed"}).status_code == 403
    assert client.put(f"/api/requests/{rid}/assign", headers=official, json={"official_id": 3}).status_code == 403


def test_citizen_cannot_change_status(client, citizen):
    rid = create_request(client, citizen)["id"]
    assert client.put(f"/api/requests/{rid}/status", headers=citizen, json={"status": "in_review"}).status_code == 403


def test_assign_rules(client, citizen, admin):
    rid = create_request(client, citizen)["id"]
    # todavía Registrada: primero debe revisarse
    assert client.put(f"/api/requests/{rid}/assign", headers=admin, json={"official_id": 2}).status_code == 422
    client.put(f"/api/requests/{rid}/status", headers=admin, json={"status": "in_review"})
    # un ciudadano no es funcionario
    assert client.put(f"/api/requests/{rid}/assign", headers=admin, json={"official_id": 4}).status_code == 422
    assert client.put(f"/api/requests/{rid}/assign", headers=admin, json={"official_id": 2}).status_code == 200
    # reasignar deja el estado igual pero queda en el historial
    r = client.put(f"/api/requests/{rid}/assign", headers=admin, json={"official_id": 3})
    assert r.status_code == 200 and r.json()["status"]["code"] == "assigned"
    last = client.get(f"/api/requests/{rid}/history", headers=admin).json()[-1]
    assert last["assigned_official"]["full_name"] == "María Gómez"


def test_admin_filters_and_search(client, citizen, admin):
    a = create_request(client, citizen, category="queja")
    create_request(client, citizen, category="reclamo")
    client.put(f"/api/requests/{a['id']}/status", headers=admin, json={"status": "in_review"})
    assert client.get("/api/requests?category=queja", headers=admin).json()["total"] == 1
    assert client.get("/api/requests?status=in_review", headers=admin).json()["total"] == 1
    assert client.get(f"/api/requests?number={a['number']}", headers=admin).json()["items"][0]["id"] == a["id"]
    assert client.get("/api/requests?number=abc", headers=admin).json()["total"] == 0


def test_users_endpoint_is_admin_only_and_masks_documents(client, admin, citizen):
    assert client.get("/api/users", headers=citizen).status_code == 403
    users = client.get("/api/users?role=official", headers=admin).json()
    assert [u["full_name"] for u in users] == ["Juan Pérez", "María Gómez"]
    assert users[0]["document_masked"].startswith("******") and "password_hash" not in users[0]


def test_stats_are_scoped(client, citizen, other_citizen, admin):
    create_request(client, citizen)
    assert client.get("/api/stats", headers=citizen).json()["total"] == 1
    assert client.get("/api/stats", headers=other_citizen).json()["total"] == 0
    assert client.get("/api/stats", headers=admin).json()["unassigned"] == 1


def test_transitions_endpoint_lists_only_allowed_targets(client, citizen, admin):
    rid = create_request(client, citizen)["id"]
    assert [s["code"] for s in client.get(f"/api/requests/{rid}/transitions", headers=admin).json()] == ["in_review"]
    assert client.get(f"/api/requests/{rid}/transitions", headers=citizen).json() == []
    client.put(f"/api/requests/{rid}/status", headers=admin, json={"status": "in_review"})
    # "Asignada" requiere funcionario: no se ofrece hasta que se asigne uno
    assert client.get(f"/api/requests/{rid}/transitions", headers=admin).json() == []


def _assigned_to_juan(client, citizen, admin):
    rid = create_request(client, citizen)["id"]
    client.put(f"/api/requests/{rid}/status", headers=admin, json={"status": "in_review"})
    client.put(f"/api/requests/{rid}/assign", headers=admin, json={"official_id": 2})
    return rid


def test_official_adds_observation_without_changing_status(client, citizen, admin, official):
    rid = _assigned_to_juan(client, citizen, admin)
    r = client.post(f"/api/requests/{rid}/observations", headers=official,
                    json={"observation": "  Se llamó al ciudadano; visita programada.  "})
    assert r.status_code == 201
    entry = r.json()
    assert entry["action"] == "observation"
    assert entry["previous_status"]["code"] == entry["new_status"]["code"] == "assigned"
    assert entry["observation"] == "Se llamó al ciudadano; visita programada."
    assert client.get(f"/api/requests/{rid}", headers=official).json()["status"]["code"] == "assigned"
    assert client.get(f"/api/requests/{rid}/history", headers=citizen).json()[-1]["action"] == "observation"


def test_observation_permissions_and_rules(client, citizen, admin, official, other_official):
    rid = _assigned_to_juan(client, citizen, admin)
    body = {"observation": "Revisión en curso."}
    assert client.post(f"/api/requests/{rid}/observations", headers=citizen, json=body).status_code == 403
    assert client.post(f"/api/requests/{rid}/observations", headers=other_official, json=body).status_code == 404
    assert client.post(f"/api/requests/{rid}/observations", headers=admin, json=body).status_code == 201
    assert client.post(f"/api/requests/{rid}/observations", headers=official, json={"observation": " "}).status_code == 422
    # una solicitud cerrada ya no admite observaciones
    for code, who in (("in_progress", official), ("resolved", official), ("closed", admin)):
        client.put(f"/api/requests/{rid}/status", headers=who, json={"status": code})
    r = client.post(f"/api/requests/{rid}/observations", headers=admin, json=body)
    assert r.status_code == 422 and "cerrada" in r.json()["detail"]
