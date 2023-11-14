#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from typing import Any, Iterable, Mapping

from airbyte_cdk import AirbyteLogger
from airbyte_cdk.destinations import Destination
from airbyte_cdk.models import (
    AirbyteConnectionStatus,
    AirbyteMessage,
    ConfiguredAirbyteCatalog,
    ConnectorSpecification,
    DestinationSyncMode,
    Status,
    Type,
)
from airbyte_cdk.destinations.vector_db_based.embedder import Embedder, create_from_config


from sqlmodel import Session
from sqlalchemy import text

from uuid import uuid4

from langchain.embeddings import OpenAIEmbeddings


from destination_pgvector.config import ConfigModel
from destination_pgvector.database import migrate
from destination_pgvector.writer import PGVectorWriter
from destination_pgvector.data_model import *

BATCH_SIZE = 32


class DestinationPgvector(Destination):
    def _init(self, config: ConfigModel):
        self.embedder = create_from_config(config.embedding, config.processing)

    def write(
        self, config: Mapping[str, Any], configured_catalog: ConfiguredAirbyteCatalog, input_messages: Iterable[AirbyteMessage]
    ) -> Iterable[AirbyteMessage]:
        """
        TODO
        Reads the input stream of messages, config, and catalog to write data to the destination.

        This method returns an iterable (typically a generator of AirbyteMessages via yield) containing state messages received
        in the input message stream. Outputting a state message means that every AirbyteRecordMessage which came before it has been
        successfully persisted to the destination. This is used to ensure fault tolerance in the case that a sync fails before fully completing,
        then the source is given the last state message output from this method as the starting point of the next sync.

        :param config: dict of JSON configuration matching the configuration declared in spec.json
        :param configured_catalog: The Configured Catalog describing the schema of the data being received and how it should be persisted in the
                                    destination
        :param input_messages: The stream of input messages received from the source
        :return: Iterable of AirbyteStateMessages wrapped in AirbyteMessage structs
        """

        config_model = ConfigModel.parse_obj(config)
        self._init(config_model)
        writer = PGVectorWriter(config_model.processing, None, self.embedder, batch_size=BATCH_SIZE)
        yield from writer.write(configured_catalog, input_messages)

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

    def insert_record(self, message: AirbyteMessage, engine):
        pass
        # You would implement your insert logic here using SQLModel and switch cases
        # with Session(engine) as session:
        #     # Map the record to your SQLModel class (e.g., YourRecordModel)
        #     record = YourRecordModel(**message.record.data)  # Transform the Airbyte record to your SQLModel instance

        #     # Add the record instance to the session and commit
        #     # Ensure your model instances match with your table structures and columns
        #     try:
        #         session.add(record)
        #         session.commit()
        #     except Exception as e:
        #         session.rollback()  # Rollback if any error occurs
        #         # Here you should handle the error (e.g., log to AirbyteLogger, raise a specific exception, etc.)

    # Note: Make sure the models in your_data_models.py are defined correctly to match the schema of the destination tables.
    # This code does not handle specific schema issues, dependencies between tables, or advanced use cases like upserting.

    def check(self, logger: AirbyteLogger, config: Mapping[str, Any]) -> AirbyteConnectionStatus:
        """
        Tests if the input configuration can be used to successfully connect to the destination with the needed permissions
            e.g: if a provided API token or password can be used to connect and write to the destination.

        :param logger: Logging object to display debug/info/error to the logs
            (logs will not be accessible via airbyte UI if they are not passed to this logger)
        :param config: Json object containing the configuration of this destination, content of this json is as specified in
        the properties of the spec.json file

        :return: AirbyteConnectionStatus indicating a Success or Failure
        """
        try:
            # db checks
            engine = migrate(config)

            # Try to connect to the database and check for vector extension
            with engine.connect() as conn:
                # Check the existence of the vector extension
                result = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
                if result.rowcount == 0:
                    raise RuntimeError("The 'vector' extension is not installed in the PostgreSQL database.")

            # If the connection is successful and the 'vector' extension exists, return success status
            logger.info("Successfully connected to the PostgreSQL database with the 'vector' extension installed.")

            # embedding checks
            self._init(ConfigModel.parse_obj(config))
            embedder_error = self.embedder.check()
            errors = [error for error in [embedder_error] if error is not None]
            if len(errors) > 0:
                return AirbyteConnectionStatus(status=Status.FAILED, message="\n".join(errors))
            else:
                return AirbyteConnectionStatus(status=Status.SUCCEEDED)

        except Exception as e:
            # If there was an error during the connection attempt, log the error and return failure status
            logger.error(f"An exception occurred while trying to connect to the PostgreSQL database: {e}")
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {repr(e)}")

    def spec(self, *args: Any, **kwargs: Any) -> ConnectorSpecification:
        return ConnectorSpecification(
            # documentationUrl="",
            documentationUrl="https://docs.airbyte.com/integrations/destinations/pgvector",
            supportsIncremental=True,
            # supported_destination_sync_modes=[DestinationSyncMode.overwrite, DestinationSyncMode.append, DestinationSyncMode.append_dedup],
            supported_destination_sync_modes=[DestinationSyncMode.overwrite],
            connectionSpecification=ConfigModel.schema(),
        )
