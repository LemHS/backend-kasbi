"""nullable_user_id_in_document

Revision ID: 0473a98e38ea
Revises: 75c96012698f
Create Date: 2026-02-18 09:01:46.038855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '0473a98e38ea'
down_revision: Union[str, None] = '75c96012698f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "documents",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "UPDATE documents SET user_id = 1 WHERE user_id IS NULL;"
    )
    op.alter_column(
        "documents",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

