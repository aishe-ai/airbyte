#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import os
import logging

from airbyte_cdk.destinations.vector_db_based.document_processor import METADATA_RECORD_ID_FIELD, METADATA_STREAM_FIELD
from airbyte_cdk.destinations.vector_db_based.indexer import Indexer
from airbyte_cdk.destinations.vector_db_based.utils import create_stream_identifier, format_exception
from airbyte_cdk.models import ConfiguredAirbyteCatalog, AirbyteMessage, ConfiguredAirbyteCatalog
from airbyte_cdk.models.airbyte_protocol import DestinationSyncMode

from typing import Any, Generator, Iterable, List, Optional, Tuple, TypeVar

from destination_pgvector.config import ConfigModel


from sqlmodel import Session, select

from destination_pgvector.data_model import DataSource, DocumentTableTemplate, create_data_source
from destination_pgvector.database import get_engine, get_test_data

# Problem: one document table for all customers doesnt allow different indixes per customer
# -> partial paritioning or extra table
# each document_source needs its own table for its document and the specifiy embedding index

# indexing=IVFFlatIndexingModel(mode='ivfflat') database=DatabaseConfigModel(host='localhost', port=5432, database='aisheAI', username='aisheAI', password=SecretStr('**********')) embedding=OpenAIEmbeddingConfigModel(mode='openai', openai_key='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') processing=ProcessingConfigModel(chunk_size=1024, chunk_overlap=0, text_fields=['title', 'content.body'], metadata_fields=['author', 'publish_date'], text_splitter=SeparatorSplitterConfigModel(mode='separator', separators=['"\\n\\n"', '"\\n"', '" "', '"."'], keep_separator=False), field_name_mappings=[])


class PGVectorIndexer(Indexer):
    def __init__(self, config: ConfigModel):
        super().__init__(config)
        self.db_engine = get_engine(config.database)

    def pre_sync(self, catalog):
        """
        Run before the sync starts.
        This method should be used to make sure all records in the destination that belong to streams with a destination mode of overwrite are deleted.

        Each record has a metadata field with the name airbyte_cdk.destinations.vector_db_based.document_processor.METADATA_STREAM_FIELD which can be used to filter documents for deletion.
        Use the airbyte_cdk.destinations.vector_db_based.utils.create_stream_identifier method to create the stream identifier based on the stream definition to use for filtering.
        """
        # TODO: handle dynamic index changes for embeddings here, provided by frontend

        # Step 1: Retrieve the current index configuration from the database
        desired_embedding_index = self.config.indexing.mode
        # TODO: check org name extraction is possible

        # Check for test or dev environment
        if os.environ.get("ENVIRONMENT") in ["test", "dev"]:
            organization, test_member = get_test_data(self.db_engine)

        with Session(self.db_engine) as session:
            for configured_stream in catalog.streams:
                # Extract the name of the stream
                data_source_name = configured_stream.stream.name

                # Check if the data source entry exists and is linked to the current organization
                statement = select(DataSource).where(DataSource.name == data_source_name, DataSource.organization_uuid == organization.uuid)
                data_source = session.exec(statement).first()
                if not data_source:
                    # Handle the case where the data source does not exist or is not linked to the current organization
                    logging.info("Creating new data source")
                    data_source = create_data_source(name=data_source_name, organization=organization)
                    session.add(data_source)
                    session.commit()

                # Construct the document table
                document_table_name = f"document_table__{organization.name}_{data_source.name}"
                print(document_table_name)

                # Example usage

                # DocumentTable, data_source = create_table_and_link_data_source(
                #     target_table_name, data_source_name, organization, self.db_engine
                # )

                # # Check if the table exists with the correct index and is linked in the data source table of the organization
                # statement = select(DataSource).where(DataSource.name == data_source_name)
                # data_source = session.exec(statement).first()

                # if data_source and data_source.document_table_name == target_table_name:
                #     # Check if the table has the correct index
                #     # This requires a direct SQL query as SQLModel does not support index introspection
                #     # TODO: Implement the SQL query to check the index on the target table

                #     print(f"Table {target_table_name} exists and is correctly linked.")
                # else:
                #     # TODO: Handle the case where the table does not exist or is not correctly linked
                #     print(f"Table {target_table_name} does not exist or is not correctly linked.")

        # for configured_stream in catalog:
        #     # Extract the name of the stream
        #     data_source_name = configured_stream[1][0].stream.name

        #     # TODO: improve table name interpolation for easier destruction while respecting postgres best practises
        #     target_table_name = f"data_source__{target_org_name}_{data_source_name}"

        #     # TODO: check if table exists with correct index and is linked in data source table of organisation, using sqlmodel only

        #     print(target_table_name, data_source_name)

        pass

    def post_sync(self):
        """
        Run after the sync finishes. This method should be used to perform any cleanup operations and can return a list of AirbyteMessages to be logged.
        """
        return []

    def index(self, document_chunks, namespace, stream):
        """
        Index a list of document chunks.

        This method should be used to index the documents in the destination.
        All chunks belong to the stream and namespace specified in the parameters.
        """
        # just store documents into db with correct deps
        # explizit indexing not needed, done by postgres and pgvector index
        pass

    def delete(self, delete_ids, namespace, stream):
        # delete document/table
        """
        Delete document chunks belonging to certain record ids.

        This method should be used to delete documents from the destination.
        The delete_ids parameter contains a list of record ids - all chunks with a record id in this list should be deleted from the destination.
        All ids belong to the stream and namespace specified in the parameters.
        """
        pass

    def check(self):
        # TODO: Perform initial setup for database-related configurations.
        # 0. Update sqlmodel
        # 1. Establish and verify database connectivity:
        #    a. Ensure the database is accessible. Check for the existence of the specific data_source document table.
        #       Verify if the table's indexing aligns with the configurations specified in the config.
        #       This step is crucial to ensure that the application is interacting with the correct table and that
        #       the table is configured as expected for optimal performance and data integrity.
        #    b. Initialize and store the database connection in an instance variable.
        #       This connection will be used for subsequent database operations, ensuring efficient reuse of the database connection.
        #       Storing it in an instance variable makes it readily accessible throughout the class.

        """
        Check if the indexer is configured correctly. This method should be used to check if the indexer is configured correctly and return an error message if it is not.
        """
        pass

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
