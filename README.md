# Seguimiento de solicitudes ciudadanas

Prototipo funcional de un sistema web donde los ciudadanos registran solicitudes (PQRS) ante
una entidad pública, y los funcionarios y administradores les hacen seguimiento. Cada cambio
de estado queda en un historial que no se puede borrar.

Es la prueba técnica para el cargo de Practicante de Desarrollo de Software en Vennex Group.

| Rol | Qué puede hacer |
|---|---|
| **Ciudadano** | Registrarse, iniciar sesión, crear solicitudes (con sugerencia opcional de IA) y ver sus solicitudes, con su detalle e historial. |
| **Funcionario** | Ver las solicitudes asignadas a él, cambiarles el estado con observación y ver su historial. |
| **Administrador** | Ver todas las solicitudes con filtros y búsqueda, asignarlas y reasignarlas, cambiar estados, ver usuarios y el historial. |

---

## 1. Tecnologías

| Capa | Tecnología | Por qué |
|---|---|---|
| Backend | **Python 3.11 + FastAPI** | Lo recomienda la prueba. Valida los datos con Pydantic y genera la documentación OpenAPI/Swagger sola. |
| ORM | **SQLAlchemy 2** | Modelos tipados y consultas parametrizadas, que protegen contra inyección SQL. |
| Base de datos | **PostgreSQL 16** | Es relacional, tiene `CHECK`, llaves foráneas y triggers (se usan para que el historial sea inmutable). |
| Frontend | **React 19 + TypeScript (modo estricto) + Vite** | Lo recomienda la prueba. El tipado estricto detecta errores al compilar. |
| Seguridad | **bcrypt** (contraseñas) + **JWT** (sesión) | Estándar, sin estado en el servidor. |
| IA (opcional) | **Google Gemini** (`gemini-2.5-flash`) por su API REST | Tiene capa gratuita y admite respuesta en JSON con esquema. |
| Pruebas | **pytest** | 33 pruebas de API sobre SQLite en memoria (rápidas, sin servidor). |

## 2. Arquitectura: monolito en capas, patrón MVC

Es **un solo servicio desplegable**. FastAPI expone la API en `/api` y, además, sirve la
interfaz de React ya compilada en `/`. Se arranca un proceso y se abre una URL.

```
Navegador ──► React (VISTA) ──fetch /api──► Controladores ──► Servicios ──► Repositorios ──► PostgreSQL
                                           (CONTROLADOR)     (reglas de     (persistencia)     (MODELO:
                                                              negocio)                          tablas)
```

```
backend/app/
├── main.py            Arma la app: rutas, manejo de errores centralizado y el frontend (monolito)
├── dependencies.py    Composición: crea cada servicio con sus dependencias (inyección)
├── core/              Configuración (.env), errores de dominio y seguridad (bcrypt, JWT)
├── models/            MODELO: tablas SQLAlchemy
├── schemas/           DTOs de entrada/salida: validación y qué datos salen
├── controllers/       CONTROLADOR: endpoints HTTP delgados, sin reglas de negocio
├── services/          Reglas de negocio
│   ├── auth_service.py      registro y login
│   ├── access_policy.py     quién puede VER qué solicitud
│   ├── workflow.py          qué cambios de estado son válidos
│   ├── request_service.py   casos de uso de la solicitud
│   ├── stats_service.py     tablero
│   └── ai/                  clasificación con IA, separada del proveedor
├── repositories/      Único lugar con consultas a la base de datos
└── db/                Sesión, creación de tablas y datos iniciales
frontend/src/
├── api/               Cliente HTTP único y funciones por recurso
├── auth/              Sesión (contexto) y protección de rutas por rol
├── pages/             VISTA: pantallas
├── components/        Componentes reutilizables
└── utils/             Validaciones, formatos y carga de datos
database/              schema.sql y las consultas de la prueba SQL
docs/                  Modelo entidad-relación y prueba de lógica
```

### Principios SOLID aplicados

| Principio | Dónde se ve |
|---|---|
| **S — Responsabilidad única** | Cada capa hace una cosa: el controlador traduce HTTP, el servicio aplica reglas y el repositorio consulta. Dentro de los servicios, `RequestAccessPolicy` solo decide *quién ve qué*, `StatusWorkflow` solo decide *qué transición es válida* y `RequestClassifier` solo habla de IA. |
| **O — Abierto/Cerrado** | Las transiciones de estado, los estados y las categorías son **datos** (`status_transitions`, `request_statuses`, `categories`). Agregar un estado o un permiso es insertar filas; `StatusWorkflow` no se modifica. En la IA, se agrega un proveedor nuevo sin tocar el clasificador. |
| **L — Sustitución de Liskov** | Cualquier implementación de `LLMProvider` (Gemini o la falsa de las pruebas) sirve al clasificador sin que este cambie su comportamiento. |
| **I — Segregación de interfaces** | `LLMProvider` exige un solo método (`generate_json`). Los repositorios están separados por agregado (usuarios, solicitudes, historial, catálogos), en vez de un "DAO" gigante. |
| **D — Inversión de dependencias** | Los servicios reciben sus dependencias por el constructor y no las crean. `dependencies.py` es el único que decide las implementaciones concretas, y las pruebas las reemplazan (por ejemplo, la IA falsa). |

## 3. Requisitos

- Python 3.11 o superior
- Node.js 20 o superior (con npm)
- PostgreSQL 14 o superior. Si no lo tiene instalado, el proyecto incluye uno de desarrollo que
  no requiere instalar nada (ver paso 5.b).

## 4. Instalación

```bash
git clone <url-del-repositorio> vennex-solicitudes
cd vennex-solicitudes

# Backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r backend/requirements-dev.txt

# Frontend
cd frontend && npm install && cd ..
```

## 5. Configuración

### a) Variables de entorno

```bash
cp backend/.env.example backend/.env
```

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | sí | URL de PostgreSQL, p. ej. `postgresql+psycopg://postgres:postgres@localhost:5432/vennex` |
| `JWT_SECRET` | sí | Secreto para firmar los tokens, **mínimo 32 caracteres** (la app no arranca con uno más corto). Genérelo con `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_EXPIRE_MINUTES` | no | Duración de la sesión (60 por defecto) |
| `GEMINI_API_KEY` | no | Llave de [Google AI Studio](https://aistudio.google.com/apikey). Sin ella, la app funciona igual y la categoría se elige a mano. |
| `GEMINI_MODEL` | no | `gemini-2.5-flash` por defecto |

El archivo `.env` está en `.gitignore`. **Ninguna clave está en el código.**

### b) Base de datos

**Opción 1, con PostgreSQL propio:**
```bash
createdb vennex          # o: CREATE DATABASE vennex;
```

**Opción 2, sin instalar PostgreSQL** (solo desarrollo; usa el paquete `pgserver`):
```bash
python scripts/dev_postgres.py       # arranca PostgreSQL y muestra la DATABASE_URL para el .env
```

**Crear tablas y datos** (en ambos casos):
```bash
cd backend
python -m app.db.init_db --demo      # --demo agrega 40 solicitudes de ejemplo con historial
```
Esto crea las tablas, el trigger que protege el historial, los catálogos y los usuarios de
prueba. Se puede correr varias veces sin duplicar nada.

## 6. Ejecución

### Modo monolito (un solo proceso)
```bash
cd frontend && npm run build && cd ..
cd backend && uvicorn app.main:app --port 8000
```
Abrir **http://localhost:8000**. La documentación de la API (Swagger) está en
**http://localhost:8000/api/docs**.

### Modo desarrollo (con recarga automática)
```bash
# terminal 1
cd backend && uvicorn app.main:app --reload --port 8000
# terminal 2
cd frontend && npm run dev
```
Abrir **http://localhost:5173**. Vite reenvía `/api` al backend.

### Pruebas
```bash
cd backend && pytest
```
33 pruebas: registro y duplicados, login, permisos por rol, la situación de cambiar el id en
la URL, la transición Registrada → Cerrada, el ciclo de vida completo con su historial,
asignación y reasignación, filtros, y la IA (respuestas inválidas, servicio caído y datos
personales que no deben salir).

## 7. Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@example.com` | `Admin12345` |
| Funcionario | `juan.perez@example.com` | `Funcionario123` |
| Funcionario | `maria.gomez@example.com` | `Funcionario123` |
| Ciudadano | `ana.torres@example.org` | `Ciudadano123` |
| Ciudadano | `carlos.ruiz@example.org` | `Ciudadano123` |

También puede registrar un ciudadano nuevo desde la pantalla de registro.

## 8. API REST

Todas las rutas empiezan por `/api`. Salvo registro, login y catálogos, todas exigen
`Authorization: Bearer <token>`.

| Método | Ruta | Quién | Descripción |
|---|---|---|---|
| POST | `/auth/register` | público | Registro. Siempre crea un **ciudadano**: el rol no lo elige quien se registra. |
| POST | `/auth/login` | público | Devuelve el token JWT y el usuario |
| GET | `/auth/me` | autenticado | Usuario actual |
| GET | `/requests` | todos | Listado paginado, **limitado por rol**. Filtros: `status`, `category`, `number`, `page`, `size` |
| POST | `/requests` | ciudadano | Crea la solicitud (estado inicial + primer registro del historial) |
| GET | `/requests/{id}` | todos | Detalle. Da 404 si el usuario no tiene acceso a esa solicitud. |
| PUT | `/requests/{id}/status` | funcionario, admin | Cambia el estado con observación y valida el flujo |
| PUT | `/requests/{id}/assign` | admin | Asigna o reasigna funcionario |
| GET | `/requests/{id}/history` | todos | Historial en orden cronológico |
| GET | `/requests/{id}/transitions` | todos | Estados a los que el usuario puede mover la solicitud |
| GET | `/users` | admin | Usuarios (documento enmascarado); filtro `role` |
| GET | `/catalogs` | público | Categorías y estados |
| GET | `/stats` | todos | Cifras del tablero, dentro del alcance del usuario |
| POST | `/ai/classify` | ciudadano | Sugerencia de categoría, prioridad y resumen |

Todos los errores tienen la misma forma: `{"detail": "mensaje", "code": "..."}`. Los errores de
validación incluyen además `fields: [{field, message}]`, y el frontend los muestra junto a
cada campo.

## 9. Reglas de negocio y seguridad

- **Flujo de estados:** ver [docs/prueba-de-logica.md](docs/prueba-de-logica.md). La lista
  blanca de transiciones está en la tabla `status_transitions`; `Registrada → Cerrada` se
  rechaza con un 422 y un mensaje que explica qué sí se puede hacer.
- **Historial:** cada cambio de estado y cada asignación escribe un registro en la **misma
  transacción** que el cambio. No existe ningún endpoint para editarlo o borrarlo, y en
  PostgreSQL un trigger rechaza `UPDATE` y `DELETE`.
- **Acceso por pertenencia (no solo por rol):** un ciudadano solo ve sus solicitudes y un
  funcionario solo las asignadas. Si alguien cambia el id en la URL, recibe un **404**, no un
  403, para no confirmar que la solicitud existe (`RequestAccessPolicy`). Los listados y el
  tablero se filtran por alcance en el backend.
- **Contraseñas:** se guardan con bcrypt (hash lento y con sal). Nunca salen de la base de
  datos: ningún esquema de salida incluye el hash.
- **Login:** el mismo mensaje sirve para "correo inexistente" y "contraseña incorrecta", y el
  tiempo de respuesta es similar en ambos casos, para no revelar qué correos están
  registrados.
- **JWT:** expira en 60 minutos. En cada petición se vuelve a leer el usuario, así que si lo
  desactivan o le cambian el rol, el cambio aplica de inmediato.
- **Validaciones en los dos lados:** el frontend responde de inmediato y el backend
  (Pydantic, servicios y `CHECK` en la base de datos) no confía en él.
- **Datos mínimos:** la lista de usuarios muestra el documento enmascarado (`******0004`) y el
  detalle de una solicitud muestra del ciudadano solo el nombre.
- **Errores:** un manejador central convierte cualquier excepción en un JSON sin trazas
  internas.

## 10. Funcionalidades opcionales implementadas

| Funcionalidad | Por qué es útil |
|---|---|
| **Clasificación con IA** (alternativa A) | El ciudadano no siempre sabe si su caso es queja, reclamo o petición. Una mala clasificación retrasa la atención; la prioridad sugerida ayuda a atender primero lo urgente. |
| **Tablero con estadísticas** | Muestra de un vistazo cuántas solicitudes hay por estado y cuántas siguen **sin funcionario**, que son las que están represadas. |
| **Pruebas automatizadas** (33) | Protegen las reglas críticas (permisos, flujo, historial) cuando otro desarrollador cambie el código. |
| **Paginación y filtros en la URL** | Los listados no cargan todo de golpe, y un filtro se puede compartir o recargar. |
| **Swagger / OpenAPI** | Documentación viva de la API en `/api/docs`. |
| **Manejo de errores centralizado** | Todos los errores tienen el mismo formato, y el frontend los muestra por campo. |
| **Historial inmutable en la base de datos** | Auditoría confiable aunque alguien se salte la API. |

## 11. Funcionalidad de IA

1. **Modelo:** Google Gemini `gemini-2.5-flash` (configurable con `GEMINI_MODEL`).
2. **Comunicación:** el backend llama a la API REST de Gemini con `httpx`, con un tiempo
   límite de 20 s. El navegador nunca habla con Gemini ni ve la llave. La llave va en una
   cabecera HTTP, no en la URL, para que no quede en los logs.
3. **Credenciales:** solo en la variable de entorno `GEMINI_API_KEY`, nunca en el código.
4. **Si falla:** si no hay llave, se agota el tiempo o el servicio se cae, se responde **503**
   con un mensaje, y el formulario sigue funcionando para clasificar a mano. La IA nunca
   bloquea el registro.
5. **Validación de la respuesta:** se pide JSON con esquema (`responseSchema`) y aun así se
   revisa: la categoría debe existir y estar activa, la prioridad debe ser baja, media o
   alta, y el resumen debe tener entre 10 y 500 caracteres. Si algo falla, se descarta y se
   pide clasificar a mano.
6. **Revisión del usuario:** la sugerencia solo **precarga** el formulario. El ciudadano ve
   un aviso, puede cambiar la categoría, la prioridad y el resumen, o descartarla. Nada se
   guarda hasta que él envía.
7. **Datos enviados al modelo:** solo el asunto y la descripción. Antes de enviarlos se
   borran correos y números largos (cédulas, teléfonos). El nombre, el documento y el correo
   del usuario nunca se envían.
8. **Prompt:** incluye las definiciones de PQRS de la Ley 1755 de 2015 para que el modelo no
   adivine, criterios explícitos de prioridad y una instrucción de tratar el texto del
   ciudadano como **dato y no como orden**, para mitigar la inyección de instrucciones.
   Además, el texto va entre etiquetas. La temperatura es 0.1, para que las respuestas sean
   consistentes.
9. **Separación:** `RequestClassifier` (lógica de negocio) depende de la interfaz
   `LLMProvider`, no de Gemini. `GeminiProvider` es un detalle intercambiable.

**Limitaciones:** el modelo puede equivocarse en casos ambiguos (por eso la revisión humana).
No ve imágenes ni adjuntos. Depende de la cuota del servicio externo. El borrado de datos
personales es por patrones, así que un nombre escrito dentro de la descripción sí se envía.
La prioridad es una sugerencia inicial y no reemplaza el criterio del funcionario.

## 12. Decisiones técnicas relevantes

- **Asignar mueve a "Asignada".** Si la solicitud está "En revisión", asignarla la pasa a
  "Asignada" en la misma operación, como en el ejemplo de la prueba. Si ya estaba asignada o
  en proceso, es una **reasignación**: el estado no cambia, pero queda en el historial.
- **Un funcionario no puede cerrar.** Resuelve la solicitud y el administrador la cierra
  (control de calidad). Cambiarlo es insertar una fila en `status_transitions`.
- **Resuelta → En proceso (reabrir)** está permitido al administrador, por si la respuesta
  no fue suficiente.
- **"Asignada" exige funcionario.** Se modela con `requires_official` en el estado, no con un
  `if` en el código.
- **Número de solicitud derivado del id** (`000123`), para no guardar información duplicada.
- **Token en `sessionStorage`** (se borra al cerrar la pestaña). Con más tiempo usaría una
  cookie `HttpOnly` + `SameSite`, que el JavaScript no puede leer (mitiga el robo por XSS).
- **Pruebas sobre SQLite en memoria.** Son rápidas y no requieren servidor. Los modelos son
  portables; el trigger de inmutabilidad es exclusivo de PostgreSQL y se verificó aparte.
- **Sin Alembic.** Las tablas se crean con `create_all`, que basta para un prototipo. En
  producción, cada cambio de esquema debería ir como una migración versionada con Alembic.

## 13. Prueba de SQL

Las cuatro consultas están en [`database/queries.sql`](database/queries.sql), con
comentarios, y se probaron sobre los datos de ejemplo. Una aclaración: en la consulta 3,
"atendidas" se interpreta como *solicitudes que el funcionario llevó a Resuelta* (sale del
historial). Se deja comentada la variante "asignadas actualmente".

## 14. Qué cambiaría con 100.000 usuarios

- Varias instancias del backend detrás de un balanceador (el JWT no guarda estado en el
  servidor, así que escala horizontalmente) y un pool de conexiones a PostgreSQL (PgBouncer).
- Paginación por cursor (`WHERE id < último_id`) en vez de `OFFSET`, y búsqueda de texto con
  índices GIN / `pg_trgm`.
- Límite de intentos en el login y en la IA (rate limiting), y registro de auditoría de
  accesos.
- La clasificación con IA en una cola asíncrona, para no bloquear la petición.
- Réplicas de lectura para el tablero y los reportes.
