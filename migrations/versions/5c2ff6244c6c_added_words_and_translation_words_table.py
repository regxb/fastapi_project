"""Added words and translation words table

Revision ID: 5c2ff6244c6c
Revises: b4cfeea8d417
Create Date: 2024-10-08 22:15:18.062374

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5c2ff6244c6c'
down_revision: Union[str, None] = 'b4cfeea8d417'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('words',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('language_id', sa.Integer(), nullable=False),
    sa.Column('part_of_speech', sa.String(), nullable=False),
    sa.Column('level', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('translation_words',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('word_id', sa.UUID(), nullable=False),
    sa.Column('from_language_id', sa.Integer(), nullable=False),
    sa.Column('to_language_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['from_language_id'], ['languages.id'], ),
    sa.ForeignKeyConstraint(['to_language_id'], ['languages.id'], ),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('translation_words')
    op.drop_table('words')
    # ### end Alembic commands ###
