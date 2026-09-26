# Imagen única del monolito: primero se compila React y luego Python sirve la API y la web.

# --- Etapa 1: compilar el frontend ---
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Etapa 2: backend + frontend compilado ---
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend /app/frontend/dist /app/frontend/dist
# No correr como root dentro del contenedor.
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
# Crea tablas y datos iniciales (idempotente) y arranca el servidor.
CMD ["sh", "-c", "python -m app.db.init_db ${SEED_DEMO:+--demo} && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
