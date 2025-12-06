"""add object_id to employees

Revision ID: 6f76f0a5c2e5
Revises: 7373f8167d4a
Create Date: 2025-12-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f76f0a5c2e5"
down_revision: Union[str, Sequence[str], None] = "7373f8167d4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("employees", sa.Column("object_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_employees_object_id", "employees", ["object_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_employees_object_id", "employees", type_="unique")
    op.drop_column("employees", "object_id")
