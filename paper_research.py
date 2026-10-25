"""Fixed, non-optimized educational historical test. Not a production strategy."""
import math
from free_data import snapshot,now
ELIGIBLE={'RELIANCE','TCS','INFY','HDFCBANK'}
FEE=1.0
SLIPPAGE=.001 # Assumed 10 basis points per side, NOT measured execution.

def simulate(bars,capital):
 if not math.isfinite(capital) or not 0<capital<=100_000_000:raise ValueError('Capital must be greater than zero and at most 100 million rupees.')
 if len(bars)<60:raise ValueError('At least 60 valid observations required.')
 cash=capital;holding=False;entry=None;trades=[];equity=[];fees=0.;skips=0;peak=capital;drawdown=0.;required=[]
 for i in range(50,len(bars)):
  # Decision uses closes ending on i-1; execution proxy is next observed daily open i.
  previous=[b['close'] for b in bars[i-50:i]]
  want=sum(previous[-20:])/20>sum(previous)/50
  bar=bars[i]
  if want:required.append(bar['open']*(1+SLIPPAGE)+FEE)
  if want and not holding:
   fill=bar['open']*(1+SLIPPAGE);debit=fill+FEE
   if debit<=cash:
    cash-=debit;fees+=FEE;holding=True;entry={'date':bar['date'],'price':fill,'debit':debit}
   else:skips+=1
  elif not want and holding:
   fill=bar['open']*(1-SLIPPAGE);cash+=fill-FEE;fees+=FEE
   trades.append({'entryDate':entry['date'],'exitDate':bar['date'],'entryFill':entry['price'],'exitFill':fill,'netPnl':fill-FEE-entry['debit'],'exitReason':'Next-open trend rule'})
   holding=False;entry=None
  value=cash+(bar['close']*(1-SLIPPAGE)-FEE if holding else 0)
  peak=max(peak,value);drawdown=max(drawdown,(peak-value)/peak*100)
  equity.append({'date':bar['date'],'value':value})
 # Terminal liquidation is explicitly an end-of-test assumption, not a discovered sell signal.
 if holding:
  fill=bars[-1]['close']*(1-SLIPPAGE);cash+=fill-FEE;fees+=FEE
  trades.append({'entryDate':entry['date'],'exitDate':bars[-1]['date'],'entryFill':entry['price'],'exitFill':fill,'netPnl':fill-FEE-entry['debit'],'exitReason':'Forced end-of-test close (assumed)'})
 first=bars[50]['open']*(1+SLIPPAGE)+FEE
 baseline=capital
 if first<=capital:baseline=capital-first+bars[-1]['close']*(1-SLIPPAGE)-FEE
 return {'initialCapital':capital,'endingCash':cash,'netPnl':cash-capital,'returnPct':(cash/capital-1)*100,
  'maxDrawdownPct':drawdown,'fees':fees,'roundTrips':len(trades),'winningTrades':sum(t['netPnl']>0 for t in trades),
  'minimumHistoricalEntryDebit':min(required) if required else None,
  'skippedEntryChecks':skips,'baselineEndingCash':baseline,'baselineNetPnl':baseline-capital,
  'startDate':bars[50]['date'],'endDate':bars[-1]['date'],'trades':trades,'equity':equity}


def assess(result):
 reasons=[]
 if result['roundTrips']==0:
  title='INSUFFICIENT CAPITAL FOR OBSERVED ENTRIES' if result['skippedEntryChecks'] else 'NO COMPLETED TRADES'
  reasons.append('No trades occurred; zero loss is not evidence of safety or profitability.')
 else:
  title='NOT APPROVED FOR LIVE USE'
  if result['netPnl']<=0:reasons.append('This historical run did not earn a positive net result after the assumed costs.')
  if result['netPnl']<result['baselineNetPnl']:reasons.append('The rule underperformed its one-share buy-and-hold comparison.')
 if result['roundTrips']<20:reasons.append('Fewer than 20 round trips: a descriptive low-sample warning, not an approval threshold. Twenty trades would not establish reliability either.')
 reasons.extend(['No independent out-of-sample or prospective evaluation has been completed.','Execution, protective stops, taxes, and corporate actions are not comprehensively modeled.'])
 return {'title':title,'liveApproved':False,'reasons':reasons,'nextAction':'Keep real money separate. Inspect the evidence; do not copy historical orders into Groww.'}

def research(key,capital):
 if key not in ELIGIBLE:raise ValueError('Historical one-share test supports only the four listed Indian equities, not indices or forex.')
 snap=snapshot(key);p=snap['prices']
 if p['status']!='ok':raise ValueError('No usable price series. No test was run.')
 if p.get('stale'):raise ValueError('Price series flagged stale. No test was run.')
 if p.get('currency')!='INR':raise ValueError('INR series required.')
 result=simulate(p['bars'],capital)
 result['assessment']=assess(result)
 return {**result,'instrument':key,'name':snap['name'],'computedAt':now(),'source':p['source'],'sourceFetchedAt':p['fetchedAt'],
 'rule':'At each next daily open, hold at most ONE whole share when the prior 20-observation close average exceeds the prior 50-observation average. Otherwise exit. Cash must cover entry and fee. No leverage or shorting.',
 'assumptions':'₹1 hypothetical fee per filled side plus 0.10% adverse slippage per side. Actual brokerage, taxes, spreads, gaps, impact, dividends and corporate actions are not fully modeled. No protective stop is modeled. Final holdings are forcibly liquidated at the last close with assumed costs.',
 'warning':'Educational retrospective test only, not independent validation or an out-of-sample profitability claim. Small fixed stock list has selection/survivorship bias; raw price adjustment basis is unverified. No optimization, walk-forward validation, robustness test, or prospective paper result is provided. Do not use this to place real orders.',
 'decision':'RESEARCH ONLY — NO LIVE TRADE INSTRUCTION'}
