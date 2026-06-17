"""add_conclusion_text_to_surveys_answers

Revision ID: 7c5322122edf
Revises: 4c0af024cb79
Create Date: 2026-06-15 15:18:43.745333

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c5322122edf'
down_revision: Union[str, Sequence[str], None] = '4c0af024cb79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('SurveysAnswers', sa.Column('conclusion_text', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('SurveysAnswers', 'conclusion_text')
