import re
import pexpect

def auth(username, password):
    clean_username = re.sub('[^a-zA-Z0-9]', '_', username)
    cmd = [ 'su', '--login', '-c /bin/true', clean_username ]

    p = pexpect.spawn(' '.join(cmd), timeout=60)
    p.expect('.*assword.*')
    p.sendline(password)
    p.expect(pexpect.EOF)
    p.close()

    return p.exitstatus == 0    
    
