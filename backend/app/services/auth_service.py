from sqlalchemy.exc import IntegrityError

from app.core.errors import AuthenticationError, ConflictError
from app.core.security import PasswordHasher, TokenService
from app.models import User
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginIn, RegisterIn
from app.services import roles

# Hash de una contraseña cualquiera: si el correo no existe se verifica contra este,
# para que la respuesta tarde lo mismo y no revele qué correos están registrados.
_DUMMY_HASH = PasswordHasher().hash("dummy-password-1")


class AuthService:
    def __init__(self, users: UserRepository, catalogs: CatalogRepository,
                 hasher: PasswordHasher, tokens: TokenService):
        self.users = users
        self.catalogs = catalogs
        self.hasher = hasher
        self.tokens = tokens

    def register_citizen(self, data: RegisterIn) -> User:
        """El registro público siempre crea ciudadanos: el rol no lo elige quien se registra."""
        if self.users.exists_email(data.email):
            raise ConflictError("Ya existe una cuenta con ese correo electrónico.")
        if self.users.exists_document(data.document_number):
            raise ConflictError("Ya existe una cuenta con ese número de documento.")
        user = User(
            role_id=self.catalogs.role_by_code(roles.CITIZEN).id,
            first_name=data.first_name,
            last_name=data.last_name,
            document_type=data.document_type,
            document_number=data.document_number,
            email=data.email,
            password_hash=self.hasher.hash(data.password),
        )
        try:
            self.users.add(user)
            self.users.db.commit()
        except IntegrityError:
            # Dos registros simultáneos con el mismo dato: la restricción UNIQUE de la BD decide.
            self.users.db.rollback()
            raise ConflictError("Ya existe una cuenta con ese correo o documento.")
        return user

    def login(self, data: LoginIn) -> tuple[str, User]:
        user = self.users.get_by_email(data.email)
        valid = self.hasher.verify(data.password, user.password_hash if user else _DUMMY_HASH)
        if not user or not valid or not user.is_active:
            raise AuthenticationError("Correo o contraseña incorrectos.")
        return self.tokens.create(user.id, user.role.code), user

    def user_from_token(self, token: str) -> User:
        # Se relee el usuario en cada petición: si lo desactivan o le cambian el rol, aplica ya.
        user = self.users.get(self.tokens.decode_user_id(token))
        if not user or not user.is_active:
            raise AuthenticationError("Sesión inválida o expirada. Inicie sesión de nuevo.")
        return user
