"""add admin user

Revision ID: c03d129033b8
Revises: c8585c75a9dd
Create Date: 2026-04-30 20:04:41.333663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext
from datetime import date
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# revision identifiers, used by Alembic.
revision: str = 'c03d129033b8'
down_revision: Union[str, Sequence[str], None] = 'c8585c75a9dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Хеширование пароля
    hashed_pw = pwd_context.hash(os.getenv("ADMIN_PASSWORD"))

    # 2. Получаем connection
    conn = op.get_bind()

    # 3. Вставляем пользователя
    #    Все обязательные поля должны быть заполнены.
    #    Дата рождения и пол для админа могут быть любыми допустимыми.
    result = conn.execute(
        sa.text("""
            INSERT INTO "Users" (first_name, last_name, email, date_of_birth, gender, hashed_password)
            VALUES (:fn, :ln, :email, :dob, :gender, :pw)
            RETURNING user_id
        """),
        {
            "fn": "Admin",
            "ln": "Admin",
            "email": "admin@spika.ru",
            "dob": date(1990, 1, 1),
            "gender": "Male",
            "pw": hashed_pw
        }
    )
    user_id = result.scalar()

    # 4. Назначаем роль Admin (role_id = 3) — убедитесь, что роль существует
    conn.execute(
        sa.text("""
            INSERT INTO "UsersRoles" (user_id, role_id) VALUES (:uid, :rid)
        """),
        {"uid": user_id, "rid": 3}
    )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    # Удаляем пользователя по email (уникальному)
    conn.execute(
        sa.text("DELETE FROM \"Users\" WHERE email = 'admin@spika.ru'")
    )
