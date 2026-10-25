"""Optional free-source snapshots. Descriptive only; no trade signals or guarantees."""
import concurrent.futures,datetime,email.utils,json,math,threading,time,urllib.parse,urllib.request,xml.etree.ElementTree as ET
IST=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
INSTRUMENTS={
 'NIFTY':('^NSEI','NIFTY 50','Nifty 50 stock market India'),
 'RELIANCE':('RELIANCE.NS','Reliance Industries','Reliance Industries NSE'),
 'TCS':('TCS.NS','Tata Consultancy Services','TCS earnings NSE'),
 'INFY':('INFY.NS','Infosys','Infosys NSE earnings'),
 'HDFCBANK':('HDFCBANK.NS','HDFC Bank','HDFC Bank NSE'),
 'EURUSD':('EURUSD=X','EUR / USD','EUR USD currency central bank'),
 'USDINR':('INR=X','USD / INR','Indian rupee USD INR RBI')}
CACHE={};LOCK=threading.Lock()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def download(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (Haven personal research workspace)'})
 with urllib.request.urlopen(req,timeout=12) as r:
  data=r.read(2_000_001)
  if len(data)>2_000_000:raise ValueError('Response too large')
  return data

def prices(symbol):
 url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol,safe='')+'?interval=1d&range=2y'
 data=json.loads(download(url))
 result=data.get('chart',{}).get('result')
 if not result:raise ValueError('No price series returned')
 obj=result[0];meta=obj.get('meta',{});q=obj['indicators']['quote'][0];bars=[]
 today=datetime.datetime.now(IST).date()
 for i,(ts,close) in enumerate(zip(obj.get('timestamp',[]),q.get('close',[]))):
  if close is None or not isinstance(close,(float,int)) or not math.isfinite(close) or close<=0:continue
  dt=datetime.datetime.fromtimestamp(ts,IST)
  # Conservatively omit today's bar, which may still be forming. Never call this a live quote.
  if dt.date()>=today:continue
  opening=q.get('open',[])[i] if i<len(q.get('open',[])) else None
  if opening is None or not isinstance(opening,(int,float)) or not math.isfinite(opening) or opening<=0:continue
  bars.append({'date':dt.date().isoformat(),'open':round(opening,5),'close':round(close,5)})
 if len(bars)<50:raise ValueError('Fewer than 50 valid past daily observations')
 closes=[b['close'] for b in bars];last=closes[-1];s20=sum(closes[-20:])/20;s50=sum(closes[-50:])/50
 age=(today-datetime.date.fromisoformat(bars[-1]['date'])).days
 return {'status':'ok','source':'Yahoo Finance chart endpoint (unofficial; not a licensed real-time feed)',
  'sourceUrl':'https://finance.yahoo.com/quote/'+urllib.parse.quote(symbol,safe='')+'/',
  'fetchedAt':now(),'currency':meta.get('currency','Unknown'),'lastBarDate':bars[-1]['date'],
  'stale':age>10,'calendarDaysSinceBar':age,'close':last,'changePct':(last/closes[-2]-1)*100,
  'sma20':s20,'sma50':s50,'description':('Past close is above both 20- and 50-observation averages.' if last>s20 and last>s50 else 'Past close is below both 20- and 50-observation averages.' if last<s20 and last<s50 else 'Past close is between the two averages.'),
  'bars':bars,'basis':'Daily historical observations; today excluded. Adjustment basis is not verified. Not suitable for order pricing.'}

def headlines(query):
 url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query+' when:7d','hl':'en-IN','gl':'IN','ceid':'IN:en'})
 root=ET.fromstring(download(url));items=[]
 for item in root.findall('./channel/item')[:5]:
  title=item.findtext('title','');link=item.findtext('link','');pub=item.findtext('pubDate','');publisher=item.findtext('source','Unknown publisher')
  if not link.startswith('https://'):continue
  try:published=email.utils.parsedate_to_datetime(pub).isoformat()
  except (ValueError,TypeError):published=None
  items.append({'title':title,'url':link,'publisher':publisher,'publishedAt':published})
 return {'status':'ok','source':'Google News RSS aggregation','fetchedAt':now(),'items':items,
  'warning':'Headlines only. Reporting and company claims are not independently verified. No full-article or sentiment analysis is performed.'}

def snapshot(key):
 if key not in INSTRUMENTS:raise ValueError('Unsupported instrument')
 with LOCK:
  if key in CACHE and time.time()-CACHE[key][0]<300:
   return {**CACHE[key][1],'cached':True}
 symbol,name,query=INSTRUMENTS[key]
 def safe(fn,arg):
  try:return fn(arg)
  except Exception:return {'status':'unavailable','error':'Provider unavailable, blocked, or returned insufficient data. No replacement values were invented.'}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  p=pool.submit(safe,prices,symbol);n=pool.submit(safe,headlines,query)
  result={'instrument':key,'name':name,'requestedAt':now(),'prices':p.result(),'news':n.result(),'cached':False,
   'decision':'NO ACTIONABLE TRADE PLAN','notice':'Descriptive historical snapshot only. Not a prediction, tested strategy, or execution instruction. Forex eligibility is not verified.'}
 with LOCK:CACHE[key]=(time.time(),result)
 return result
