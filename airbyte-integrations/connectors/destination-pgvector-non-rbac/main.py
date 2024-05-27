#
# Copyright (c) 2024 Airbyte, Inc., all rights reserved.
#


import sys

from destination_pgvector_non_rbac import DestinationPgvectorNonRbac

if __name__ == "__main__":
    destination = DestinationPgvectorNonRbac()
    destination.run(sys.argv[1:])
