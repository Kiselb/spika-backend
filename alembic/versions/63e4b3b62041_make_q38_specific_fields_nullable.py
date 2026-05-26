"""make Q38-specific fields nullable


Revision ID: 63e4b3b62041
Revises: 44de0ef734e2
Create Date: 2026-05-25 17:41:14.794868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63e4b3b62041'
down_revision: Union[str, Sequence[str], None] = '44de0ef734e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('Questions', 'type_of_thinking', existing_type=sa.Integer(), nullable=True)
    op.alter_column('Questions', 'focus', existing_type=sa.Text(), nullable=True)
    op.alter_column('Questions', 'clarification_1', existing_type=sa.Text(), nullable=True)
    op.alter_column('Questions', 'clarification_2', existing_type=sa.Text(), nullable=True)
    op.alter_column('Questions', 'key_indicators', existing_type=sa.Text(), nullable=True)
    op.alter_column('Questions', 'proof', existing_type=sa.Text(), nullable=True)
    op.alter_column('Questions', 'interpretation_template', existing_type=sa.Text(), nullable=True)

    op.create_check_constraint(
        constraint_name="ck_q38_fields_required",
        table_name="Questions",
        condition=(
            "questions_type_id <> 2 OR ("
            "type_of_thinking IS NOT NULL AND "
            "focus IS NOT NULL AND "
            "clarification_1 IS NOT NULL AND "
            "clarification_2 IS NOT NULL AND "
            "key_indicators IS NOT NULL AND "
            "proof IS NOT NULL AND "
            "interpretation_template IS NOT NULL"
            ")"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('Questions', 'type_of_thinking', existing_type=sa.Integer(), nullable=False)
    op.alter_column('Questions', 'focus', existing_type=sa.Text(), nullable=False)
    op.alter_column('Questions', 'clarification_1', existing_type=sa.Text(), nullable=False)
    op.alter_column('Questions', 'clarification_2', existing_type=sa.Text(), nullable=False)
    op.alter_column('Questions', 'key_indicators', existing_type=sa.Text(), nullable=False)
    op.alter_column('Questions', 'proof', existing_type=sa.Text(), nullable=False)
    op.alter_column('Questions', 'interpretation_template', existing_type=sa.Text(), nullable=False)

    op.drop_constraint("ck_q38_fields_required", "Questions", type_="check")
