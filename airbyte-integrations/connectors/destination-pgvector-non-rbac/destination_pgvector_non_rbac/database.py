import os
import logging

from dotenv import load_dotenv

from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import text

from destination_pgvector_non_rbac.data_model import create_document_obj

load_dotenv()


def migrate(config):
    database_config = config["database"]
    engine = get_engine(database_config)

    # Create tables
    with engine.begin() as connection:  # Use 'begin' to auto-commit
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        tables_to_create = SQLModel.metadata.sorted_tables
        SQLModel.metadata.create_all(connection, tables=tables_to_create)

    logging.info("Created all needed tables")

    # Check for test or dev environment
    if os.environ.get("ENVIRONMENT") in ["test", "dev"]:
        create_test_data(engine)

    return engine


def create_test_data(engine):
    with Session(engine) as session:
        test_document = create_document_obj()
        session.add(test_document)
        session.commit()

        logging.info("Test data created")

        return test_document


def get_config_value(config, key, default=None):
    if isinstance(config, dict):
        return config.get(key, default)
    else:
        if key == "password":
            return getattr(config, key, default).get_secret_value()
        else:
            return getattr(config, key, default)


def get_engine(database_config):
    try:
        database_url = (
            f"postgresql://"
            f"{get_config_value(database_config, 'username', 'default_username')}:"
            f"{get_config_value(database_config, 'password', 'default_password')}@"
            f"{get_config_value(database_config, 'host', 'default_host')}:{get_config_value(database_config, 'port', 'default_port')}/"
            f"{get_config_value(database_config, 'database', 'default_database')}"
        )
        engine = create_engine(database_url)
        logging.info("Got db connection")
        return engine
    except Exception as e:
        logging.error(f"Failed to get db connection: {e}")
        # Optionally, re-raise the exception if you want to propagate it
        raise
