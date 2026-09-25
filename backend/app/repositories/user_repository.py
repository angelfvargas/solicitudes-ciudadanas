from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def exists_email(self, email: str) -> bool:
        return self.db.scalar(select(User.id).where(User.email == email)) is not None

    def exists_document(self, document_number: str) -> bool:
        return self.db.scalar(
            select(User.id).where(User.document_number == document_number)) is not None

    def list(self, role_code: str | None = None) -> list[User]:
        stmt = select(User).join(User.role).order_by(User.first_name, User.last_name)
        if role_code:
            stmt = stmt.where(Role.code == role_code)
        return list(self.db.scalars(stmt))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
