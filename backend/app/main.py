"""Punto de entrada. Arma la aplicación monolítica: API REST en /api y, si existe el
build de React, la interfaz web en /. Un solo proceso, un solo despliegue."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

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

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        messages = {404: ("Ruta no encontrada.", "not_found"), 405: ("Método no permitido.", "method_not_allowed")}
        detail, code = messages.get(exc.status_code, (str(exc.detail), "http_error"))
        return JSONResponse(status_code=exc.status_code, content={"detail": detail, "code": code})

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = []
        for err in exc.errors():
            field = ".".join(str(p) for p in err["loc"] if p not in ("body", "query", "path"))
            fields.append({"field": field, "message": validation_message(err)})
        return JSONResponse(status_code=422, content={
            "detail": "Hay datos inválidos en la solicitud.", "code": "validation_error",
            "fields": fields})

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        return JSONResponse(status_code=500, content={
            "detail": "Ocurrió un error inesperado. Intente de nuevo.", "code": "internal_error"})


def validation_message(err: dict) -> str:
    """Traduce los mensajes de validación de Pydantic (vienen en inglés) al español."""
    kind, ctx, msg = err["type"], err.get("ctx", {}), str(err["msg"])
    if kind == "value_error":
        if "email" in msg.lower():
            return "Correo electrónico inválido."
        return msg.removeprefix("Value error, ")  # mensajes propios, ya en español
    templates = {
        "missing": "Este campo es obligatorio.",
        "string_too_short": "Debe tener al menos {min_length} caracteres.",
        "string_too_long": "Debe tener como máximo {max_length} caracteres.",
        "string_type": "Debe ser texto.",
        "int_parsing": "Debe ser un número entero.",
        "int_type": "Debe ser un número entero.",
        "greater_than": "Debe ser mayor que {gt}.",
        "greater_than_equal": "Debe ser mayor o igual a {ge}.",
        "less_than_equal": "Debe ser menor o igual a {le}.",
        "literal_error": "Valor no permitido. Opciones: {expected}.",
        "json_invalid": "El cuerpo de la petición no es un JSON válido.",
        "model_attributes_type": "Formato inválido: se esperaba un objeto JSON.",
    }
    if kind in templates:
        return templates[kind].format(**{k: str(v).replace(" or ", " o ") for k, v in ctx.items()})
    return msg


def mount_frontend(app: FastAPI, dist: Path) -> None:
    if not (dist / "index.html").is_file():
        return
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path == "api" or path.startswith("api/"):
            # Una ruta de API que no existe es un 404 en JSON, no la página web.
            return JSONResponse(status_code=404, content={"detail": "Ruta no encontrada.", "code": "not_found"})
        # Rutas de React (/solicitudes/5, /login...) devuelven index.html; React Router decide.
        file = (dist / path).resolve()
        if path and file.is_file() and dist.resolve() in file.parents:
            return FileResponse(file)
        # index.html no se guarda en caché: así el navegador siempre toma la versión nueva de la app
        # (los archivos de /assets llevan un hash en el nombre y sí se pueden guardar).
        return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache"})


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
