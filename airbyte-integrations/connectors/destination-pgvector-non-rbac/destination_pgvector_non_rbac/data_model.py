import uuid

# needed, dont ask me why
import uuid as uuid_pkg
from typing import List, Optional

from sqlmodel import Field, SQLModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column

from pgvector.sqlalchemy import Vector


class Document(SQLModel, table=True):
    # Common fields
    uuid: uuid_pkg.UUID = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    context_data: dict = Field(sa_column=Column(JSONB))
    data_source: Optional[str] = None
    # hardcoded because not setable in openai api
    embeddings: List[float] = Field(sa_column=Column(Vector(1536)))
    content: Optional[str] = None
    # Add other common fields or relationships here


def create_document(organization, data_source, raw_document):

    # Convert UUIDs to strings
    uuid_str = str(uuid.uuid4())

    return Document(
        uuid=uuid_str,
        name="Test document",
        description="Airbyte Data Source Document",
        url="",
        context_data={},
        embeddings=raw_document.embedding,
        content=raw_document.page_content,
    )
