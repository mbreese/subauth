'''
Implement authentication using an formated text file.

File format:

username:{function}:hashed_password

Supported functions: sha1, sha256, bcrypt, kerberos, pam

SHA1, SHA256 include a salt in their hashed_password field: salt$hash

'''

import hashlib
import os
import bcrypt
import pam

class PasswdAuth(object):
    def __init__(self, config):
        if not config.contains('filename') or not os.path.exists(config.get('filename')):
            raise RuntimeError("Missing filename for passwd authentication!")

        self.filename = config.get('filename')
        self.loadfile()

        if config.contains('kerberos.realm'):
            import subauth.auth.krbauth
            self._kerberos = subauth.auth.krbauth.KerberosAuth(config.get_prefix('kerberos.'))
        else:
            self._kerberos = None

    def loadfile(self):
        self.users = {}
        with open(self.filename) as f:
            for line in f:
                if not line or line.strip() == '' or line[0] == '#' or ':' not in line:
                    continue

                cols = line.split(':')
                username = cols[0]
                hash_func = cols[1]
                if len(cols) > 2:
                    pass_hash = cols[2]
                else:
                    pass_hash = ''

                self.users[username] = (hash_func, pass_hash)

    def auth(self, username, password):
        if not username in self.users:
            return False

        hash_func, pass_hash = self.users[username]

        if hash_func.startswith('{SHA1}'):
            salt, pass_hash2 = pass_hash.split('$')
            return auth_sha1(password, salt, pass_hash2)
        elif hash_func.startswith('{SHA256}'):
            salt, pass_hash2 = pass_hash.split('$')
            return auth_sha256(password, salt, pass_hash2)
        elif hash_func.startswith('{BCRYPT}'):
            return auth_bcrypt(password, pass_hash)
        elif hash_func.startswith('{PAM}'):
            return self.auth_pam(username, password)
        elif hash_func.startswith('{KERBEROS}'):
            return self._kerberos.auth(pass_hash, password)

        return False

    def __repr__(self):
        return "Passwd file: %s" % self.filename


def auth_sha1(test_pass, salt, pass_hash):
    test = hashlib.sha1(salt + test_pass).hexdigest()
    return secure_compare(test, pass_hash)


def auth_sha256(test_pass, salt, pass_hash):
    test = hashlib.sha256(salt + test_pass).hexdigest()
    return secure_compare(test, pass_hash)


def auth_bcrypt(test_pass, pass_hash):
    return bcrypt.hashpw(test_pass, pass_hash)


def auth_pam(username, password):
    p = pam.pam()
    return p.authenticate(username, password)


def secure_compare(one, two):
    same = True
    for x,y in zip(one, two):
        if x != y:
            same = False
    if len(one) != len(two):
        return False
    return same

