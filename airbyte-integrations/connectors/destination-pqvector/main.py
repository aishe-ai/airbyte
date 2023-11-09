#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from destination_pgvector import Destinationpgvector

if __name__ == "__main__":
    Destinationpgvector().run(sys.argv[1:])
