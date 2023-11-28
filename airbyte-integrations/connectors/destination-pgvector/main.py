#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys
from dotenv import load_dotenv

from destination_pgvector import DestinationPgvector

load_dotenv()  # This loads the environment variables from a .env file

if __name__ == "__main__":
    DestinationPgvector().run(sys.argv[1:])
