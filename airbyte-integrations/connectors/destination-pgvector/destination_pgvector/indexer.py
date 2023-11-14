#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import json
import uuid

import chromadb
from airbyte_cdk.destinations.vector_db_based.document_processor import METADATA_RECORD_ID_FIELD, METADATA_STREAM_FIELD
from airbyte_cdk.destinations.vector_db_based.indexer import Indexer
from airbyte_cdk.destinations.vector_db_based.utils import create_stream_identifier, format_exception
from airbyte_cdk.models import ConfiguredAirbyteCatalog
from airbyte_cdk.models.airbyte_protocol import DestinationSyncMode
from chromadb.config import Settings
from destination_chroma.config import ChromaIndexingConfigModel
from destination_chroma.utils import is_valid_collection_name


class PGVectorIndexer(Indexer):
    def __init__(self, config: ChromaIndexingConfigModel):
        super().__init__(config)
        self.collection_name = config.collection_name

    def check(self):
        collection_name_validation_error = is_valid_collection_name(self.collection_name)
        if collection_name_validation_error:
            return collection_name_validation_error

        auth_method = self.config.auth_method
        if auth_method.mode == "persistent_client" and not auth_method.path.startswith("/local/"):
            return "Path must be prefixed with /local"

        client = self._get_client()
        try:
            heartbeat = client.heartbeat()
            if not heartbeat:
                return "Chroma client server is not alive"
            collection = client.get_or_create_collection(name=self.collection_name)
            count = collection.count()
            if count != 0 and not count:
                return f"unable to get or create collection with name {self.collection_name}"
            return
        except Exception as e:
            return format_exception(e)
        finally:
            del client

    def delete(self, delete_ids, namespace, stream):
        if len(delete_ids) > 0:
            self._delete_by_filter(field_name=METADATA_RECORD_ID_FIELD, field_values=delete_ids)

    def index(self, document_chunks, namespace, stream):
        entities = []
        for i in range(len(document_chunks)):
            chunk = document_chunks[i]
            entities.append(
                {
                    "id": str(uuid.uuid4()),
                    "embedding": chunk.embedding,
                    "metadata": self._normalize(chunk.metadata),
                    "document": chunk.page_content,
                }
            )
        self._write_data(entities)

    def pre_sync(self, catalog: ConfiguredAirbyteCatalog) -> None:
        self.client = self._get_client()
        streams_to_overwrite = [
            create_stream_identifier(stream.stream)
            for stream in catalog.streams
            if stream.destination_sync_mode == DestinationSyncMode.overwrite
        ]
        if len(streams_to_overwrite):
            self._delete_by_filter(field_name=METADATA_STREAM_FIELD, field_values=streams_to_overwrite)

    def _get_client(self):
        auth_method = self.config.auth_method
        if auth_method.mode == "persistent_client":
            path = auth_method.path
            client = chromadb.PersistentClient(path=path)
            return client

        elif auth_method.mode == "http_client":
            host = auth_method.host
            port = auth_method.port
            ssl = auth_method.ssl
            username = auth_method.username
            password = auth_method.password

            if username and password:
                settings = Settings(
                    chroma_client_auth_provider="chromadb.auth.basic.BasicAuthClientProvider",
                    chroma_client_auth_credentials=f"{username}:{password}",
                )
                client = chromadb.HttpClient(settings=settings, host=host, port=port, ssl=ssl)
            else:
                client = chromadb.HttpClient(host=host, port=port, ssl=ssl)
            return client
        return

    def _delete_by_filter(self, field_name, field_values):
        collection = self.client.get_collection(name=self.collection_name)
        where_filter = {field_name: {"$in": field_values}}
        collection.delete(where=where_filter)

    def _normalize(self, metadata: dict) -> dict:
        result = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                result[key] = value
            else:
                # JSON encode all other types
                result[key] = json.dumps(value)
        return result

    def _write_data(self, entities):
        ids = [entity["id"] for entity in entities]
        embeddings = [entity["embedding"] for entity in entities]
        if not any(embeddings):
            embeddings = None
        metadatas = [entity["metadata"] for entity in entities]
        documents = [entity["document"] for entity in entities]

        collection = self.client.get_collection(name=self.collection_name)
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

        # engine = migrate(config)
        # SQLModel.metadata.drop_all(engine)
        # engine = migrate(config)

        # Create a new session
        # with Session(engine) as session:
        #     # Create an organization
        #     organization = Organization(
        #         uuid=uuid4(), name="Test Organization", description="A test organization for verifying the write function."
        #     )

        #     # Create a DataSource related to the organization
        #     data_source = DataSource(
        #         uuid=uuid4(), name="Test DataSource", bot_auth_data={"token": "testtoken"}, organization_uuid=organization.uuid
        #     )

        #     # Create a Document related to the data_source
        #     document = Document(
        #         uuid=uuid4(),
        #         name="Test Document",
        #         description="A test document for verifying the write function.",
        #         url="https://example.com/test_document",
        #         context_data={"info": "test"},
        #         # embeddings=[0.0] * 128,  # Mocking a vector with 128 dimensions of zeros
        #         data_source_uuid=data_source.uuid,
        #         content="Sample content",  # Here, we ensure 'content' is not None
        #     )

        #     # Create a Member related to the organization
        #     member = Member(uuid=uuid4(), email="test_user@example.com", name="Test User", organization_uuid=organization.uuid)

        #     # Create a Membership which relates a Member, Document, and DataSource
        #     membership = Membership(
        #         uuid=uuid4(),
        #         data_source_role="viewer",
        #         namespace_user_name="test_user_namespace",
        #         data_source_uuid=data_source.uuid,
        #         member_uuid=member.uuid,
        #         document_uuid=document.uuid,
        #     )

        #     # Add all instances to the session and commit the transactions
        #     session.add(organization)
        #     session.add(data_source)
        #     session.add(document)
        #     session.add(member)
        #     session.add(membership)

        #     # Flush the changes to the database
        #     session.commit()

        # print(config, configured_catalog)

        # # Iterate over incoming messages
        # for message in input_messages:
        #     print("\n --->", message.record.data["field2"])
        #     yield message

        # if message.type == Type.RECORD:
        #     self.insert_record(message, engine)

        # elif message.type == Type.STATE:
        #     # State message indicates all previous records have been written
        #     # Only emit the state message here if you have a guarantee the previous records are written
        #     yield message

    # def insert_record(self, message: AirbyteMessage, engine):
    #     pass
    #     # You would implement your insert logic here using SQLModel and switch cases
    #     # with Session(engine) as session:
    #     #     # Map the record to your SQLModel class (e.g., YourRecordModel)
    #     #     record = YourRecordModel(**message.record.data)  # Transform the Airbyte record to your SQLModel instance

    #     #     # Add the record instance to the session and commit
    #     #     # Ensure your model instances match with your table structures and columns
    #     #     try:
    #     #         session.add(record)
    #     #         session.commit()
    #     #     except Exception as e:
    #     #         session.rollback()  # Rollback if any error occurs
    #     #         # Here you should handle the error (e.g., log to AirbyteLogger, raise a specific exception, etc.)

    # # Note: Make sure the models in your_data_models.py are defined correctly to match the schema of the destination tables.
    # # This code does not handle specific schema issues, dependencies between tables, or advanced use cases like upserting.
