#/usr/bin/env python3

import sys
from passlib.hash import nthash

_help = """
dependencies:
    pip3 install passlib

just type:
    python3 nt_hash.py password

"""

if len(sys.argv) < 2:
    sys.exit(_help)

nt_hash = nthash.hash(sys.argv[1])
print(nt_hash)
