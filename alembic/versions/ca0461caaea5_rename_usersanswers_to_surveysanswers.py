"""rename UsersAnswers to SurveysAnswers

Revision ID: ca0461caaea5
Revises: 3863d773eb75
Create Date: 2026-04-30 17:52:03.098947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca0461caaea5'
down_revision: Union[str, Sequence[str], None] = '3863d773eb75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('UsersAnswers', 'SurveysAnswers')


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table('SurveysAnswers', 'UsersAnswers')
