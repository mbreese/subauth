#!/usr/bin/env python
import sys
import os
import hashlib
import getpass
import base64

def new_user(username, password='', hashfunc='sha1'):
    salt = base64.b64encode(os.urandom(33))

    if not password:
        # generating random password
        password = base64.b64encode(os.urandom(15)).replace('+', '').replace('=', '').replace('/', '')
        sys.stderr.write('Generating random password: %s\n' % password)

    hashpass = ''
    if hashfunc == 'sha1':
        hashpass = hashlib.sha1(salt + password).hexdigest()

    if not hashpass:
        sys.stderr.write("ERROR! Invalid hash function: %s\n" % hashfunc)
        sys.exit(1)

    print '%s:%s:%s:%s' % (username, hashfunc, salt, hashpass)

def usage(msg=None):
    if msg:
        sys.stderr.write('%s\n' % msg)

    sys.stderr.write('''
Create a new entry for the text-password authentication file.

Usage: passwd.py {opts} username

Possible options:
    -p        Read password from command-line 
    -i        Read password from stdin
              (default is to generate a random password)

    -sha1     Use SHA1 hash function (default)

Currently, only SHA1 hashes are generated, but the format may support other
hash functions in the future.

''')

    sys.exit(1)

if __name__ == '__main__':
    username = None
    password = None
    read_pass = False
    read_pass_stdin = False
    hashfunc = 'sha1'

    for arg in sys.argv[1:]:
        if arg == '-p':
            read_pass = True
        elif arg == '-i':
            read_pass_stdin = True
        elif arg == '-sha1':
            hashfunc = 'sha1'
        elif not username:
            username = arg
        else:
            usage('Unknown option: %s\n' % arg)

    if not username:
        usage()

    if read_pass_stdin:
        password = sys.stdin.next().strip()
    elif read_pass:
        password = getpass.getpass("Password: ")

    new_user(username, password, hashfunc)
