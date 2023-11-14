#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = [
    "airbyte-cdk",
    "langchain",
    "sqlmodel",
    "pydantic",
    "psycopg2-binary",
    "python-dotenv",
    "pytest",
    "pydantic[email]",
    "sqlalchemy<2.0",
    "pgvector",
    "airbyte-cdk[vector-db-based]==0.51.41",
]

TEST_REQUIREMENTS = ["pytest~=6.2"]

setup(
    name="destination_pgvector",
    description="Destination implementation for Pgvector.",
    author="Airbyte",
    author_email="contact@airbyte.io",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
