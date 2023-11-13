from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel, create_engine
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB, BYTEA
from sqlalchemy.types import UserDefinedType

from pydantic import UUID4, EmailStr


class PgVector(UserDefinedType):
    """A custom SQLAlchemy type for PGVector PostgreSQL type."""

    def get_col_spec(self, **kwargs):
        return "vector"

    def bind_expression(self, bindvalue):
        # Serialize the bindvalue for insertion into the database.
        # This should convert from a Python structure into a pgvector-compatible format.
        raise NotImplementedError("bind_expression not implemented for pgvector")

    def column_expression(self, col):
        # Deserialize the column value fetched from the database.
        # This should convert from a pgvector-compatible format into a Python structure.
        raise NotImplementedError("column_expression not implemented for pgvector")

    def bind_processor(self, dialect):
        # Process the internally serialized value before sending to the database.
        def process(value):
            # Further processing might be necessary here
            return value

        return process

    def result_processor(self, dialect, coltype):
        # Process the result value fetched from the database.
        def process(value):
            # Convert into a Python list or numpy array as needed
            return value

        return process


# Define the Organizations SQLModel with its attributes.
class Organization(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    name: str
    description: Optional[str] = None

    # Establish the relationship as in the diagram.
    data_sources: List["DataSource"] = Relationship(back_populates="organization")
    members: List["Member"] = Relationship(back_populates="organization")


# Define the DataSources SQLModel with its attributes.
class DataSource(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    bot_auth_data: dict = Field(sa_column=Column(JSONB))

    # Foreign key relation to Organizations.
    organization_uuid: UUID4 = Field(foreign_key="organization.uuid")
    organization: Organization = Relationship(back_populates="data_sources")

    # Establish the relationship as in the diagram.
    documents: List["Document"] = Relationship(back_populates="data_source")
    memberships: List["Membership"] = Relationship(back_populates="data_source")


# Define the Members SQLModel with its attributes.
class Member(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    email: EmailStr
    name: str

    # Foreign key relation to Organizations.
    organization_uuid: UUID4 = Field(foreign_key="organization.uuid")
    organization: Organization = Relationship(back_populates="members")

    # Establish the relationship as in the diagram.
    memberships: List["Membership"] = Relationship(back_populates="member")


# Define the Documents SQLModel with its attributes.
class Document(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    url: str
    context_data: dict = Field(sa_column=Column(JSONB))
    embeddings: list = Field(sa_column=Column(PgVector))

    # embeddings: Any  # This type will depend on what you mean by "vector[]", which isn't a standard SQL type
    content: str

    # Foreign key relation to DataSources.
    data_source_uuid: UUID4 = Field(foreign_key="datasource.uuid")
    data_source: DataSource = Relationship(back_populates="documents")

    # Establish the relationship as in the diagram.
    memberships: List["Membership"] = Relationship(back_populates="document")


# Define the Memberships SQLModel with its attributes.
class Membership(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    data_source_role: str
    namespace_user_name: str

    # Foreign key relations.
    data_source_uuid: UUID4 = Field(foreign_key="datasource.uuid")
    data_source: DataSource = Relationship(back_populates="memberships")

    member_uuid: UUID4 = Field(foreign_key="member.uuid")
    member: Member = Relationship(back_populates="memberships")

    document_uuid: UUID4 = Field(foreign_key="document.uuid")
    document: Document = Relationship(back_populates="memberships")


def create_vector_extension(engine):
    """Creates the 'vector' PostgreSQL extension if it doesn't exist."""
    with engine.begin() as connection:  # Use 'begin' to auto-commit
        connection.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def create_tables(database_url: str):
    """
    Creates the 'vector' extension and database tables for all SQLModel classes.
    """
    engine = create_engine(database_url)

    # Create 'vector' extension
    create_vector_extension(engine)

    # Create tables
    with engine.begin() as connection:  # Use 'begin' to auto-commit
        SQLModel.metadata.create_all(connection)
