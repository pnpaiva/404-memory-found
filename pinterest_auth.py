#!/usr/bin/env python3
"""
One-time Pinterest setup: turn an approved app into the secrets the daily workflow needs.

Pinterest access tokens die after 30 days, so the workflow does not store one. It stores the app
credentials plus a refresh token and mints a fresh access token on every run. This script walks the
OAuth dance once, then prints the board list and the exact commands to store the secrets.

    python3 pinterest_auth.py

Before running it you need, from https://developers.pinterest.com/apps/:
  1. a Pinterest business account for the site (you already have one if you pin by hand),
  2. an app approved for Trial access (Connect app, reviewed within a business day),
  3. the app ID and app secret from the app's page,
  4. the redirect URI below added to the app under Configure -> Redirect URIs, character for character.

Nothing is written to the repository. The values are printed once, in your terminal, for you to paste
into `gh secret set` yourself.
"""

import base64
import http.server
import json
import socket
import sys
import threading
import urllib.parse
import webbrowser
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REDIRECT_URI = "http://localhost:8412/"
SCOPES = "boards:read,pins:read,pins:write"
AUTH_URL = "https://www.pinterest.com/oauth/"
TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
API = "https://api.pinterest.com/v5"
REPO = "pnpaiva/404-memory-found"


class CodeCatcher(http.server.BaseHTTPRequestHandler):
    """Catches the ?code=... that Pinterest sends back to the redirect URI."""

    code = None

    def do_GET(self):  # noqa: N802
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        CodeCatcher.code = (query.get("code") or [None])[0]
        body = (b"<h2>Done. You can close this tab and go back to the terminal.</h2>"
                if CodeCatcher.code else b"<h2>No code in the callback. Check the redirect URI.</h2>")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def basic_auth(app_id, secret):
    return "Basic " + base64.b64encode(f"{app_id}:{secret}".encode()).decode()


def post_token(app_id, secret, fields):
    req = Request(TOKEN_URL, data=urllib.parse.urlencode(fields).encode(), method="POST",
                  headers={"Authorization": basic_auth(app_id, secret),
                           "Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(req, timeout=60) as r:
        return json.load(r)


def list_boards(token):
    req = Request(f"{API}/boards?page_size=50", headers={"Authorization": f"Bearer {token}"})
    with urlopen(req, timeout=60) as r:
        return json.load(r).get("items", [])


def port_is_free(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def main():
    print(__doc__)
    app_id = input("App ID: ").strip()
    secret = input("App secret: ").strip()
    if not app_id or not secret:
        print("Both are required. Find them at https://developers.pinterest.com/apps/")
        return 1

    if not port_is_free(8412):
        print("Port 8412 is busy. Free it and run this again, the redirect URI depends on it.")
        return 1

    params = urllib.parse.urlencode({"client_id": app_id, "redirect_uri": REDIRECT_URI,
                                     "response_type": "code", "scope": SCOPES, "state": "404mf"})
    url = f"{AUTH_URL}?{params}"
    server = http.server.HTTPServer(("127.0.0.1", 8412), CodeCatcher)
    threading.Thread(target=server.handle_request, daemon=True).start()
    print("\nApprove the app in the browser window that just opened.")
    print("If it did not open, paste this into your browser:\n")
    print(url + "\n")
    webbrowser.open(url)

    for _ in range(120):
        if CodeCatcher.code:
            break
        threading.Event().wait(1)
    server.server_close()
    if not CodeCatcher.code:
        print("No authorization code came back. The usual cause is a redirect URI that does not match")
        print(f"exactly. It must be registered as: {REDIRECT_URI}")
        return 1

    try:
        tokens = post_token(app_id, secret, {"grant_type": "authorization_code", "code": CodeCatcher.code,
                                             "redirect_uri": REDIRECT_URI, "continuous_refresh": "true"})
    except HTTPError as e:
        print(f"Token exchange failed: HTTP {e.code} {e.read().decode()[:300]}")
        return 1

    access, refresh = tokens["access_token"], tokens.get("refresh_token")
    print(f"\nAccess token issued, valid for {tokens.get('expires_in', 0) // 86400} days.")
    if not refresh:
        print("No refresh token came back, so the workflow would stop working in 30 days.")
        print("Re-run this and make sure the app uses the Authorization Code grant.")
        return 1

    boards = list_boards(access)
    if not boards:
        print("\nThis account has no boards yet. Create one on Pinterest, then run this again.")
        return 1
    print("\nBoards on this account:\n")
    for b in boards:
        print(f"  {b['id']}   {b['name']}   ({b.get('pin_count', 0)} pins)")
    board_id = boards[0]["id"] if len(boards) == 1 else input("\nPaste the board ID to pin to: ").strip()

    print("\n" + "=" * 78)
    print("Run these four commands. Each one asks for the value, so paste it when prompted.")
    print("Nothing here is written to any file.\n")
    for name, value in (("PINTEREST_APP_ID", app_id), ("PINTEREST_APP_SECRET", secret),
                        ("PINTEREST_REFRESH_TOKEN", refresh), ("PINTEREST_BOARD_ID", board_id)):
        print(f"  gh secret set {name} --repo {REPO}")
        print(f"      value: {value}\n")
    print("=" * 78)
    print("\nThe next daily build will pin on its own. Check the 'Pin new posts to Pinterest' step.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
