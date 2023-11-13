import pytest
import os
import logging

from dotenv import load_dotenv
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.exc import OperationalError

# Load environment variables from the root .env file
root_dir = os.path.dirname(os.path.dirname(__file__))  # Get the root directory
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path)

# Import your SQLModel classes from the data_model module
from destination_pgvector.data_model import *  # This assumes your SQLModel classes are defined in data_model.py


# Define the pytest fixture for setting up the test database
@pytest.fixture(scope="module")
def setup_database():
    # Construct the database URL using environment variables
    postgres_user = os.environ.get("POSTGRES_USER")
    postgres_password = os.environ.get("POSTGRES_PASSWORD")
    postgres_database = os.environ.get("POSTGRES_DATABASE")
    postgres_host = os.environ.get("POSTGRES_HOST")

    if not all([postgres_user, postgres_password, postgres_database, postgres_host]):
        pytest.fail("One or more required environment variables are not set.")

    test_database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}/{postgres_database}"

    # Set up the test database and create tables
    engine = create_engine(test_database_url)
    SQLModel.metadata.create_all(engine)

    # Perform any additional setup actions required by the Airbyte destination

    yield engine

    # Clean up the test database
    SQLModel.metadata.drop_all(engine)


# Define the test function to validate the destination can connect and the schema is correct
def test_destination_connection(setup_database):
    try:
        # Attempt to connect to the database
        with Session(setup_database) as session:
            # Perform a simple query, like checking for the number of tables in the public schema
            result = session.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public';")
            count = result.scalar()
            assert count > 0, "No tables found in the public schema"

            # Perform any additional destination-specific tests required by the Airbyte destination

    except OperationalError as exc:
        pytest.fail(f"Could not connect to the database: {exc}")


# # Run the tests
# if __name__ == "__main__":
#     pytest.main(["-svv", os.path.abspath(__file__)])
