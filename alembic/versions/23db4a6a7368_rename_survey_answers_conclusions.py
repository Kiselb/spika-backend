"""rename_survey_answers_conclusions

Revision ID: 23db4a6a7368
Revises: 6961dd941b41
Create Date: 2026-06-13 18:46:58.884309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23db4a6a7368'
down_revision: Union[str, Sequence[str], None] = '6961dd941b41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('SurveyAnswersConclusions', 'SurveysAnswersConclusions')


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table('SurveysAnswersConclusions', 'SurveyAnswersConclusions')
