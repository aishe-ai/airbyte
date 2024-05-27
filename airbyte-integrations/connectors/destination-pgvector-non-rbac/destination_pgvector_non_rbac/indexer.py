#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import uuid

import logging

from airbyte_cdk.destinations.vector_db_based.indexer import Indexer

from sqlmodel import Session

from destination_pgvector_non_rbac.data_model import create_document_obj

from destination_pgvector_non_rbac.database import get_engine
from destination_pgvector_non_rbac.config import ConfigModel


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
        # not needed currently
        pass

    def post_sync(self):
        """
        Run after the sync finishes. This method should be used to perform any cleanup operations and can return a list of AirbyteMessages to be logged.
        """
        # not needed currently
        return []

    # explizit indexing not needed, done by postgres and pgvector index
    def index(self, document_chunks, namespace, data_source_name):
        """
        Index a list of document chunks.

        This method should be used to index the documents in the destination.
        All chunks belong to the stream and namespace specified in the parameters.
        """
        with Session(self.db_engine) as session:
            # Check if the data source entry exists and is linked to the current organization
            for raw_document in document_chunks:
                print(raw_document.record)
                pre_formatted = {
                    "uuid": str(uuid.uuid4()),
                    "name": "test",
                    "description": "test descriptionn",
                    "url": "test url",
                    "context_data": raw_document.metadata,
                    "date_source": data_source_name,
                    "embeddings": raw_document.embedding,
                    "page_content": raw_document.page_content,
                    "ingested_at": raw_document.record.emitted_at,
                }
                try:
                    docObject = create_document_obj(pre_formatted)
                    session.add(docObject)
                    session.commit()
                except Exception as error:
                    pre_formatted["embeddings"] = []
                    logging.error(f"Couldnt ingest: {str(pre_formatted)}, because {str(error)}")
                print("-----------------------")

        pass

    def delete(self, delete_ids, namespace, stream):
        """
        Delete document chunks belonging to certain record ids.

        This method should be used to delete documents from the destination.
        The delete_ids parameter contains a list of record ids - all chunks with a record id in this list should be deleted from the destination.
        All ids belong to the stream and namespace specified in the parameters.
        """
        # TODO
        pass

    def check(self):
        """
        Check if the indexer is configured correctly.
        This method should be used to check if the indexer is configured correctly and return an error message if it is not.
        """
        # not needed currently
        pass
