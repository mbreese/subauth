import time
import hashlib
import hmac
import sys

import subauth.config
import subauth.auth

from flask import Flask, request, Response

app = Flask(__name__)
conf = subauth.config.Config('subauth.conf')

auth_backend = subauth.auth.PasswdAuth(conf)

def make_digest(message):
    return hmac.new(conf.get('ticket.secret'), message, hashlib.sha256).hexdigest()

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def require_secure():
    """Sends a 403 Forbidden response that"""
    return Response('Could not verify your access level for that URL.\n', 403, {})

def valid_auth_response(username, redirect=False):
    expires = str(int(time.time() + conf.get('ticket.expires'))) # now + 1 hour

    resp = None

    if redirect:
        nsredirect = request.cookies.get('NSREDIRECT')
        if nsredirect:
            resp = Response('302 Moved Temporarily', 302, {'Location': nsredirect})
            resp.set_cookie('NSREDIRECT','', expires='0', domain=conf.get('ticket.domain', None))

    if not resp:
        resp = Response("<html><body>OK<br/><a href=\"/auth/passwd\">Change password</a><br/><br/><a href=\"/auth/signout\">Sign out</a></body></html>", 200, {'X-%s' % conf.get('ticket.cookie', 'SUBAUTHCOOKIE'): '%s:%s:%s' % (expires, username, make_digest("%s:%s" % (expires,username)))})

    resp.set_cookie(conf.get('ticket.cookie', 'SUBAUTHCOOKIE'), '%s:%s:%s' % (expires, username, make_digest("%s:%s" % (expires,username))), domain=conf.get('ticket.domain', None))
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

@app.route("/auth/signout")
def signout():
    resp = Response("OK", 200)
    resp.set_cookie(conf.get('ticket.cookie', 'SUBAUTHCOOKIE'), '', expires='0', domain=conf.get('ticket.domain',None))
    return resp

@app.route("/auth/passwd", methods=["GET","POST"])
def change_passwd():
    if not conf.get('allow_change', False):
        return 'Password changing has been disabled'

    msg = ''
    if request.method == 'POST':
        username = request.form['username'].encode('UTF_8')
        oldpass = request.form['oldpass'].encode('UTF_8')
        newpass = request.form['newpass'].encode('UTF_8')
        newpass2 = request.form['newpass2'].encode('UTF_8')
        if not auth_backend.auth(username, oldpass):
            msg = 'Invalid username/password'
        elif newpass != newpass2:
            msg = 'New passwords did not match!'
        elif auth_backend.change_password(username, newpass):
            return 'Changed.'
        else:
            msg = 'Unable to change password (account type doesn\'t allow it)'

    return '''
<html>
<head><title>Change password</title></head>
<body>
Change password<br/>
<b>%s</b>
<form action="/auth/passwd" method=POST>
<table border=0>
<tr><td>Username</td><td><input name='username' value='%s'/></td></tr>
<tr><td>Old password</td><td><input name='oldpass' type='password'/></td></tr>
<tr><td>&nbsp;</td></tr>
<tr><td>New password</td><td><input name='newpass' type='password'/></td></tr>
<tr><td>Confirm</td><td><input name='newpass2' type='password'/></td></tr>
<tr><td>&nbsp;</td><td><input type='submit' value='Change password'/></td></tr>
</table>
</form>
</body>
</html>
''' % (msg,request.form['username'] if 'username' in request.form else '')

@app.route("/auth", strict_slashes=False, methods=['GET','POST'])
def passport():
    '''
    this is the main authenticating function
    
    First, we will look for a signed cookie with an expiration date.
    If that doesn't exist, we will try to authenticate the user using HTTP-BASIC authentication
    '''
    log('original uri: %s' % request.args.get('p'))

    if conf.get('require_secure', False):
        log('is request secure? %s' % request.is_secure)
        if not request.is_secure:
            return require_secure()

    auth_cookie = request.cookies.get(conf.get('ticket.cookie', 'SUBAUTHCOOKIE'))
    if auth_cookie:
        log('cookie: %s' % auth_cookie)
        try:
            ts, username, sig = auth_cookie.split(':')
            if int(ts) > time.time() and make_digest('%s:%s' % (ts, username)) == sig:
                log('cookie valid')
                return valid_auth_response(username)
        except Exception, e:
            log(str(e))
            pass
        log('cookie not valid')
    else:
        log('no cookie')

    if not request.authorization:
        log("no auth... request one")
        return authenticate()
    
    log("Checking: %s/*****************" % (request.authorization.username,))

    try:
        if auth_backend.auth(str(request.authorization.username), str(request.authorization.password)):
            return valid_auth_response(str(request.authorization.username))
    except Exception, e:
        log(str(e))

    log("no valid authentication :(")

    return authenticate()

@app.route("/auth/signin", strict_slashes=False, methods=['GET','POST'])
def signin():
    log(request.cookies.get('NSREDIRECT')) 
    log("checking html request")
    if request.method == 'POST':
        username = request.form['username'].encode('UTF_8')
        passwd = request.form['passwd'].encode('UTF_8')

        try:
            if auth_backend.auth(username, passwd):
                log("success!")
                return valid_auth_response(username, True)
        except Exception, e:
            log(str(e))

    log("no auth")
    log("sending html form")
    return '''
<html>
<head><title>Sign in</title></head>
<body>
Sign in<br/>
<form action="/auth/signin" method=POST>
<table border=0>
<tr><td>Username</td><td><input name='username'/></td></tr>
<tr><td>Password</td><td><input name='passwd' type='password'/></td></tr>
<tr><td>&nbsp;</td><td><input type='submit' value='Sign in'/></td></tr>
</table>
</form>
</body>
</html>
'''

