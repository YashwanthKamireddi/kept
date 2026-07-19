"""follow-up attribution (asked_by_keeper_id)

Revision ID: 67f120ae415d
Revises: 3b50a73dae88
Create Date: 2026-07-19 10:40:53.468438

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "67f120ae415d"
down_revision: Union[str, Sequence[str], None] = "3b50a73dae88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Batch mode: SQLite rebuilds the table to add a FK constraint.
    with op.batch_alter_table("follow_ups") as batch:
        batch.add_column(sa.Column("asked_by_keeper_id", sa.String(length=32), nullable=True))
        batch.create_foreign_key(
            "fk_follow_ups_asked_by_keeper", "keepers", ["asked_by_keeper_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("follow_ups") as batch:
        batch.drop_constraint("fk_follow_ups_asked_by_keeper", type_="foreignkey")
        batch.drop_column("asked_by_keeper_id")
