'''
Implement authentication using an formated text file.

File format:

username:function:salt:func(salt+password)

Supported functions: sha1

'''

import subauth
import subauth.auth
import hashlib
import os

class PasswdAuth(subauth.auth.Auth):
    def __init__(self, config):
        if not config.contains('filename') or not os.path.exists(config.get('filename')):
            raise RuntimeError("Missing filename for passwd authentication!")

        subauth.auth.Auth.__init__(self, config)


    def auth(self, username, password):
        pass_hash = ''
        pass_salt = ''
        hash_func = ''
        with open(self.config.get('filename')) as f:
            for line in f:
                if not line or line.strip() == '' or line[0] == '#' or ':' not in line:
                    continue

                cols = line.split(':')
                if cols[0] == username:
                    hash_func = cols[1]
                    pass_salt = cols[2]
                    pass_hash = cols[3]


        if not hash_func or not pass_hash or not pass_salt:
            return False

        subauth.log('found: %s/%s/%s' % (hash_func, pass_salt, pass_hash))
        test = ''
        if hash_func == 'sha1':
            test = hashlib.sha1(pass_salt + password).hexdigest()

        if not test:
            return False

        subauth.log('comparing %s ? %s' % (test, secure_compare(test, pass_hash)))

        return secure_compare(test, pass_hash)

    def __repr__(self):
        return "Passwd file: %s" % self.config.get('filename')

def secure_compare(one, two):
    same = True
    for x,y in zip(one, two):
        if x != y:
            same = False
    return same

