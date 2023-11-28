from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from pydantic import UUID4, EmailStr
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType
from sqlalchemy import func, cast, Numeric, Column
from sqlalchemy.dialects.postgresql import ARRAY

from sqlalchemy.sql.expression import bindparam

from pgvector.sqlalchemy import Vector

from pydantic import UUID4, EmailStr

from dataclasses import dataclass
from polyfactory.factories import DataclassFactory
from uuid import uuid4
from typing import List, Optional
from pydantic import EmailStr
from random import randint, choice

import random
import uuid


# Define the Organizations SQLModel with its attributes.
class Organization(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    name: str
    description: Optional[str] = None

    # Relationships
    data_sources: List["DataSource"] = Relationship(back_populates="organization")
    members: List["Member"] = Relationship(back_populates="organization")


# Define the DataSources SQLModel with its attributes.
class DataSource(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    bot_auth_data: dict = Field(sa_column=Column(JSONB))
    document_table_name: str  # New field for document table name

    # Foreign key relation to Organizations.
    organization_uuid: UUID4 = Field(foreign_key="organization.uuid")
    organization: Organization = Relationship(back_populates="data_sources")

    # Relationships
    memberships: List["Membership"] = Relationship(back_populates="data_source")


# Define the Members SQLModel with its attributes.
class Member(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    email: EmailStr
    name: str

    # Foreign key relation to Organizations.
    organization_uuid: UUID4 = Field(foreign_key="organization.uuid")
    organization: Organization = Relationship(back_populates="members")

    # Relationships
    memberships: List["Membership"] = Relationship(back_populates="member")


# Define the DocumentTable SQLModel with its attributes.
class DocumentTable(SQLModel, table=True):
    name: str = Field(primary_key=True)
    uuid: UUID4
    description: Optional[str] = None
    url: str
    context_data: dict = Field(sa_column=Column(JSONB))
    embeddings: List[float] = Field(sa_column=Column(Vector(None)))
    content: str

    # Foreign key relation to DataSources.
    data_source_uuid: UUID4 = Field(foreign_key="datasource.uuid")
    # data_source: DataSource = Relationship(back_populates="document_tables")

    # Relationships
    memberships: List["Membership"] = Relationship(back_populates="document_table")


# Define the Memberships SQLModel with its attributes.
class Membership(SQLModel, table=True):
    uuid: UUID4 = Field(primary_key=True)
    data_source_role: str
    namespace_user_name: str
    document_table_name: str  # New field for document table name

    # Foreign key relations.
    data_source_uuid: UUID4 = Field(foreign_key="datasource.uuid")
    data_source: DataSource = Relationship(back_populates="memberships")

    member_uuid: UUID4 = Field(foreign_key="member.uuid")
    member: Member = Relationship(back_populates="memberships")

    document_uuid: UUID4 = Field(foreign_key="documenttable.name")
    document_table: DocumentTable = Relationship(back_populates="memberships")


# TODO, add function for generating mock data based on above data, which is linked together so it can be stored correctly into db, using polyfactory


def create_mock_organization(org_name=None, member_name=None, member_email=None):
    # Use provided values or generate random ones
    org_name = org_name or f"Organization {random.randint(1, 1000)}"
    member_name = member_name or f"Member {random.randint(1, 1000)}"
    member_email = member_email or f"user{random.randint(1, 1000)}@example.com"

    # Create an Organization instance
    organization = Organization(uuid=uuid.uuid4(), name=org_name, description=f"Description {random.randint(1, 1000)}")

    # Create a Member instance
    member = Member(
        uuid=uuid.uuid4(),
        email=member_email,
        name=member_name,
        organization_uuid=organization.uuid,
    )

    data_source = DataSource(
        uuid=uuid.uuid4(),
        name=f"DataSource {random.randint(1, 1000)}",
        description=f"Description {random.randint(1, 1000)}",
        bot_auth_data={},
        document_table_name=f"DocumentTable {random.randint(1, 1000)}",
        organization_uuid=organization.uuid,
    )
    document_table = DocumentTable(
        name=f"DocumentTable {random.randint(1, 1000)}",
        uuid=uuid.uuid4(),
        description=f"Description {random.randint(1, 1000)}",
        url=f"https://example.com/{random.randint(1, 1000)}",
        context_data={},
        embeddings=[random.uniform(0, 1) for _ in range(10)],
        content=f"Content {random.randint(1, 1000)}",
        data_source_uuid=data_source.uuid,
    )

    membership = Membership(
        uuid=uuid.uuid4(),
        data_source_role=random.choice(["admin", "user", "viewer"]),
        namespace_user_name=f"User {random.randint(1, 1000)}",
        document_table_name=document_table.name,
        data_source_uuid=data_source.uuid,
        member_uuid=member.uuid,
        document_uuid=document_table.uuid,
    )

    # return organization, data_source, member, document_table, membership

    return organization, member
