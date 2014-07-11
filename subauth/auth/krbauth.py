'''
Implement kerberos authentication
'''

import subauth
import kerberos

class KerberosAuth(object):
    def __init__(self, config):
        if not config.contains('realm'):
            raise RuntimeError("Missing Kerberos Realm for authentication!")

	self.realm = config.get('realm')
	self.domain = config.get('domain', '')


    def auth(self, username, password):
        subauth.log('trying user: %s|%s|%s' % (username, self.domain, self.realm))
        try:
            if kerberos.checkPassword(username, password, self.domain, self.realm):
                subauth.log("Success!")
                return True
        except Exception, e:
            subauth.log('Exception: %s' % e)
            pass
        return False

    def __repr__(self):
        return "Kerberos: %s" % self.realm
