"""add legal entity and department to employees

Revision ID: ee57aadd1993
Revises: 14afeb5dd725
Create Date: 2025-11-13 12:13:31.694679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ee57aadd1993"
down_revision: Union[str, Sequence[str], None] = "14afeb5dd725"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("legal_entity", sa.String(), nullable=True))
    op.add_column("employees", sa.Column("department", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("employees", "department")
    op.drop_column("employees", "legal_entity")