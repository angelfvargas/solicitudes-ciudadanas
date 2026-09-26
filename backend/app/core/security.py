"""Hash de contraseñas (bcrypt) y tokens de acceso (JWT)."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.errors import AuthenticationError


class PasswordHasher:
    """bcrypt: hash lento y con sal propia por contraseña. Nunca se guarda la contraseña."""

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


class TokenService:
    def __init__(self) -> None:
        settings = get_settings()
        self._secret = settings.jwt_secret
        self._algorithm = settings.jwt_algorithm
        self._expire = timedelta(minutes=settings.jwt_expire_minutes)

    def create(self, user_id: int, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + self._expire}
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_user_id(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return int(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError):
            raise AuthenticationError("Sesión inválida o expirada. Inicie sesión de nuevo.") from None
