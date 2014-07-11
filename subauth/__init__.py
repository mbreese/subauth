import time
import hashlib
import hmac
import sys

import subauth.config
import subauth.auth.passwd

from flask import Flask, request, Response

app = Flask(__name__)

conf = subauth.config.Config('subauth.conf')

auth_backend = subauth.auth.passwd.PasswdAuth(conf.get_prefix('passwd.'))

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
    resp = Response("OK", 200, {'X-%s' % conf.get('ticket.cookie', 'SUBAUTH'): '%s:%s:%s' % (expires, username, make_digest("%s:%s" % (expires,username)))})
    resp.set_cookie(conf.get('ticket.cookie', 'SUBAUTH'), '%s:%s:%s' % (expires, username, make_digest("%s:%s" % (expires,username))))
    return resp

def log(msg):
    if conf.get('verbose'):
        sys.stderr.write('%s\n' % msg)

@app.errorhandler(404)
def page_not_found(error):
    print 'page not found: %s' % request.path
    return 'This page does not exist', 404

# @app.route("/reload")
# def reload():
#     auth_backend.loadfile()
#     return "OK"

@app.route("/auth")
def passport():
    '''
    this is the main authenticating function
    
    First, we will look for a signed cookie with an expiration date.
    If that doesn't exist, we will try to authenticate the user using HTTP-BASIC authentication
    '''
    log('original uri: %s' % request.args.get('p'))

    auth_cookie = request.cookies.get(conf.get('ticket.cookie', 'IGVTICKET'))
    if auth_cookie:
        log('cookie: %s' % auth_cookie)
        try:
            ts, username, sig = auth_cookie.split(':')
            if int(ts) > time.time() and make_digest('%s:%s' % (ts, username)) == sig:
                log('cookie valid')
                return valid_auth_response(username)
        except:
            pass
        log('cookie not valid')
    else:
        log('no cookie')


    if not request.authorization:
        log("no auth... request one")
        return authenticate()
    
    log("Checking: %s/*****************" % (request.authorization.username,))

    try:
        if auth_backend.auth(request.authorization.username, request.authorization.password):
            return valid_auth_response(request.authorization.username)
    except Exception, e:
        log(str(e))

    log("no valid authentication :(")
    return authenticate()
