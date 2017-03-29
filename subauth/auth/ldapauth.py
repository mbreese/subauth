'''
Implement kerberos authentication
'''

import subauth
import ldap 

class LDAPAuth(object):
    def __init__(self, config):
        if not config.contains('uri'):
            raise RuntimeError("Missing uri for authentication!")
        if not config.contains('bindDN'):
            raise RuntimeError("Missing bindDN template for authentication!")

	self.uri = config.get('uri')
	self.bindDN = config.get('bindDN')


    def auth(self, username, password):
        dn = self.bindDN % username
        subauth.log('trying user: %s|%s|%s' % (username, self.uri, dn))
        try:
            conn = ldap.initialize(self.uri)
            conn.simple_bind(dn, password)
            if conn.whoami_s():
                subauth.log("Success!")
                return True
        except Exception, e:
            subauth.log('Exception: %s' % e)
            pass
        return False

    def __repr__(self):
        return "LDAP: %s" % self.uri
