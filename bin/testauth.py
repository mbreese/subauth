#!/usr/bin/env python
import sys
import os
import getpass

import subauth.auth

def usage(msg=None):
    if msg:
        sys.stderr.write('%s\n' % msg)

    sys.stderr.write('''\
Create a new entry for the text-password authentication file.

Usage: testauth.py passwd_file username

''')

    sys.exit(1)

if __name__ == '__main__':
    fname = sys.argv[1]
    username = sys.argv[2]
    password = getpass.getpass("Password: ")

    auth_backend = subauth.auth.PasswdAuth(fname)
    return auth_backend.auth(username, password)
