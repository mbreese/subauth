subauth
===

An external service for authenticating user requests from Nginx.

Nginx can be configured to use a sub-request to validate if a client is authorized to view a file. To do this, nginx takes the user's request, and redirects it to a separate URL. In this project, we will use a Flask webapp to process this sub-request to determine if it is a valid request.

Since we are using a sub-request, the easiest mechanism that we can use to get a username or password is HTTP-basic authentication. If the user enters a valid username/password, they will get a cookie ticket that says they are validated. If they make a new request, then the cookie will be checked for validity first. If that isn't valid, then (and only then) will we poll one of the backends to see if the username/password is good. By checking a ticket first, we will limit any stress on the potentially remote backend (such as a Kerberos server).
