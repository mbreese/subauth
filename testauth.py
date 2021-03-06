#!venv/bin/python
import sys
import os
import getpass

import subauth.auth

def usage(msg=None):
    if msg:
        sys.stderr.write('%s\n' % msg)

    sys.stderr.write('''\
Create a new entry for the text-password authentication file.

Usage: testauth.py username

''')

    sys.exit(1)

if __name__ == '__main__':
    conf = subauth.config.Config('subauth.conf')

    username = sys.argv[1]
    password = getpass.getpass("Password: ")

    auth_backend = subauth.auth.PasswdAuth(conf)
    if auth_backend.auth(username, password):
        print "OK"
    else:
        print "ERROR"
        sys.exit(1)
