from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in the project.
    Uses modern SQLAlchemy 2.0 type-mapping.
    """

    type_annotation_map = {
        dict[str, Any]: JSONB,
        uuid.UUID: PG_UUID(as_uuid=True),
    }
