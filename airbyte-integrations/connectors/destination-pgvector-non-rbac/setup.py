#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = [
    # use requirements text file
]

TEST_REQUIREMENTS = ["pytest~=6.2"]

setup(
    name="destination_pgvector_non_rbac",
    description="Non rbac destination implementation for Pgvector.",
    author="Airbyte",
    author_email="contact@airbyte.io",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
