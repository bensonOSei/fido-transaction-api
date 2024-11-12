"""Add user email column to users table

Revision ID: 4efe0abc666b
Revises: 4dbfefd29e47
Create Date: 2024-11-12 09:09:05.989228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4efe0abc666b'
down_revision: Union[str, None] = '4dbfefd29e47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(), nullable=True, unique=True))


def downgrade() -> None:
    op.drop_column('users', 'email')
    op.drop_constraint('users_email_key', 'users', type_='unique')
