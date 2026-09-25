-- =====================================================================
-- Prueba adicional de SQL (sección 15). PostgreSQL.
-- Probadas contra los datos de ejemplo (python -m app.db.init_db --demo).
-- =====================================================================

-- Consulta 1 — Cantidad de solicitudes por estado.
-- Se parte de la tabla de estados con LEFT JOIN para que un estado sin
-- solicitudes aparezca con 0 en vez de desaparecer del resultado.
SELECT s.name        AS estado,
       COUNT(r.id)   AS cantidad
FROM request_statuses s
LEFT JOIN requests r ON r.status_id = s.id
GROUP BY s.id, s.name, s.sort_order
ORDER BY s.sort_order;


-- Consulta 2 — Las 10 solicitudes más recientes.
-- El número visible se deriva del id (no se guarda duplicado).
-- r.id como segundo criterio desempata dos solicitudes creadas en el mismo instante.
SELECT LPAD(r.id::text, 6, '0')              AS numero,
       r.created_at                          AS fecha,
       r.subject                             AS asunto,
       c.name                                AS categoria,
       s.name                                AS estado,
       u.first_name || ' ' || u.last_name    AS ciudadano
FROM requests r
JOIN categories       c ON c.id = r.category_id
JOIN request_statuses s ON s.id = r.status_id
JOIN users            u ON u.id = r.citizen_id
ORDER BY r.created_at DESC, r.id DESC
LIMIT 10;


-- Consulta 3 — Cantidad de solicitudes atendidas por cada funcionario.
-- Decisión: "atendida" = el funcionario la llevó a estado Resuelta (queda en el
-- historial, así que cuenta aunque luego la hayan reasignado o cerrado).
-- Se muestran también los funcionarios con 0 y, como dato extra, su carga actual.
SELECT u.first_name || ' ' || u.last_name                       AS funcionario,
       COUNT(DISTINCT h.request_id)                             AS atendidas,
       (SELECT COUNT(*) FROM requests r
         JOIN request_statuses rs ON rs.id = r.status_id
         WHERE r.official_id = u.id AND NOT rs.is_final
           AND rs.code <> 'resolved')                           AS en_curso_actualmente
FROM users u
JOIN roles ro ON ro.id = u.role_id AND ro.code = 'official'
LEFT JOIN request_status_history h
       ON h.changed_by_id = u.id
      AND h.new_status_id = (SELECT id FROM request_statuses WHERE code = 'resolved')
GROUP BY u.id, u.first_name, u.last_name
ORDER BY atendidas DESC, funcionario;

-- Variante más simple, si "atendidas" se entiende como "asignadas actualmente":
-- SELECT u.first_name || ' ' || u.last_name AS funcionario, COUNT(r.id) AS solicitudes
-- FROM users u JOIN roles ro ON ro.id = u.role_id AND ro.code = 'official'
-- LEFT JOIN requests r ON r.official_id = u.id
-- GROUP BY u.id, u.first_name, u.last_name ORDER BY solicitudes DESC;


-- Consulta 4 — Solicitudes que actualmente no tienen funcionario asignado.
SELECT LPAD(r.id::text, 6, '0') AS numero,
       r.created_at             AS fecha,
       r.subject                AS asunto,
       s.name                   AS estado
FROM requests r
JOIN request_statuses s ON s.id = r.status_id
WHERE r.official_id IS NULL
ORDER BY r.created_at;   -- las más antiguas primero: son las que llevan más tiempo esperando
