"""Punto de entrada. Arma la aplicación monolítica: API REST en /api y, si existe el
build de React, la interfaz web en /. Un solo proceso, un solo despliegue."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.controllers import (ai_controller, auth_controller, catalog_controller, request_controller,
                             user_controller)
from app.core.config import get_settings
from app.core.errors import DomainError


def register_error_handlers(app: FastAPI) -> None:
    """Manejo de errores centralizado: todas las respuestas de error tienen la misma forma
    {"detail": "...", "code": "..."} y nunca exponen trazas internas."""

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code,
                            content={"detail": exc.message, "code": exc.code})

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = []
        for err in exc.errors():
            field = ".".join(str(p) for p in err["loc"] if p not in ("body", "query", "path"))
            message = str(err["msg"]).removeprefix("Value error, ")
            fields.append({"field": field, "message": message})
        return JSONResponse(status_code=422, content={
            "detail": "Hay datos inválidos en la solicitud.", "code": "validation_error",
            "fields": fields})

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        return JSONResponse(status_code=500, content={
            "detail": "Ocurrió un error inesperado. Intente de nuevo.", "code": "internal_error"})


def mount_frontend(app: FastAPI, dist: Path) -> None:
    if not (dist / "index.html").is_file():
        return
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        # Rutas de React (/solicitudes/5, /login...) devuelven index.html; React Router decide.
        file = (dist / path).resolve()
        if path and file.is_file() and dist.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(dist / "index.html")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Vennex — Seguimiento de solicitudes ciudadanas",
        version="1.0.0",
        docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None,
    )
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["*"], allow_headers=["*"])
    register_error_handlers(app)
    for controller in (auth_controller, request_controller, user_controller,
                       catalog_controller, ai_controller):
        app.include_router(controller.router, prefix="/api")

    @app.get("/api/health", tags=["Sistema"])
    def health():
        return {"status": "ok"}

    mount_frontend(app, Path(settings.frontend_dist))
    return app


app = create_app()
