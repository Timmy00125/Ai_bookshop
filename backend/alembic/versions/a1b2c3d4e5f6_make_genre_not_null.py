"""make genre not null

Revision ID: a1b2c3d4e5f6
Revises: 6cabbfabbb81
Create Date: 2026-05-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6cabbfabbb81'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update any NULL genres to 'Uncategorized' before making NOT NULL
    op.execute("UPDATE books SET genre = 'Uncategorized' WHERE genre IS NULL")
    op.alter_column('books', 'genre', nullable=False)


def downgrade() -> None:
    op.alter_column('books', 'genre', nullable=True)
