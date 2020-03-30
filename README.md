subauth
===

An external service for authenticating user requests from Nginx.

See here for more details: http://nginx.org/en/docs/http/ngx_http_auth_request_module.html

Nginx can be configured to use a sub-request to validate if a client is authorized to view a file. To do this, nginx takes the user's request, and redirects it to a separate URL. In this project, we will use a Flask webapp to process this sub-request to determine if it is a valid request.

Since we are using a sub-request, the easiest mechanism that we can use to get a username or password is HTTP-basic authentication. If the user enters a valid username/password, they will get a cookie ticket that says they are validated. If they make a new request, then the cookie will be checked for validity first. If that isn't valid, then (and only then) will we poll one of the backends to see if the username/password is good. In addition to storing username/passwords in a local file, you can also delegate authentication to a remote Kerberos backend. Using a cookie/ticket for authentication first limits the stress on any remote backend.

# Installing
You can install subauth by cloning the Git repository and running 'make'. This will setup a virtualenv folder and setup all dependencies (in `venv`; a copy of virtualenv is included in the `support` directory). This will install Flask and uWSGI. Before using subauth, you'll need to perform the following steps:

1. setup subauth.conf
2. add users to a passwd file
3. add subauth to your Nginx configuration

## Subauth config
In order to use subauth, you'll have to setup a local configuration file. Here is an example file:

    # cookie settings
    ticket.secret=**SECRET**
    ticket.cookie=SUBAUTHCOOKIE
    # expire after 60 minutes
    ticket.expires=3600
    passwd.filename=local.passwd
    passwd.kerberos.realm=STANFORD.EDU
    verbose
    allow_change

What do these values mean?

**ticket.secret** - This is the private key that will be used to protect your ticket. Don't share this with anyone. If can be generated using the `bin/gensecret.py` script if you need one.

**ticket.cookie** - This is the name of your cookie. This is passed to the user's browser and stored there. You can name this whatever you'd like.

**ticket.expires** - The number of seconds that this ticket is valid for.

**passwd.filename** - The local filename that will house the users and their passwords. See below for a description of the format.

**passwd.kerberos.realm** - If you will be delgating authentication to a Kerberos server, what realm will be used? (This is required if using Kerberos delegation)

**passwd.kerberos.domain** - Similarly, if you need to specify a Kerberos domain, you can set it here. (This is optional for Kerberos delegation)

> Note: If you want to use Kerberos delegation, you'll need to also run `./install.sh kerberos` to install the appropriate Python libraries.

**require_secure** - Only process a request (including asking for a password) if the request is secure (HTTPS). SSL must be setup within Nginx and the proper uWSGI parameter set (HTTPS).

**verbose** - Include this line if you want verbose logging

**allow_change** - Allow users to change their passwords (only possible for SHA1, SHA256, BCRYPT account types)

## Adding users

Valid users are stored in a local passwd-like file. You can set the pathname of this file in the `subauth.conf` file (see above). Each user that will be allowed access must be specified in this file. Each line should be formatted like this:

    username:{type}:password:groups

Where {type} is either `{SHA1}` or `{KEREROS}`. If the type is `{SHA1}` or `{SHA256}`, the a salt will be included in the password field (`salt$password`). Then the password will be the hash(salt + password).

If the type is `{KERBEROS}`, the typeinfo will be the Kerberos username that will be sent to the Kerberos server for authentication (usually username@domain.edu). In this case, the password field will be empty (it isn't used).

If the type is `{LOGIN}`, a user login to the localhost will be used.

Groups should be a comma-delimited list of valid groups that this user belongs to. Groups aren't currently used, but they may be used in the future to grant access to distinct paths.

These lines may be generated automatically for you using the `bin/newuser.py` script.

## Nginx config

Here is how to add this as a sub-request authentication service in nginx.conf. Let's assume that you want to install the WSGI application in `/srv/subauth` and that you will want to call it as `/_auth`. Finally, let's assume that we want to *protect* the URL `/private-data`.

    location /private-data {
            auth_request /_auth;
            # if the authentication is successful, set a ticket
            auth_request_set $foo $upstream_http_x_subauthcookie;
            add_header Set-Cookie "SUBAUTHCOOKIE=$foo;Domain=www.example.com;Path=/";
    }
    location /_auth {
            uwsgi_pass unix:///srv/subauth/tmp/uwsgi.sock;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_set_header X-Original-URI $request_uri;
            uwsgi_param  QUERY_STRING       "p=$request_uri";
            uwsgi_param  REQUEST_METHOD     $request_method;
            uwsgi_param  CONTENT_TYPE       $content_type;
            uwsgi_param  CONTENT_LENGTH     "";
            uwsgi_param  REQUEST_URI        /auth;
            uwsgi_param  PATH_INFO          /auth;
            uwsgi_param  REMOTE_USER        $remote_user;
            uwsgi_param  REMOTE_ADDR        $remote_addr;
            uwsgi_param  REMOTE_PORT        $remote_port;
            uwsgi_param  SERVER_PORT        $server_port;
            uwsgi_param  SERVER_NAME        $server_name;
            uwsgi_param  HTTPS              $https if_not_empty;
    }

    location /auth {
            uwsgi_pass unix:///srv/subauth/tmp/uwsgi.sock;
            include uwsgi_params;
    }


If you want to use an HTML form to signin, then you can set that up a bit differently... Nginx expects to get a 200 (success) or a 401/405 on failure from the sub-request authorization page. Because of this, we can't directly send the HTML sign in form. So we need to setup an error handler in Nginx.

    location /private-data {
            auth_request /_auth;

            error_page 401 = @error401;

            # if the authentication is successful, set a ticket
            auth_request_set $foo $upstream_http_x_subauthcookie;
            add_header Set-Cookie "SUBAUTHCOOKIE=$foo;Domain=www.example.com;Path=/";
    }

    ...

    location @error401 {
        add_header Set-Cookie "NSREDIRECT=$scheme://$http_host$request_uri;Domain=www.example.com;Path=/";
        return 302 https://www.example.com/auth/signin;
    }


This does two things. First, when the subauth request fails for /private-data, instead of sending a 401 back to the user (and getting an HTTP-Auth prompt), instead it redirects to /auth/signin. This step also adds a new cookie named 'NSREDIRECT'. When the user successfully signs in, then this cookie is read and the user is redirected back to the resource they originally requested (/private-data).


Key points:

* Make sure that your cookie name is set correctly in `auth_request`.
* Make sure that you are pointing to the correct location for the uWSGI socket. By default we point to a BSD socket (file), but this could also point to a port. To run the uWSGI server on a port, you'd have to make the appropriate changes to the `run.sh` script as well.
* Currently the WSGI app that controls authentication is hard coded to use the URI `/auth` (See above).

## Starting subauth
To start the webservice, use the included `run.sh` script. It has three commands: `./run.sh start`, `./run.sh stop`, or `./run.sh restart`. If you add a new user, then the entire service needs to be restarted as we load the configuration from disk once.
