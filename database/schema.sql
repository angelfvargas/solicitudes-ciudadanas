-- Esquema de la base de datos (PostgreSQL). Generado a partir de los modelos SQLAlchemy
-- (backend/app/models), que son la fuente de verdad. La app lo crea sola con:
--   python -m app.db.init_db

CREATE TABLE categories (
	id SERIAL NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	UNIQUE (name)
);


CREATE TABLE request_statuses (
	id SERIAL NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	is_initial BOOLEAN NOT NULL, 
	is_final BOOLEAN NOT NULL, 
	requires_official BOOLEAN NOT NULL, 
	allows_assignment BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	UNIQUE (name)
);


CREATE TABLE roles (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);


CREATE TABLE status_transitions (
	id SERIAL NOT NULL, 
	from_status_id INTEGER NOT NULL, 
	to_status_id INTEGER NOT NULL, 
	role_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (from_status_id, to_status_id, role_id), 
	FOREIGN KEY(from_status_id) REFERENCES request_statuses (id), 
	FOREIGN KEY(to_status_id) REFERENCES request_statuses (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id)
);


CREATE TABLE users (
	id SERIAL NOT NULL, 
	role_id INTEGER NOT NULL, 
	first_name VARCHAR(60) NOT NULL, 
	last_name VARCHAR(60) NOT NULL, 
	document_type VARCHAR(2) NOT NULL, 
	document_number VARCHAR(15) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_users_document_type CHECK (document_type IN ('CC', 'CE', 'TI', 'PA')), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	UNIQUE (document_number), 
	UNIQUE (email)
);

CREATE INDEX ix_users_role_id ON users (role_id);

CREATE TABLE requests (
	id SERIAL NOT NULL, 
	citizen_id INTEGER NOT NULL, 
	category_id INTEGER NOT NULL, 
	status_id INTEGER NOT NULL, 
	official_id INTEGER, 
	subject VARCHAR(150) NOT NULL, 
	description TEXT NOT NULL, 
	priority VARCHAR(10), 
	ai_summary TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_requests_subject_len CHECK (length(subject) >= 5), 
	CONSTRAINT ck_requests_description_len CHECK (length(description) >= 20), 
	CONSTRAINT ck_requests_priority CHECK (priority IS NULL OR priority IN ('baja', 'media', 'alta')), 
	FOREIGN KEY(citizen_id) REFERENCES users (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id), 
	FOREIGN KEY(status_id) REFERENCES request_statuses (id), 
	FOREIGN KEY(official_id) REFERENCES users (id)
);

CREATE INDEX ix_requests_category_id ON requests (category_id);
CREATE INDEX ix_requests_citizen_id ON requests (citizen_id);
CREATE INDEX ix_requests_created_at ON requests (created_at);
CREATE INDEX ix_requests_official_id ON requests (official_id);
CREATE INDEX ix_requests_status_id ON requests (status_id);

CREATE TABLE request_status_history (
	id SERIAL NOT NULL, 
	request_id INTEGER NOT NULL, 
	previous_status_id INTEGER, 
	new_status_id INTEGER NOT NULL, 
	changed_by_id INTEGER NOT NULL, 
	action VARCHAR(20) NOT NULL, 
	assigned_official_id INTEGER, 
	observation TEXT, 
	changed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_history_action CHECK (action IN ('created', 'status_change', 'assignment', 'observation')), 
	CONSTRAINT ck_history_previous CHECK ((action = 'created') = (previous_status_id IS NULL)), 
	CONSTRAINT ck_history_official CHECK ((action = 'assignment') = (assigned_official_id IS NOT NULL)), 
	FOREIGN KEY(request_id) REFERENCES requests (id), 
	FOREIGN KEY(previous_status_id) REFERENCES request_statuses (id), 
	FOREIGN KEY(new_status_id) REFERENCES request_statuses (id), 
	FOREIGN KEY(changed_by_id) REFERENCES users (id), 
	FOREIGN KEY(assigned_official_id) REFERENCES users (id)
);

CREATE INDEX ix_history_request_changed ON request_status_history (request_id, changed_at);

-- El historial es inmutable: la base de datos rechaza UPDATE y DELETE.
CREATE OR REPLACE FUNCTION forbid_history_change() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'El historial de solicitudes es inmutable (operación % rechazada)', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_history_immutable ON request_status_history;
CREATE TRIGGER trg_history_immutable
    BEFORE UPDATE OR DELETE ON request_status_history
    FOR EACH ROW EXECUTE FUNCTION forbid_history_change();
