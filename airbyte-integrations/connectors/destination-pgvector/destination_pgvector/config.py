#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

from typing import Union

import dpath.util
from airbyte_cdk.destinations.vector_db_based.config import (
    AzureOpenAIEmbeddingConfigModel,
    CohereEmbeddingConfigModel,
    FakeEmbeddingConfigModel,
    OpenAICompatibleEmbeddingConfigModel,
    OpenAIEmbeddingConfigModel,
    ProcessingConfigModel,
)
from airbyte_cdk.utils.spec_schema_transformations import resolve_refs
from pydantic import BaseModel, Field, SecretStr


class DatabaseConfigModel(BaseModel):
    host: str = Field(..., title="Host", description="The host address of the database.")
    port: int = Field(default=5432, title="Port", description="The port number on which the database server is running.")
    database: str = Field(..., title="Name", description="The name of the database.")
    username: str = Field(..., title="Username", description="The username used to authenticate with the database.")
    password: SecretStr = Field(
        ..., title="Password", airbyte_secret=True, description="The password used to authenticate with the database."
    )

    class Config:
        schema_extra = {"group": "database"}


class ConfigModel(BaseModel):
    database: DatabaseConfigModel
    embedding: Union[
        OpenAIEmbeddingConfigModel,
        CohereEmbeddingConfigModel,
        FakeEmbeddingConfigModel,
        AzureOpenAIEmbeddingConfigModel,
        OpenAICompatibleEmbeddingConfigModel,
    ] = Field(..., title="Embedding", description="Embedding configuration", discriminator="mode", group="embedding", type="object")
    processing: ProcessingConfigModel

    class Config:
        title = "Pinecone Destination Config"
        schema_extra = {
            "groups": [
                {"id": "database", "title": "Datebase Config"},
                {"id": "processing", "title": "Processing"},
                {"id": "embedding", "title": "Embedding"},
            ]
        }

    @staticmethod
    def remove_discriminator(schema: dict) -> None:
        """pydantic adds "discriminator" to the schema for oneOfs, which is not treated right by the platform as we inline all references"""
        dpath.util.delete(schema, "properties/*/discriminator")

    @classmethod
    def schema(cls):
        """we're overriding the schema classmethod to enable some post-processing"""
        schema = super().schema()
        schema = resolve_refs(schema)
        cls.remove_discriminator(schema)
        return schema
