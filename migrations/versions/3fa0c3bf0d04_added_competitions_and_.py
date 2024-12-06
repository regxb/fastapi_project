"""Added competitions and CompetitionStatistics table

Revision ID: 3fa0c3bf0d04
Revises: b712cc63a2d3
Create Date: 2024-11-16 14:21:21.528309

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3fa0c3bf0d04'
down_revision: Union[str, None] = 'b712cc63a2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('competitions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('competition_statistics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('competition_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('user_points', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('competition_statistics')
    op.drop_table('competitions')
    # ### end Alembic commands ###
