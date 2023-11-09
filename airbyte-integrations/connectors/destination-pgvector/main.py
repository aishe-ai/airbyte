#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from destination_pgvector import DestinationPgvector

if __name__ == "__main__":
    DestinationPgvector().run(sys.argv[1:])
