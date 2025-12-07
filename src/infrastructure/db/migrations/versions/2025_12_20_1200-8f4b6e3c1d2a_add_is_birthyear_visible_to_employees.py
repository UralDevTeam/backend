"""add is_birthyear_visible to employees

Revision ID: 8f4b6e3c1d2a
Revises: 7e3f4c0c2c1e
Create Date: 2025-12-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f4b6e3c1d2a'
down_revision: Union[str, Sequence[str], None] = '7e3f4c0c2c1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'employees',
        sa.Column('is_birthyear_visible', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )


def downgrade() -> None:
    op.drop_column('employees', 'is_birthyear_visible')