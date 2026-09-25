VALID = {"first_name": "Pedro", "last_name": "Salas", "document_type": "CC",
         "document_number": "1234567890", "email": "Pedro@Example.com", "password": "Clave1234"}


def test_register_creates_citizen_without_exposing_hash(client):
    r = client.post("/api/auth/register", json=VALID)
    assert r.status_code == 201
    body = r.json()
    assert body["role"]["code"] == "citizen"
    assert body["email"] == "pedro@example.com"  # normalizado
    assert "password" not in str(body) and "hash" not in str(body)


def test_register_rejects_duplicate_email_and_document(client):
    assert client.post("/api/auth/register", json=VALID).status_code == 201
    same_email = {**VALID, "document_number": "9999999999", "email": "PEDRO@example.com"}
    r = client.post("/api/auth/register", json=same_email)
    assert r.status_code == 409 and "correo" in r.json()["detail"]
    same_doc = {**VALID, "email": "otro@example.com"}
    r = client.post("/api/auth/register", json=same_doc)
    assert r.status_code == 409 and "documento" in r.json()["detail"]


def test_register_validates_fields(client):
    bad = {**VALID, "email": "no-es-correo", "password": "corta", "document_number": "12AB"}
    r = client.post("/api/auth/register", json=bad)
    assert r.status_code == 422
    fields = {f["field"] for f in r.json()["fields"]}
    assert {"email", "password"} <= fields


def test_password_needs_letters_and_numbers(client):
    r = client.post("/api/auth/register", json={**VALID, "password": "solotexto"})
    assert r.status_code == 422


def test_register_cannot_choose_role(client):
    r = client.post("/api/auth/register", json={**VALID, "role": "admin"})
    assert r.status_code == 201 and r.json()["role"]["code"] == "citizen"


def test_login_error_does_not_reveal_which_field_failed(client):
    wrong_password = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "x"})
    unknown_user = client.post("/api/auth/login", json={"email": "nadie@example.com", "password": "x"})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json()["detail"] == unknown_user.json()["detail"]


def test_protected_endpoints_require_token(client):
    assert client.get("/api/requests").status_code == 401
    assert client.get("/api/requests", headers={"Authorization": "Bearer basura"}).status_code == 401
