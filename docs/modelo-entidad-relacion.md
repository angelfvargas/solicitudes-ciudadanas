# Modelo entidad-relación

El diagrama se dibuja solo en GitHub (Mermaid). El SQL completo está en
[`database/schema.sql`](../database/schema.sql).

```mermaid
erDiagram
    roles ||--o{ users : "tiene"
    users ||--o{ requests : "registra (citizen_id)"
    users |o--o{ requests : "atiende (official_id)"
    categories ||--o{ requests : "clasifica"
    request_statuses ||--o{ requests : "estado actual"
    requests ||--o{ request_status_history : "tiene"
    request_statuses ||--o{ request_status_history : "anterior / nuevo"
    users ||--o{ request_status_history : "hizo el cambio"
    users |o--o{ request_status_history : "funcionario en ese momento"
    request_statuses ||--o{ status_transitions : "desde / hacia"
    roles ||--o{ status_transitions : "puede ejecutar"

    roles {
        int id PK
        varchar code UK "citizen | official | admin"
        varchar name
    }
    users {
        int id PK
        int role_id FK
        varchar first_name
        varchar last_name
        varchar document_type "CHECK: CC, CE, TI, PA"
        varchar document_number UK
        varchar email UK "minúsculas"
        varchar password_hash "bcrypt"
        bool is_active
        timestamptz created_at
    }
    categories {
        int id PK
        varchar code UK
        varchar name UK
        bool is_active
    }
    request_statuses {
        int id PK
        varchar code UK
        varchar name UK
        int sort_order
        bool is_initial
        bool is_final
        bool requires_official
        bool allows_assignment
    }
    status_transitions {
        int id PK
        int from_status_id FK
        int to_status_id FK
        int role_id FK
    }
    requests {
        int id PK "el número 000123 se deriva de aquí"
        int citizen_id FK
        int category_id FK
        int status_id FK
        int official_id FK "NULL = sin asignar"
        varchar subject "CHECK length >= 5"
        text description "CHECK length >= 20"
        varchar priority "CHECK baja/media/alta, NULL"
        text ai_summary
        timestamptz created_at
        timestamptz updated_at
    }
    request_status_history {
        int id PK
        int request_id FK
        int previous_status_id FK "NULL en el registro inicial"
        int new_status_id FK
        int changed_by_id FK
        int assigned_official_id FK
        text observation
        timestamptz changed_at
    }
```

## Decisiones

| Decisión | Por qué |
|---|---|
| Roles, categorías y estados son **tablas**, no textos sueltos ni `ENUM` | Se agregan o renombran sin tocar código. Las llaves foráneas impiden guardar una categoría o un estado que no existe. |
| Tabla `status_transitions` | El flujo de estados es un dato. Todo lo que no está en la tabla se rechaza, y agregar un paso nuevo es insertar una fila (principio Abierto/Cerrado). |
| El número de solicitud **no se guarda** | Se deriva del `id` (`LPAD(id, 6, '0')`). Guardarlo aparte duplicaría información que puede desincronizarse, como pide evitar la prueba. |
| `requests.status_id` sí se guarda aunque el historial lo tenga | Es el estado *actual*. Sin él, filtrar por estado exigiría buscar el último registro del historial de cada solicitud. Se escribe en la misma transacción que el historial, así que no se desincroniza. |
| `history.assigned_official_id` | No es redundante: guarda quién estaba asignado *en ese momento*. Si la solicitud se reasigna, el historial conserva lo que pasó. |
| `UNIQUE` en correo y documento | Es la última barrera contra duplicados, aunque el servicio ya lo valide (evita el caso de dos registros simultáneos). |
| `CHECK` en longitudes, prioridad y tipo de documento | La base de datos no confía ni siquiera en el backend. |
| Trigger que rechaza `UPDATE`/`DELETE` en el historial | "El historial no debe poder eliminarse": ni desde la interfaz (no hay endpoint) ni saltándose la API. |

## Índices

- `requests(citizen_id)`, `requests(official_id)`: consultas "mis solicitudes" y "asignadas a mí".
- `requests(status_id)`, `requests(category_id)`: filtros del administrador.
- `requests(created_at)`: orden por fecha y "las 10 más recientes".
- `request_status_history(request_id, changed_at)`: historial de una solicitud, ya ordenado.
- Los `UNIQUE` (correo, documento, códigos) crean su propio índice: el login busca por correo.
