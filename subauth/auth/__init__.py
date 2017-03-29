'''
Implement authentication using an formated text file.

File format:

username:{function}:hashed_password

Supported functions: sha1, sha256, bcrypt, kerberos, linux user login (login)

SHA1, SHA256 include a salt in their hashed_password field: salt$hash

'''

import os
import stat
import time
import hashlib

import bcrypt
import loginauth

class PasswdAuth(object):
    def __init__(self, config):
        if not config.contains('passwd.filename') or not os.path.exists(config.get('passwd.filename')):
            config.dump()
            raise RuntimeError("Missing filename for passwd authentication!")

        self.filename = config.get('passwd.filename')
        self.loadfile()

        if config.contains('ldap.uri'):
            import subauth.auth.ldapauth
            self._ldap = subauth.auth.ldapauth.LDAPAuth(config.get_prefix('ldap.'))
        else:
            self._ldap = None

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

                cols = line.strip().split(':')
                username = cols[0]
                hash_func = cols[1]
                if len(cols) > 2:
                    pass_hash = cols[2]
                else:
                    pass_hash = ''
                if len(cols) > 3:
                    groups = cols[3]
                else:
                    groups = ''

                self.users[username] = (hash_func, pass_hash, groups)

    def change_password(self, username, password):
        if self.users[username][0] not in ['SHA1', 'SHA256', 'BCRYPT']:
            # Only allowed to change these passwords.
            return False

        wait_count = 0
        while wait_count < 10 and os.path.exists('%s.tmp' % self.filename):
           wait_count += 1
           time.sleep(1) 

        if wait_count >= 10:
            return False

        out = open('%s.tmp' % self.filename, 'w')
        found = False
        for uname in self.users:
            if uname != username:
                out.write('%s:%s\n' % (uname, ':'.join(self.users[uname])))
            else:
                found = True
                hash_func, pass_hash, groups = self.users[username]
                # All of these will upgrade to bcrypt based passwords
                out.write('%s:BCRYPT:%s:%s\n' % (username, bcrypt.hashpw(password, bcrypt.gensalt()), groups))

        out.close()
	os.chmod('%s.tmp' % self.filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)
        if found:
            os.rename('%s.tmp' % self.filename, self.filename)
            self.loadfile()
            return True
        else:
            os.unlink('%s.tmp' % self.filename)
            return False

    def auth(self, username, password):
        if not username in self.users:
            return False

        hash_func, pass_hash, groups = self.users[username]

        if hash_func == 'SHA1':
            salt, pass_hash2 = pass_hash.split('$')
            return auth_sha1(password, salt, pass_hash2)
        elif hash_func == 'SHA256':
            salt, pass_hash2 = pass_hash.split('$')
            return auth_sha256(password, salt, pass_hash2)
        elif hash_func == 'BCRYPT':
            return auth_bcrypt(password, pass_hash)
        elif hash_func == 'LOGIN':
            return auth_login(username, password)
        elif hash_func == 'LDAP':
            return self._ldap.auth(username, password)
        elif hash_func == 'KERBEROS':
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
    return bcrypt.hashpw(test_pass, pass_hash) == pass_hash


def auth_login(username, password):
    return loginauth.auth(username, password)


def secure_compare(one, two):
    same = True
    for x,y in zip(one, two):
        if x != y:
            same = False
    if len(one) != len(two):
        return False
    return same

