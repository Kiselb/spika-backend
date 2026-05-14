"""add_developer_role

Revision ID: 09b5a0119121
Revises: 5c6c0922815a
Create Date: 2026-05-13 13:49:56.146180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09b5a0119121'
down_revision: Union[str, Sequence[str], None] = '5c6c0922815a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "INSERT INTO \"Roles\" (role_id, role_name) VALUES (4, 'Developer')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM \"Roles\" WHERE role_name = 'Developer'"
    )
