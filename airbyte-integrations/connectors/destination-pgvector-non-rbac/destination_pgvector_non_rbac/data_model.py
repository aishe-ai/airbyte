import uuid

# needed, dont ask me why
import uuid as uuid_pkg
from typing import List, Optional
from datetime import datetime

from sqlmodel import Field, SQLModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column
from pgvector.sqlalchemy import Vector

# hardcoded because not setable in openai api
EMBEDDING_DIMS = 1536

TEST_DATA = {
    "name": "test",
    "description": "test descriptionn",
    "url": "test url",
    "context_data": {},
    "date_source": "test",
    "embeddings": [[]],
    "page_content": "test content",
}


class Document(SQLModel, table=True):
    uuid: uuid_pkg.UUID = Field(primary_key=True, default=str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    context_data: dict = Field(sa_column=Column(JSONB))
    data_source: Optional[str] = None
    embeddings: List[float] = Field(sa_column=Column(Vector(EMBEDDING_DIMS)))
    page_content: Optional[str] = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now())


def create_document_obj(raw_document=TEST_DATA):
    return Document(**raw_document)
