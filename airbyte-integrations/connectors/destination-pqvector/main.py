#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from destination_pqvector import DestinationPqvector

if __name__ == "__main__":
    DestinationPqvector().run(sys.argv[1:])
