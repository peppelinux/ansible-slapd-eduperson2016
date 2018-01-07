#!/usr/bin/env python3

#~ Copyright 2017 Giuseppe De Marco <giuseppe.demarco@unical.it>
#~ 
#~ Permission is hereby granted, free of charge, to any person obtaining a 
#~ copy of this software and associated documentation files (the "Software"), 
#~ to deal in the Software without restriction, including without limitation 
#~ the rights to use, copy, modify, merge, publish, distribute, sublicense, 
#~ and/or sell copies of the Software, and to permit persons to whom the Software 
#~ is furnished to do so, subject to the following conditions:
#~ 
#~ The above copyright notice and this permission notice shall be included 
#~ in all copies or substantial portions of the Software.
#~ 
#~ THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
#~ OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
#~ FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
#~ THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
#~ LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
#~ FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
#~ DEALINGS IN THE SOFTWARE.

import binascii
import hashlib
import os
import sys
from base64 import urlsafe_b64encode as encode
from base64 import urlsafe_b64decode as decode

def sshaSplit(ssha_password, debug=0):
    payload = decode(ssha_password)[6:-4]
    salt = decode(ssha_password)[-4:]
    if debug: 
        hex_salt = binascii.hexlify(salt)
        hex_digest = binascii.hexlify(payload)
        print('\n[sshaSplit debug]\n\t'
              'ssha_password: {} \n\tsalt: {} \n\tpayload: {}\n'.format(ssha_password, 
                                                           str(hex_salt, 'ascii'), 
                                                           str(hex_digest, 'ascii')))
    return {'salt': salt, 'payload': payload, 'ssha': ssha_password}

def sshaEncoder(password, salt=None, debug=0):
    """[0,6][payload][-4:]"""
    if salt: salt = binascii.unhexlify(salt)
    else: salt = os.urandom(4)
    enc_password = bytes(password, encoding='ascii')
    h = hashlib.sha1(enc_password)
    h.update(salt)
    if debug > 1:
        hex_salt = binascii.hexlify(salt)
        hex_digest = h.hexdigest()
        print('[sshaEncode debug]\n \tsalt: {} \n\thex_payload: {}\n'
                        '\tpassword: {}'.format(str(hex_salt, 'ascii'), hex_digest, password))
    return {'salt': salt, 'digest': h.digest(), 'password': password}

def hashPassword(password, salt=None, debug=0):
    sshaenc = sshaEncoder(password, salt, debug)
    b64digest_salt = encode(sshaenc['digest']+sshaenc['salt'])
    byte_res = b"{SSHA}" + b64digest_salt
    return str(byte_res, 'ascii')

def checkPassword(password, ssha_password, debug=0):
    assert ssha_password.startswith('{SSHA}')
    # extract payload and salt
    sshasplit = sshaSplit(ssha_password, debug)
    payload, salt = sshasplit['payload'], sshasplit['salt']
    
    ssha_hash = hashPassword(password, binascii.hexlify(salt))
    
    if debug > 1: 
        print('[checkPassword debug]\n \tssha_password:    {}\n\t'
              'created_password: {}'.format(ssha_password, ssha_hash))
    if debug > 2: 
        print('\tsalt: {}\n\tpassword: {}'.format(str(binascii.hexlify(salt), 'ascii'), 
                                      password))
    if ssha_hash == ssha_password: 
        return True

if __name__ == '__main__':  
    import argparse
    parser = argparse.ArgumentParser(description='Usage:\n'
                                     'python ssha.py '
                                     '-p Password'
                                     '[-c SSHA hash to check]')
    parser.add_argument('-p', required=True, help="Password to encode in {SSHA}")
    parser.add_argument('-s', required=False, 
                        help="Salt, 4 bytes in hex format, example \"fooo\": -s 666f6f6f")    
    parser.add_argument('-c', required=False, help="{SSHA} hash to check")
    parser.add_argument('-b', required=False, action='store_true', help="if {SSHA} hash is in base64 format")
    parser.add_argument('-d', required=False, type=int, default=0, help="Debug level")

    args = parser.parse_args()
    password = args.p
    if args.c:
        if args.b: shahash = str(decode(args.c), 'ascii')
        else: shahash = args.c
        is_valid = checkPassword(password, shahash, args.d) == True
        print('\n{{SSHA}} Check is valid: {}\n'.format(is_valid))
    else:
        hash_password=hashPassword(password, args.s, args.d)
        print(hash_password,'\n')
