"""new_document_status

Revision ID: 75c96012698f
Revises: a2a016ad85e1
Create Date: 2026-02-09 19:02:21.510061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '75c96012698f'
down_revision: Union[str, None] = 'a2a016ad85e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
