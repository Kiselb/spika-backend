"""add questions validators

Revision ID: 25222d9a21ea
Revises: 22857ebf9901
Create Date: 2026-05-30 14:07:23.818308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25222d9a21ea'
down_revision: Union[str, Sequence[str], None] = '22857ebf9901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("INSERT INTO \"QuestionsValidatorsTypes\" (validator_type_id, validator_type_name) VALUES (2, 'Целое число больше 0')")
    op.execute("INSERT INTO \"QuestionsValidatorsTypes\" (validator_type_id, validator_type_name) VALUES (3, 'Число с плавающей точкой больше 0')")
    op.execute("INSERT INTO \"QuestionsValidatorsTypes\" (validator_type_id, validator_type_name) VALUES (4, 'Непустая строка с длиной от 2 до 2048 символов')")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
