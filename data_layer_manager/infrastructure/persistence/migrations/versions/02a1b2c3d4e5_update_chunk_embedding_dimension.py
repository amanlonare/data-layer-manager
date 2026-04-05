"""update_chunk_embedding_dimension

Revision ID: 02a1b2c3d4e5
Revises: bfba0d1203d3
Create Date: 2026-04-03 13:50:00.000000

"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "02a1b2c3d4e5"
down_revision: str | None = "bfba0d1203d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Adjust column size. In PostgreSQL/pgvector, this usually requires dropping and re-adding or ALTER
    # For a dev-stage project, we'll alter the type.
    op.alter_column(
        "chunks",
        "embedding",
        existing_type=Vector(1536),
        type_=Vector(384),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "chunks",
        "embedding",
        existing_type=Vector(384),
        type_=Vector(1536),
        existing_nullable=True,
    )
