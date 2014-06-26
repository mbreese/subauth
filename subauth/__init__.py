import time
import hashlib
import hmac
import sys

import subauth.config

from flask import Flask, request, Response

app = Flask(__name__)

conf = subauth.config.Config('subauth.conf')

auth_backends = []
for method in [x.strip() for x in conf.get('auth','').split(',')]:
    if method == 'kerberos':
        import subauth.auth.krbauth
        auth_backends.append(subauth.auth.krbauth.KerberosAuth(conf.get_prefix('kerberos.')))
    elif method == 'passwd':
        import subauth.auth.passwd
        auth_backends.append(subauth.auth.passwd.PasswdAuth(conf.get_prefix('passwd.')))


def make_digest(message):
    return hmac.new(conf.get('ticket.secret'), message, hashlib.sha1).hexdigest()

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def valid_auth_response(username):
    expires = str(int(time.time() + conf.get('ticket.expires'))) # now + 1 hour
    resp = Response("OK", 200, {'X-%s' % conf.get('ticket.cookie', 'IGVTICKET'): '%s:%s:%s' % (expires, username, make_digest("%s:%s" % (expires,username)))})
    resp.set_cookie(conf.get('ticket.cookie', 'IGVTICKET'), '%s:%s:%s' % (expires, username, make_digest("%s:%s" % (expires,username))))
    return resp

def log(msg):
    if conf.get('verbose'):
        if conf.get('verbose.stdout'):
            sys.stdout.write('%s\n' % msg)
        else:
            sys.stderr.write('%s\n' % msg)

@app.errorhandler(404)
def page_not_found(error):
    print 'page not found: %s' % request.path
    return 'This page does not exist', 404

@app.route("/auth")
def passport():
    '''
    this is the main authenticating function
    
    First, we will look for a signed cookie with an expiration date.
    If that doesn't exist, we will try to authenticate the user using HTTP-BASIC authentication
    '''

    auth_cookie = request.cookies.get(conf.get('ticket.cookie', 'IGVTICKET'))
    if auth_cookie:
        log('cookie: %s' % auth_cookie)
        try:
            ts, username, sig = auth_cookie.split(':')
            if int(ts) > time.time() and make_digest('%s:%s' % (ts, username)) == sig:
                log('cookie valid')
                return valid_auth_response('OK')
        except:
            pass
        log('cookie not valid')
    else:
        log('no cookie')


    if not request.authorization:
        log("no auth... request one")
        return authenticate()
    
    log("Checking: %s/*****************" % (request.authorization.username, ))
    
    for auth in auth_backends:
        log("Trying: %s" % auth)
        try:
            if auth.auth(request.authorization.username, request.authorization.password):
                log("VALID!")
                return valid_auth_response(request.authorization.username)
        except Exception, e:
            log(str(e))
    
    log("no valid authentication :(")
    return authenticate()
