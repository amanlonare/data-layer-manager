from typing import Any

from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    """
    The normalized "Handshake" contract for extracted content before chunking.
    Produced by the parsing layer, ingested by the chunking layer.
    """

    raw_content: str
    title: str | None = None
    source_locator: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    # RESERVED extensibility field; MVP should not depend on it
    sections: list[dict[str, Any]] = Field(default_factory=list)
