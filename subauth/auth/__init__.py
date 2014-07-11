'''
Implement authentication using an formated text file.

File format:

username:function:salt:func(salt+password)

Supported functions: sha1

'''

import hashlib
import os

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
                pass_hash = cols[2]

                self.users[username] = (hash_func, pass_hash)

    def auth(self, username, password):
        if not username in self.users:
            return False

        hash_func, pass_hash = self.users[username]

        if hash_func.startswith('{SHA1}'):
            test = ''
            pass_salt = hash_func[6:]
            test = hashlib.sha1(pass_salt + password).hexdigest()
            return secure_compare(test, pass_hash)
        elif hash_func.startswith('{KERBEROS}'):
            return self._kerberos.auth(hash_func[10:], password)

        return False

    def __repr__(self):
        return "Passwd file: %s" % self.filename


def secure_compare(one, two):
    same = True
    for x,y in zip(one, two):
        if x != y:
            same = False
    if len(one) != len(two):
        return False
    return same

