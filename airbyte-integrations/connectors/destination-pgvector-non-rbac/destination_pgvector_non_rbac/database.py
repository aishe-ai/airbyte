import os
import logging

from sqlmodel import create_engine, SQLModel, Session, select, inspect
from sqlalchemy import text

from pydantic import ValidationError


from destination_pgvector_non_rbac.data_model import create_mock_organization, Organization, Member
from destination_pgvector_non_rbac.config import pgvector_indexes


def migrate(config):
    database_config = config["database"]
    engine = get_engine(database_config)

    # Create tables
    with engine.begin() as connection:  # Use 'begin' to auto-commit
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        # Create all tables, except the document table template
        tables_to_create = [
            table for table in SQLModel.metadata.sorted_tables if table.name not in ["documenttabletemplate", "basedocumenttabletemplate"]
        ]
        SQLModel.metadata.create_all(connection, tables=tables_to_create)

    logging.info("Created all needed tables")

    # Check for test or dev environment
    if os.environ.get("ENVIRONMENT") in ["test", "dev"]:
        get_test_data(engine)

    return engine


def get_test_data(engine):
    # Read environment variables
    test_org_name = os.environ.get("TEST_ORG_NAME", "Test Organization")
    test_member_name = os.environ.get("TEST_MEMBER_NAME", "Test Member")
    test_member_email = os.environ.get("TEST_MEMBER_EMAIL", "testmember@example.com")

    with Session(engine) as session:
        # Query for the test organization
        query_org = select(Organization).where(Organization.name == test_org_name)
        test_org = session.exec(query_org).first()

        # Query for the test member
        query_member = select(Member).where(Member.email == test_member_email)
        test_member = session.exec(query_member).first()

        # If test data not found, create and store it
        if not test_org or not test_member:
            test_org, test_member = create_test_data(engine, test_org_name, test_member_name, test_member_email)

        return test_org, test_member


def create_test_data(engine, test_org_name, test_member_name, test_member_email):
    with Session(engine) as session:
        test_org, test_member = create_mock_organization(
            org_name=test_org_name, member_name=test_member_name, member_email=test_member_email
        )
        session.add(test_org)
        session.commit()

        session.add(test_member)
        session.commit()

        logging.info("Test data created")

        return test_org, test_member


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
            f"{get_config_value(database_config, 'host', 'default_host')}/"
            f"{get_config_value(database_config, 'database', 'default_database')}"
        )
        engine = create_engine(database_url)
        logging.info("Got db connection")
        return engine
    except Exception as e:
        logging.error(f"Failed to get db connection: {e}")
        # Optionally, re-raise the exception if you want to propagate it
        raise
