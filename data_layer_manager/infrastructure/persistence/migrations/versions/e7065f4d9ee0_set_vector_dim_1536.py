"""set_vector_dim_1536

Revision ID: e7065f4d9ee0
Revises: e4f2533ea402
Create Date: 2026-04-06 00:29:26.451565

"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "e7065f4d9ee0"
down_revision: str | Sequence[str] | None = "e4f2533ea402"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to 1536 dimensions for OpenAI embeddings."""
    op.alter_column(
        "chunks",
        "embedding",
        existing_type=Vector(384),
        type_=Vector(1536),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema back to 384 dimensions."""
    op.alter_column(
        "chunks",
        "embedding",
        existing_type=Vector(1536),
        type_=Vector(384),
        existing_nullable=True,
    )
