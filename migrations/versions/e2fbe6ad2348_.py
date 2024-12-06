"""empty message

Revision ID: e2fbe6ad2348
Revises: a017af220149
Create Date: 2024-12-03 18:28:40.440008

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e2fbe6ad2348'
down_revision: Union[str, None] = 'a017af220149'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('photo_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('username', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'username')
    op.drop_column('users', 'photo_url')
    # ### end Alembic commands ###
