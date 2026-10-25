#!/usr/bin/env python3
"""Single-user loopback-only Haven server. Python 3.10+, standard library only."""
import argparse, hashlib, http.cookies, json, mimetypes, os, secrets, sqlite3, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from free_data import snapshot
from paper_research import research

ROOT = Path(__file__).resolve().parent
DATA = Path.home() / '.haven-local'
DB = DATA / 'account.sqlite3'
LOCK = threading.RLock()
SESSIONS = {}
ATTEMPTS = []
TTL = 3600
ITERATIONS = 600_000
ASSETS = {'icon.svg', 'icon-192.png', 'icon-512.png', 'manifest.webmanifest'}

LOGIN = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Haven · Private workspace</title><style>
*{box-sizing:border-box}body{margin:0;min-height:100dvh;background:#102f2b;color:#eef4e9;display:grid;place-items:center;padding:24px;font:14px system-ui,sans-serif}.wrap{width:100%;max-width:420px}.logo{font-size:30px;letter-spacing:-1px;font-weight:650;margin-bottom:48px}.logo span{color:#d9ef9d}small{font-size:10px;letter-spacing:2px;color:#adc3ad}h1{font-size:30px;font-weight:550;letter-spacing:-1px;margin:12px 0}p{color:#aec3b6;font-size:13px;line-height:1.8}form{margin-top:26px}label{display:block;font-size:12px;margin-top:18px;margin-bottom:8px}input{width:100%;background:#23463c;border:1px solid #496557;border-radius:9px;padding:14px;color:white;font:inherit}button{width:100%;border:0;border-radius:9px;padding:15px;background:#d9ef9d;color:#102f2b;font:600 13px system-ui;cursor:pointer;margin-top:24px}button:disabled{opacity:.6}#status{min-height:24px;color:#f2d5a6;font-size:12px;margin-top:12px}.note{border-top:1px solid #355449;margin-top:28px;padding-top:18px;font-size:11px}.local{color:#d9ef9d;font-size:11px;margin-bottom:20px}</style></head><body><main class="wrap"><div class="logo"><span>◈</span> haven</div><small>YOUR LAPTOP. YOUR WORKSPACE.</small><h1 id="title">Loading…</h1><p id="intro">Checking your local account.</p><form id="form"><label for="password">Workspace password</label><input id="password" type="password" autocomplete="current-password" required minlength="12" maxlength="256"><div id="confirmWrap" hidden><label for="confirm">Confirm password</label><input id="confirm" type="password" autocomplete="new-password" maxlength="256"></div><button id="submit" disabled>Continue</button><div id="status" role="status"></div></form><p class="note">Local access only · No real-money execution<br>Your operating-system account remains the security boundary. This does not encrypt browser records or protect against malware on your laptop.</p></main><script>
let setup=false;const $=id=>document.getElementById(id);fetch('/api/session',{cache:'no-store'}).then(r=>r.json()).then(s=>{if(s.authenticated){location.replace('/');return}setup=!s.configured;$('title').textContent=setup?'Make this space yours.':'Welcome back.';$('intro').textContent=setup?'Create a password of at least 12 characters. Keep it in a password manager; there is no email password recovery.':'Sign in to your local workspace. Your session expires after one hour.';$('confirmWrap').hidden=!setup;$('confirm').required=setup;$('password').autocomplete=setup?'new-password':'current-password';$('submit').textContent=setup?'Create private workspace':'Unlock workspace';$('submit').disabled=false}).catch(()=>{$('status').textContent='Cannot reach the local server. Keep the launcher terminal open.'});$('form').onsubmit=async e=>{e.preventDefault();if(setup&&$('password').value!==$('confirm').value){$('status').textContent='Passwords do not match.';return}$('submit').disabled=true;$('status').textContent='Checking…';try{const r=await fetch(setup?'/api/setup':'/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:$('password').value})});const d=await r.json();if(!r.ok)throw Error(d.error||'Unable to sign in');$('password').value='';$('confirm').value='';location.replace('/')}catch(err){$('status').textContent=err.message;$('submit').disabled=false}};
</script></body></html>'''

def connection():
    return sqlite3.connect(DB)

def configured():
    with connection() as c:
        return c.execute('SELECT COUNT(*) FROM account').fetchone()[0] > 0

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)

class Handler(BaseHTTPRequestHandler):
    server_version = 'HavenLocal/1.0'
    sys_version = ''
    def log_message(self, fmt, *args):
        # Deliberately omit request bodies, headers, passwords, and tokens.
        print(time.strftime('%H:%M:%S'), self.command, self.path.split('?')[0], flush=True)
    def allowed_origin(self):
        port = self.server.server_port
        allowed = {f'localhost:{port}', f'127.0.0.1:{port}'}
        return self.headers.get('Host') in allowed
    def session(self):
        try:
            cookie = http.cookies.SimpleCookie(self.headers.get('Cookie', ''))
            token = cookie['haven_session'].value
        except (KeyError, http.cookies.CookieError):
            return None
        with LOCK:
            for key, expires in list(SESSIONS.items()):
                if expires < time.time():
                    SESSIONS.pop(key, None)
            return token if token in SESSIONS else None
    def send(self, status, data, content_type='application/json; charset=utf-8', cookie=None):
        if not isinstance(data, bytes):
            data = json.dumps(data).encode() if isinstance(data, dict) else data.encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Permissions-Policy', 'camera=(), geolocation=()')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if not self.allowed_origin():
            return self.send(403, {'error':'Only localhost access is allowed.'})
        path = self.path.split('?', 1)[0]
        if path == '/api/paper-research':
            if not self.session(): return self.send(401, {'error':'Sign in first.'})
            query = parse_qs(urlsplit(self.path).query)
            try:
                capital = float(query.get('capital', ['100'])[0])
                result = research(query.get('symbol', ['RELIANCE'])[0], capital)
            except ValueError as e: return self.send(400, {'error':str(e)})
            return self.send(200, result)
        if path == '/paper-panel.js':
            if not self.session(): return self.send(401, {'error':'Sign in first.'})
            return self.send(200, (ROOT/'paper-panel.js').read_bytes(), 'application/javascript; charset=utf-8')
        if path == '/api/snapshot':
            if not self.session():
                return self.send(401, {'error':'Sign in first.'})
            key = parse_qs(urlsplit(self.path).query).get('symbol', ['NIFTY'])[0]
            try: result = snapshot(key)
            except ValueError: return self.send(400, {'error':'Unsupported instrument.'})
            return self.send(200, result)
        if path == '/free-panel.js':
            if not self.session(): return self.send(401, {'error':'Sign in first.'})
            return self.send(200, (ROOT/'free-panel.js').read_bytes(), 'application/javascript; charset=utf-8')
        if path == '/api/session':
            return self.send(200, {'configured': configured(), 'authenticated': bool(self.session())})
        if path in ('/', '/index.html'):
            if not self.session():
                return self.send(200, LOGIN, 'text/html; charset=utf-8')
            html = (ROOT / 'index.html').read_text(encoding='utf-8')
            html = html.replace('DEMONSTRATION ONLY — No market or news provider is connected. Sample instruments below are fictional; these are not recommendations.', 'PAPER DEMONSTRATION — The order scenario below is fictional. The separate on-demand research panel uses free external sources; it is not a live signal feed.')
            html = html.replace('This build has none of those connections.', 'Optional free historical snapshots and headlines are available above. A live licensed feed and validated strategy are not connected.')
            # Do not cache an authenticated workspace shell using the demo service worker.
            html = html.replace("if('serviceWorker'in navigator&&location.protocol!=='file:')navigator.serviceWorker.register('./sw.js').catch(()=>{});", '')
            html = html.replace('<div class="topright">', '<div class="topright"><button class="btn secondary small" onclick="havenLogout()">Lock</button>', 1)
            js = '''<script>
async function havenLogout(){stopVoice();await fetch('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.replace('/')}
if('serviceWorker' in navigator){navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>r.unregister()));caches.keys().then(keys=>keys.filter(k=>k.startsWith('haven-')).forEach(k=>caches.delete(k)))}
setInterval(async()=>{try{const r=await fetch('/api/session',{cache:'no-store'});const s=await r.json();if(!s.authenticated){stopVoice();location.replace('/')}}catch{stopVoice();document.body.innerHTML='<main style="padding:40px;font-family:system-ui"><h1>Local server unavailable</h1><p>Monitoring was never active. Restart the launcher and refresh. No real orders are managed.</p></main>'}},15000);
</script>'''
            html = html.replace('</body>', js + '<script src="/free-panel.js"></script><script src="/paper-panel.js"></script></body>')
            return self.send(200, html, 'text/html; charset=utf-8')
        if path.lstrip('/') in ASSETS and path.count('/') == 1:
            asset = ROOT / path[1:]
            return self.send(200, asset.read_bytes(), mimetypes.guess_type(str(asset))[0] or 'application/octet-stream')
        return self.send(404, {'error':'Not found.'})
    def do_POST(self):
        if not self.allowed_origin() or self.headers.get('Origin') != 'http://' + self.headers.get('Host', ''):
            return self.send(403, {'error':'Request origin not allowed.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send(415, {'error':'JSON required.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 <= length <= 4096:
                return self.send(413, {'error':'Request too large.'})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict): raise ValueError()
        except (ValueError, json.JSONDecodeError):
            return self.send(400, {'error':'Invalid request.'})
        path = self.path.split('?', 1)[0]
        if path == '/api/logout':
            with LOCK:
                token = self.session()
                if token: SESSIONS.pop(token, None)
            return self.send(200, {'ok':True}, cookie='haven_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
        if path not in ('/api/setup', '/api/login'):
            return self.send(404, {'error':'Not found.'})
        password = payload.get('password')
        if not isinstance(password, str) or len(password) < 12 or len(password) > 256:
            return self.send(400, {'error':'Use a password between 12 and 256 characters.'})
        with LOCK:
            now = time.time()
            ATTEMPTS[:] = [t for t in ATTEMPTS if now - t < 300]
            if len(ATTEMPTS) >= 5:
                return self.send(429, {'error':'Too many attempts. Wait five minutes and try again.'})
            if path == '/api/setup':
                if configured():
                    return self.send(409, {'error':'An account already exists. Refresh to sign in.'})
                salt = secrets.token_bytes(32)
                digest = hash_password(password, salt)
                with connection() as c:
                    c.execute('INSERT INTO account (id,salt,digest) VALUES (1,?,?)', (salt,digest))
            else:
                with connection() as c:
                    record = c.execute('SELECT salt,digest FROM account WHERE id=1').fetchone()
                if not record or not secrets.compare_digest(hash_password(password, record[0]), record[1]):
                    ATTEMPTS.append(now)
                    return self.send(401, {'error':'Unable to sign in. Check your password.'})
            ATTEMPTS.clear()
            token = secrets.token_urlsafe(48)
            SESSIONS[token] = now + TTL
        # Secure flag is intentionally absent on loopback HTTP, not public deployment.
        return self.send(200, {'ok':True}, cookie=f'haven_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={TTL}')

def main():
    parser = argparse.ArgumentParser(description='Haven laptop-only server. Never expose to the internet.')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
    with connection() as c:
        c.execute('CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY CHECK(id=1),salt BLOB NOT NULL,digest BLOB NOT NULL)')
    try: os.chmod(DB, 0o600)
    except OSError: pass
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as e:
        print(f'Cannot start: {e}. Close the other instance or choose --port 8766.')
        return
    print(f'\nHaven local workspace: http://127.0.0.1:{args.port}\nKeep this window open. Ctrl+C stops the server.\nLAPTOP ONLY. No live data, broker connection, or real trading.\n', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nHaven stopped.')
    finally: server.server_close()

if __name__ == '__main__': main()
