#!/usr/bin/env python
import sys
import os
import hashlib
import getpass
import base64

def new_user(username, password='', hashfunc='sha1'):

    if not password:
        # generating random password
        password = base64.b64encode(os.urandom(15)).replace('+', '').replace('=', '').replace('/', '')
        sys.stderr.write('Generating random password: %s\n' % password)

    if hashfunc == 'SHA1':
        salt = base64.b64encode(os.urandom(33))
        hashpass = hashlib.sha1(salt + password).hexdigest()
        print '%s:{SHA1}%s:%s:' % (username, salt, hashpass)
    elif hashfunc == 'KERBEROS':
        print '%s:{KERBEROS}%s::' % (username, password)
    else:
        sys.stderr.write("ERROR! Invalid hash function: %s\n" % hashfunc)
        sys.exit(1)


def usage(msg=None):
    if msg:
        sys.stderr.write('%s\n' % msg)

    sys.stderr.write('''\
Create a new entry for the text-password authentication file.

Usage: passwd.py {opts} username

Possible options:
    -p        Read password from command-line 
    -i        Read password from stdin
              (default is to generate a random password)

    -sha1            Use SHA1 hash function (default)
    -krb krbname     Use kerberos authentication with the following Kerberos credentials

Currently, only SHA1 hashes are generated, but the format may support other
hash functions in the future.

''')

    sys.exit(1)

if __name__ == '__main__':
    username = None
    password = None
    read_pass = False
    read_pass_stdin = False
    hashfunc = 'SHA1'
    
    last = None

    for arg in sys.argv[1:]:
        if last == '-krb':
            password = arg
            last = None
        elif arg == '-p':
            read_pass = True
        elif arg == '-i':
            read_pass_stdin = True
        elif arg == '-sha1':
            hashfunc = 'SHA1'
        elif arg == '-krb':
            hashfunc = 'KERBEROS'
            last = arg
        elif not username:
            username = arg
        else:
            usage('Unknown option: %s\n' % arg)

    if not username:
        usage()

    if hashfunc == 'SHA1':
        if read_pass_stdin:
            password = sys.stdin.next().strip()
        elif read_pass:
            password = getpass.getpass("Password: ")

    new_user(username, password, hashfunc)
