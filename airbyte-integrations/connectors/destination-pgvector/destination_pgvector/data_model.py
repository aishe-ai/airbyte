from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType
from sqlalchemy import func, cast, Numeric, Column
from sqlalchemy.dialects.postgresql import ARRAY

from sqlalchemy.sql.expression import bindparam

from pgvector.sqlalchemy import Vector

from pydantic import UUID4, EmailStr


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
    embedding: List[float] = Field(sa_column=Column(Vector(None)))
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
