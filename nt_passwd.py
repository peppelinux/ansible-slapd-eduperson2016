#/usr/bin/env python3

import sys
import hashlib,binascii

_help = """
just type:
    python3 nt_hash.py password

"""

if len(sys.argv) < 2:
    sys.exit(_help)

hash = hashlib.new('md4', sys.argv[1].encode('utf-16le')).digest()
print(str(binascii.hexlify(hash), encoding='ascii'))
