"""drop unique constraint on teams.leader_employee_id

Revision ID: 5c9a31d7b4e2
Revises: 6f76f0a5c2e5
Create Date: 2025-12-05 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5c9a31d7b4e2"
down_revision: Union[str, Sequence[str], None] = "6f76f0a5c2e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unique constraint from teams.leader_employee_id if present."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for constraint in inspector.get_unique_constraints("teams"):
        column_names = set(constraint.get("column_names", []))
        if column_names == {"leader_employee_id"}:
            op.drop_constraint(constraint["name"], "teams", type_="unique")
            break


def downgrade() -> None:
    """Restore unique constraint on teams.leader_employee_id."""

    op.create_unique_constraint(
        "uq_teams_leader_employee_id", "teams", ["leader_employee_id"]
    )
