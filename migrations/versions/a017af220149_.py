"""empty message

Revision ID: a017af220149
Revises: 0a53ebb3502d
Create Date: 2024-12-02 10:46:00.811074

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a017af220149'
down_revision: Union[str, None] = '0a53ebb3502d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('competitions', 'competitions_rooms')
    op.add_column('competitions_rooms', sa.Column('owner_id', sa.Integer(), nullable=False))
    op.add_column('competitions_rooms', sa.Column('language_from_id', sa.Integer(), nullable=False))
    op.add_column('competitions_rooms', sa.Column('language_to_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'competitions_rooms', 'languages', ['language_from_id'], ['id'])
    op.create_foreign_key(None, 'competitions_rooms', 'users', ['owner_id'], ['id'])
    op.create_foreign_key(None, 'competitions_rooms', 'languages', ['language_to_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('competitions_rooms', 'competitions')
    op.drop_constraint(None, 'competitions', type_='foreignkey')
    op.drop_constraint(None, 'competitions', type_='foreignkey')
    op.drop_constraint(None, 'competitions', type_='foreignkey')
    op.drop_column('competitions', 'language_to_id')
    op.drop_column('competitions', 'language_from_id')
    op.drop_column('competitions', 'owner_id')
    # ### end Alembic commands ###
