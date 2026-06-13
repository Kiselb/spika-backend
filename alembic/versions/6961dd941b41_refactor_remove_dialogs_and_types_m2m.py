"""refactor_remove_dialogs_and_types_m2m

Revision ID: 6961dd941b41
Revises: 5b90c214b4b6
Create Date: 2026-06-13 18:37:06.056079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6961dd941b41'
down_revision: Union[str, Sequence[str], None] = '5b90c214b4b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Удалить таблицу SurveysTypesOfThinking
    op.drop_table('SurveysTypesOfThinking')

    # 2. Удалить таблицу SurveysAnswersDialogs
    op.drop_table('SurveysAnswersDialogs')

    # 3. Создать таблицу SurveyAnswersConclusions
    op.create_table(
        'SurveyAnswersConclusions',
        sa.Column('ConclusionID', sa.Integer(), nullable=False),
        sa.Column('ConclusionName', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('ConclusionID'),
        sa.UniqueConstraint('ConclusionName')
    )

    # 4. Заполнить начальными значениями
    op.execute("INSERT INTO \"SurveyAnswersConclusions\" (\"ConclusionID\", \"ConclusionName\") VALUES (1, 'Да')")
    op.execute("INSERT INTO \"SurveyAnswersConclusions\" (\"ConclusionID\", \"ConclusionName\") VALUES (2, 'Нет')")
    op.execute("INSERT INTO \"SurveyAnswersConclusions\" (\"ConclusionID\", \"ConclusionName\") VALUES (3, 'Условно Да')")

    # 5. Добавить колонку conclusion_id в SurveysAnswers
    op.add_column('SurveysAnswers', sa.Column('conclusion_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_surveys_answers_conclusion',
        'SurveysAnswers', 'SurveyAnswersConclusions',
        ['conclusion_id'], ['ConclusionID']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удалить внешний ключ и колонку
    op.drop_constraint('fk_surveys_answers_conclusion', 'SurveysAnswers', type_='foreignkey')
    op.drop_column('SurveysAnswers', 'conclusion_id')

    # Восстановить таблицы
    op.create_table(
        'SurveysTypesOfThinking',
        sa.Column('survey_id', sa.Integer(), sa.ForeignKey('Surveys.survey_id'), primary_key=True),
        sa.Column('types_of_thinking_id', sa.Integer(), sa.ForeignKey('TypesOfThinking.types_of_thinking_id'), primary_key=True)
    )

    op.create_table(
        'SurveysAnswersDialogs',
        sa.Column('dialog_pair_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('survey_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('dialog_pair_question', sa.Text(), nullable=False),
        sa.Column('dialog_pair_answer', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['survey_id', 'question_id'], ['SurveysAnswers.survey_id', 'SurveysAnswers.question_id'])
    )

    # Удалить таблицу SurveyAnswersConclusions
    op.drop_table('SurveyAnswersConclusions')

