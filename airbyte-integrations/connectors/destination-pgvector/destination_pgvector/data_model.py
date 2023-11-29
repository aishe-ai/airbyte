import uuid

# needed, dont ask me why
import uuid as uuid_pkg
import random
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy import Column, ForeignKey, Index

from pgvector.sqlalchemy import Vector


class Organization(SQLModel, table=True):
    uuid: uuid_pkg.UUID = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    data_sources: List["DataSource"] = Relationship(back_populates="organization")
    members: List["Member"] = Relationship(back_populates="organization")


class DataSource(SQLModel, table=True):
    uuid: uuid_pkg.UUID = Field(primary_key=True)
    organization_uuid: uuid_pkg.UUID = Field(foreign_key="organization.uuid")
    name: str
    description: Optional[str] = None
    bot_auth_data: dict = Field(sa_column=Column(JSONB))
    document_table_metadata: dict = Field(sa_column=Column(JSONB))
    airbyte_meta_data: dict = Field(sa_column=Column(JSONB))
    organization: Organization = Relationship(back_populates="data_sources")
    memberships: List["Membership"] = Relationship(back_populates="data_source")


class Member(SQLModel, table=True):
    uuid: uuid_pkg.UUID = Field(primary_key=True)
    organization_uuid: uuid_pkg.UUID = Field(foreign_key="organization.uuid")
    email: str
    name: str
    organization: Organization = Relationship(back_populates="members")
    memberships: List["Membership"] = Relationship(back_populates="member")


class DocumentTableTemplate(SQLModel):
    # Note: This is a template for dynamically named document tables.
    uuid: uuid_pkg.UUID = Field(primary_key=True)
    data_source_uuid: uuid_pkg.UUID = Field(foreign_key="datasource.uuid")
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    context_data: dict = Field(sa_column=Column(JSONB))
    embeddings: List[float] = Field(sa_column=Column(Vector(None)))
    content: Optional[str] = None
    memberships: List["Membership"] = Relationship(back_populates="document")


class Membership(SQLModel, table=True):
    uuid: uuid_pkg.UUID = Field(primary_key=True)
    data_source_uuid: uuid_pkg.UUID = Field(foreign_key="datasource.uuid")
    member_uuid: uuid_pkg.UUID = Field(foreign_key="member.uuid")
    document_uuid: uuid_pkg.UUID  # No foreign key here, as it's dynamic
    data_source_meta_data: dict = Field(sa_column=Column(JSONB))
    data_source: DataSource = Relationship(back_populates="memberships")
    member: Member = Relationship(back_populates="memberships")
    # 'document' relationship will be added dynamically


def create_data_source(name: str, organization: Organization, document_table_name=""):
    return DataSource(
        uuid=str(uuid.uuid4()),
        name=name,
        description=f"Airbyte Data Source",
        bot_auth_data={},  # Assuming this is the correct format for your JSONB field
        document_table_metadata={name: document_table_name},
        airbyte_meta_data={},  # Assuming a default empty dict, adjust as needed
        organization_uuid=organization.uuid,
    )


def create_mock_organization(org_name=None, member_name=None, member_email=None):
    # Use provided values or generate random ones
    org_name = org_name or f"Organization {random.randint(1, 1000)}"
    member_name = member_name or f"Member {random.randint(1, 1000)}"
    member_email = member_email or f"user{random.randint(1, 1000)}@example.com"

    # Create an Organization instance
    organization = Organization(uuid=str(uuid.uuid4()), name=org_name, description=f"Description {random.randint(1, 1000)}")

    # Create a Member instance
    member = Member(
        uuid=str(uuid.uuid4()),
        email=member_email,
        name=member_name,
        organization_uuid=organization.uuid,
    )

    # Create a DataSource instance
    data_source = DataSource(
        uuid=str(uuid.uuid4()),
        name=f"DataSource {random.randint(1, 1000)}",
        description=f"Description {random.randint(1, 1000)}",
        bot_auth_data={},  # Assuming JSONB field
        document_table_metadata={},  # Assuming JSONB field
        airbyte_meta_data={},  # Assuming JSONB field
        organization_uuid=organization.uuid,
    )

    # Create a dynamically named DocumentTable instance
    document_table = document_table_factory(organization, data_source)

    # Create a Membership instance
    membership = Membership(
        uuid=str(uuid.uuid4()),
        data_source_uuid=data_source.uuid,
        member_uuid=member.uuid,
        document_uuid=document_table.uuid,  # Assuming this is the correct field
        data_source_meta_data={},  # Assuming JSONB field
    )

    return organization, member


def document_table_factory(organization: Organization, data_source: DataSource) -> SQLModel:
    class DocumentTableTemplate(SQLModel, table=True):
        __tablename__ = f"document_table__{organization.name}_{data_source.name}"

        # Note: This is a template for dynamically named document tables.
        uuid: uuid_pkg.UUID = Field(primary_key=True)
        data_source_uuid: uuid_pkg.UUID = Field(sa_column=Column(SQLAlchemyUUID, ForeignKey("datasource.uuid", ondelete="CASCADE")))
        name: str
        description: Optional[str] = None
        url: Optional[str] = None
        context_data: dict = Field(sa_column=Column(JSONB))
        embeddings: List[float] = Field(sa_column=Column(Vector(2000)))
        content: Optional[str] = None
        # memberships: List["Membership"] = Relationship(back_populates="document")

    # Define the pgvector index
    Index(
        f"embedding_idx_{organization.name}_{data_source.name}",
        DocumentTableTemplate.embeddings,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 200},
        postgresql_ops={"embeddings": "vector_l2_ops"},
    )

    return DocumentTableTemplate

