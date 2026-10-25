"""Standard-library integration checks; starts an isolated server and removes test credentials."""
import http.cookiejar,json,os,subprocess,sys,tempfile,time,urllib.request,urllib.error
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='haven-test-') as tmp:
 env={**os.environ,'HOME':tmp,'USERPROFILE':tmp}
 proc=subprocess.Popen([sys.executable,str(root/'local_server.py'),'--port','18765'],env=env,stdout=subprocess.DEVNULL)
 try:
  base='http://127.0.0.1:18765'
  jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
  def req(path,data=None,origin=None):
   headers={}
   if data is not None:headers={'Content-Type':'application/json','Origin':origin or base}
   r=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
   try:
    with client.open(r) as res:return res.status,res.read().decode(),res.headers
   except urllib.error.HTTPError as e:return e.code,e.read().decode(),e.headers
  # Short bounded startup check in a one-shot test, not a development-server polling loop.
  for i in range(30):
   try:req('/api/session');break
   except urllib.error.URLError:time.sleep(.1)
  assert json.loads(req('/api/session')[1])=={'configured':False,'authenticated':False}
  assert 'Make this space yours' in req('/')[1]
  assert req('/api/setup',{'password':'long-test-password-918'},origin='http://evil.example')[0]==403
  assert req('/api/setup',{'password':'short'})[0]==400
  assert req('/api/setup',{'password':'long-test-password-918'})[0]==200
  assert json.loads(req('/api/session')[1])['authenticated']
  html=req('/')[1];assert 'havenLogout' in html and 'serviceWorker.register' not in html
  assert req('/local_server.py')[0]==404
  assert req('/../.haven-local/account.sqlite3')[0]==404
  assert req('/api/logout',{})[0]==200
  assert not json.loads(req('/api/session')[1])['authenticated']
  assert req('/api/login',{'password':'wrong-password-long'})[0]==401
  assert req('/api/login',{'password':'long-test-password-918'})[0]==200
  assert req('/api/setup',{'password':'other-long-password'})[0]==409
  req('/api/logout',{})
  for _ in range(5):assert req('/api/login',{'password':'wrong-password-long'})[0]==401
  assert req('/api/login',{'password':'long-test-password-918'})[0]==429
  print('PASS: setup, password validation, sign-in/out, origin rejection, asset allowlist, no authenticated shell caching, and rate limiting.')
 finally:
  proc.terminate();proc.wait(timeout=5)
