import datetime,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_research import simulate
bars=[{'date':(datetime.date(2024,1,1)+datetime.timedelta(days=i)).isoformat(),'open':100+i,'close':100+i} for i in range(120)]
r=simulate(bars,10000)
assert r['roundTrips']==1 and r['fees']==2
assert r['trades'][0]['entryDate']==bars[50]['date']
expected=(219*.999-1)-(150*1.001+1)
assert math.isclose(r['netPnl'],expected,abs_tol=1e-8)
assert r['trades'][0]['exitReason'].startswith('Forced')
small=simulate(bars,100)
assert small['roundTrips']==0 and small['endingCash']==100 and small['skippedEntryChecks']==70
# Changing future bars must not change the first entry's price/date.
modified=[dict(b) for b in bars]
for b in modified[80:]:b['close']=10;b['open']=10
other=simulate(modified,10000)
assert other['trades'][0]['entryDate']==r['trades'][0]['entryDate']
assert other['trades'][0]['entryFill']==r['trades'][0]['entryFill']
for bad in [0,-1,float('nan'),float('inf')]:
 try:simulate(bars,bad)
 except ValueError:pass
 else:raise AssertionError('Invalid capital accepted')
print('PASS: next-observation entry, fees/slippage, terminal liquidation, affordability, future-data isolation for first entry, invalid capital.')
