#!/usr/bin/python3

import http.server
import socketserver
import subprocess
import os
import sys
import pwd
import syslog

def drop_privs(user):
    pwnam = pwd.getpwnam(user)
    if os.getgid() != pwnam.pw_gid:
        os.setgid(pwnam.pw_gid)
    if os.getuid() != pwnam.pw_uid:
        os.setuid(pwnam.pw_uid)

drop_privs("fastd")

syslog.openlog(logoption=syslog.LOG_PID | syslog.LOG_PERROR)
syslog.syslog("daemon started")

PORT = 11684

GITBASEDIR="/etc/fastd/.peers/fastd-peers-clients"

os.chdir(GITBASEDIR)

if not os.path.isdir(".git"):
    sys.exit("bad repo basedir")

if len(subprocess.check_output(["git", "status", "--porcelain"])) != 0:
    sys.exit("git is not clean")

class WebhookHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        response ="ok\n".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)
        # TODO: rate-limit
        self.pull_from_github()

    def do_POST(self):
        # handle POST just like GET
        self.do_GET()

    def reload(self):
        syslog.syslog("triggering fastd config reload")
        for seg in range(1,8):
            fn = "/var/run/fastd.{0:02}-clients.pid".format(seg)
            subprocess.call(["pkill", "-HUP", "-F", fn])
        for fn in ["/var/run/fastd.00-clients.pid"]:
            subprocess.call(["pkill", "-USR2", "-F", fn])

    def pull_from_github(self):
        syslog.syslog("pull from github triggered")
        old_commit = subprocess.check_output(["git", "rev-parse", "HEAD"])
        subprocess.call(["git", "pull"])
        new_commit = subprocess.check_output(["git", "rev-parse", "HEAD"])
        syslog.syslog("old commit: {}, new commit: {}".format(old_commit, new_commit))
        if old_commit != new_commit:
            self.reload()

Handler = WebhookHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)

syslog.syslog("serving at port {}".format(PORT))
httpd.serve_forever()

