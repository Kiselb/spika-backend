"""rename_type_of_thinking_column

Revision ID: cafd97fe0323
Revises: 23db4a6a7368
Create Date: 2026-06-13 18:50:54.083013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cafd97fe0323'
down_revision: Union[str, Sequence[str], None] = '23db4a6a7368'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('Questions', 'type_of_thinking', new_column_name='type_of_thinking_id')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('Questions', 'type_of_thinking_id', new_column_name='type_of_thinking')
