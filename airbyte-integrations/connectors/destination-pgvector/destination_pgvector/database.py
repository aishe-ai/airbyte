import os
import logging

from dotenv import load_dotenv

from sqlmodel import create_engine, SQLModel
from sqlalchemy import text


# Load environment variables from the root .env file
root_dir = os.path.dirname(os.path.dirname(__file__))  # Get the root directory
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path)


def get_engine():
    # Construct the database URL using environment variables
    postgres_user = os.environ.get("POSTGRES_USER")
    postgres_password = os.environ.get("POSTGRES_PASSWORD")
    postgres_database = os.environ.get("POSTGRES_DATABASE")
    postgres_host = os.environ.get("POSTGRES_HOST")

    if not all([postgres_user, postgres_password, postgres_database, postgres_host]):
        logging.error("One or more required environment variables are not set.")

    test_database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}/{postgres_database}"

    engine = create_engine(test_database_url)
    logging.info("Got db connection")
    return engine


def migrate():
    engine = get_engine()

    # Create tables
    with engine.begin() as connection:  # Use 'begin' to auto-commit
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        SQLModel.metadata.create_all(connection)

    logging.info("Created all needed tables")

    return engine
