import logging

from sqlmodel import create_engine, SQLModel
from sqlalchemy import text


def get_engine(database_config):
    test_database_url = (
        f"postgresql://{database_config['username']}:{database_config['password']}@{database_config['host']}/{database_config['database']}"
    )

    engine = create_engine(test_database_url)
    logging.info("Got db connection")
    return engine


def migrate(config):
    database_config = config["database"]
    engine = get_engine(database_config)

    # Create tables
    with engine.begin() as connection:  # Use 'begin' to auto-commit
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        SQLModel.metadata.create_all(connection)

    logging.info("Created all needed tables")

    return engine
