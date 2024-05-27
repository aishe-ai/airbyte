import pytest
import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel
from sqlalchemy.exc import OperationalError

# Load environment variables from the root .env file
root_dir = os.path.dirname(os.path.dirname(__file__))  # Get the root directory
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path)

# Import your SQLModel classes from the data_model module
from destination_pgvector_non_rbac.data_model import *  # This assumes your SQLModel classes are defined in data_model.py
from destination_pgvector_non_rbac.database import migrate


# use check functionality for db connection


# Define the pytest fixture for setting up the test database
@pytest.fixture(scope="module")
def setup_database():
    # # Set up the test database and create tables
    # engine = migrate()

    # # Perform any additional setup actions required by the Airbyte destination
    # yield engine

    # # Clean up the test database
    # SQLModel.metadata.drop_all(engine)
    pass


# Define the test function to validate the destination can connect and the schema is correct
def test_destination_connection(setup_database):
    # try:
    #     # Attempt to connect to the database
    #     with Session(setup_database) as session:
    #         # Perform a simple query, like checking for the number of tables in the public schema
    #         result = session.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public';")
    #         count = result.scalar()
    #         assert count > 0, "No tables found in the public schema"

    #         # Perform any additional destination-specific tests required by the Airbyte destination

    # except OperationalError as exc:
    #     pytest.fail(f"Could not connect to the database: {exc}")
    pass
