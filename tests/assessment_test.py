import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_research import assess
for pnl,trades,skips,expected in [(-73.32,6,0,'NOT APPROVED FOR LIVE USE'),(0,0,187,'INSUFFICIENT CAPITAL FOR OBSERVED ENTRIES'),(500,100,0,'NOT APPROVED FOR LIVE USE'),(0,0,0,'NO COMPLETED TRADES')]:
 result=assess({'netPnl':pnl,'roundTrips':trades,'skippedEntryChecks':skips,'baselineNetPnl':-68.39})
 assert result['title']==expected and result['liveApproved'] is False
print('PASS: assessment labels and no automatic live approval.')
