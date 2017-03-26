#!venv/bin/python
import sys
import os
import hashlib
import getpass
import base64
import bcrypt

def new_user(username, password='', hashfunc='BCRYPT', groups=[]):

    if not password:
        # generating random password
        password = base64.b64encode(os.urandom(15)).replace('+', '').replace('=', '').replace('/', '')
        sys.stderr.write('Generating random password: %s\n' % password)

    if hashfunc == 'SHA1':
        salt = base64.b64encode(os.urandom(33))
        hashpass = hashlib.sha1(salt + password).hexdigest()
        print '%s:SHA1:%s$%s:%s' % (username, salt, hashpass, ','.join(groups))
    elif hashfunc == 'SHA256':
        salt = base64.b64encode(os.urandom(33))
        hashpass = hashlib.sha256(salt + password).hexdigest()
        print '%s:SHA256:%s$%s:%s' % (username, salt, hashpass, ','.join(groups))
    elif hashfunc == 'BCRYPT':
        hashpass = bcrypt.hashpw(password, bcrypt.gensalt())
        print '%s:BCRYPT:%s:%s' % (username, hashpass, ','.join(groups))
    elif hashfunc == 'KERBEROS':
        print '%s:KERBEROS:%s:%s' % (username, password, ','.join(groups))
    elif hashfunc == 'LOGIN':
        print '%s:LOGIN::%s' % (username, ','.join(groups))
    else:
        sys.stderr.write("ERROR! Invalid hash function: %s\n" % hashfunc)
        sys.exit(1)


def usage(msg=None):
    if msg:
        sys.stderr.write('%s\n' % msg)

    sys.stderr.write('''\
Create a new entry for the text-password authentication file.

Usage: newuser.py {opts} username

Possible options:
    -p        Read password from command-line 
    -i        Read password from stdin
              (default is to generate a random password)
    -g group  Group for the user to belong to (can be multiple)

    -login           Use Linux user login authentication
    -sha1            Use SHA1 hash function
    -sha256          Use SHA256 hash function
    -bcrypt          Use bcrypt hash function (default)
    -krb krbname     Use kerberos authentication with the following Kerberos credentials


''')

    sys.exit(1)

if __name__ == '__main__':
    username = None
    password = None
    read_pass = False
    read_pass_stdin = False
    hashfunc = 'BCRYPT'
    groups = []
    
    last = None

    for arg in sys.argv[1:]:
        if last == '-krb':
            hashfunc = 'KERBEROS'
            password = arg
            last = None
        elif last == '-g':
            groups.append(arg)
            last = None
        elif arg == '-p':
            read_pass = True
        elif arg == '-i':
            read_pass_stdin = True
        elif arg == '-sha1':
            hashfunc = 'SHA1'
        elif arg == '-sha256':
            hashfunc = 'SHA256'
        elif arg == '-login':
            hashfunc = 'LOGIN'
        elif arg == '-bcrypt':
            hashfunc = 'BCRYPT'
        elif arg in ['-krb', '-g']:
            last = arg
        elif not username:
            username = arg
        else:
            usage('Unknown option: %s\n' % arg)

    if not username:
        usage()

    if hashfunc in ['SHA1', 'SHA256', 'BCRYPT']:
        if read_pass_stdin:
            password = sys.stdin.next().strip()
        elif read_pass:
            password = getpass.getpass("Password: ")

    new_user(username, password, hashfunc, groups)
