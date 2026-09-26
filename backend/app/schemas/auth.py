import re
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

from app.schemas.user import UserOut

NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' -]{2,60}$")


class RegisterIn(BaseModel):
    first_name: str
    last_name: str
    document_type: Literal["CC", "CE", "TI", "PA"]
    document_number: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)

    @field_validator("first_name", "last_name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not NAME_RE.match(v):
            raise ValueError("Solo letras y espacios, entre 2 y 60 caracteres")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("La contraseña debe tener al menos una letra y un número")
        if len(v.encode("utf-8")) > 72:  # límite de bcrypt
            raise ValueError("La contraseña es demasiado larga")
        return v

    @field_validator("document_number")
    @classmethod
    def valid_document(cls, v: str, info: ValidationInfo) -> str:
        # document_type se valida antes (va primero en el modelo); si no es válido, ya hay un error ahí.
        document_type = info.data.get("document_type")
        number = v.strip().upper()
        if document_type in ("CC", "TI"):
            ok, rule = re.fullmatch(r"\d{6,10}", number), "entre 6 y 10 dígitos"
        elif document_type in ("CE", "PA"):  # admiten letras
            ok, rule = re.fullmatch(r"[A-Z0-9]{5,15}", number), "entre 5 y 15 letras o números"
        else:
            return number
        if not ok:
            raise ValueError(f"Número de documento inválido para {document_type}: {rule}")
        return number


class LoginIn(BaseModel):
    # En el login no se valida el formato: basta con que coincida con una cuenta existente.
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=64)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
