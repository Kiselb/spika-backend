"""rename_survey_conclusion_val_to_q15

Revision ID: 9559a186b1bb
Revises: cafd97fe0323
Create Date: 2026-06-13 19:10:21.912032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9559a186b1bb'
down_revision: Union[str, Sequence[str], None] = 'cafd97fe0323'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'Surveys',
        'survey_conclusion_val',
        new_column_name='survey_conclusion_q15'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'Surveys',
        'survey_conclusion_q15',
        new_column_name='survey_conclusion_val'
    )
