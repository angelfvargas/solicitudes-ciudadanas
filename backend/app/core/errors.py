"""Errores de dominio.

Los servicios lanzan estas excepciones sin saber nada de HTTP; un único manejador
(registrado en main.py) las traduce a respuestas JSON. Así el formato de error es
el mismo en toda la API y la lógica de negocio no depende del framework.
"""


class DomainError(Exception):
    status_code = 400
    code = "domain_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class AuthenticationError(DomainError):
    status_code = 401
    code = "unauthenticated"


class PermissionDeniedError(DomainError):
    status_code = 403
    code = "forbidden"


class BusinessRuleError(DomainError):
    """Una regla de negocio impide la operación (p. ej. una transición de estado inválida)."""
    status_code = 422
    code = "business_rule"


class AIUnavailableError(DomainError):
    status_code = 503
    code = "ai_unavailable"
