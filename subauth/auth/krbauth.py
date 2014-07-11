'''
Implement kerberos authentication
'''

import subauth
import subauth.auth
import kerberos

class KerberosAuth(subauth.auth.Auth):
    def __init__(self, config):
        if not config.contains('realm'):
            raise RuntimeError("Missing Kerberos Realm for authentication!")

        subauth.auth.Auth.__init__(self, config)

    def auth(self, username, password):
        subauth.log('trying user: %s|%s|%s' % (username, self.config.get('domain',''), self.config.get('realm')))
        try:
            if kerberos.checkPassword(username, password, self.config.get('domain',''), self.config.get('realm')):
                subauth.log("Success!")
                return True
        except Exception, e:
            subauth.log('Exception: %s' % e)
            pass
        return False

    def __repr__(self):
        return "Kerberos: %s" % self.config.get('realm')