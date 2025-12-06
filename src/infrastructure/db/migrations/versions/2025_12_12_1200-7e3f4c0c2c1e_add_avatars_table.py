"""add avatars table

Revision ID: 7e3f4c0c2c1e
Revises: 5c9a31d7b4e2
Create Date: 2025-12-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e3f4c0c2c1e'
down_revision: Union[str, Sequence[str], None] = '5c9a31d7b4e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'avatars',
        sa.Column('employee_id', sa.UUID(), nullable=False),
        sa.Column('mime_type', sa.String(length=128), nullable=False, server_default='image/png'),
        sa.Column('image_small', sa.LargeBinary(), nullable=False),
        sa.Column('image_large', sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('employee_id')
    )


def downgrade() -> None:
    op.drop_table('avatars')
