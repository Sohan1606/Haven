# Haven
### A calmer personal market-research workspace

Haven is an independent portfolio project: a responsive market-research and paper-trading web application with a full-screen, call-style voice interface.

**Status: portfolio/demo release v0.1.0. Not a published live-trading product.** It is not affiliated with Groww, NSE, BSE, Yahoo, Google, or any broker. No broker orders are placed. No investment returns or prediction accuracy are promised.

## What's inside
- Responsive forest-green and ivory interface with subtle transitions and reduced-motion support.
- On-demand availability/readiness flow, a manually entered allocation, and separate virtual practice cash.
- Single-user local password setup/sign-in, session expiry, lock, and rate limiting.
- Optional free daily historical price snapshots, averages, and timestamped headline links.
- A fixed one-share historical moving-average experiment with assumed costs, affordability checks, drawdown, trade logs, and a baseline comparison.
- Explicit “Not approved for live use” assessments; profitable historical results never automatically approve real trading.
- Fictional paper order entry/exit workflow with fee accounting.
- Full-viewport mobile voice screen, red hang-up, optional speech output, and limited voice commands.
- Local records, export, reset, pause, and balance hiding.

## Start locally
Requires **Python 3.10+**. No pip dependencies or paid API keys.

```bash
python3 local_server.py
```
On Windows:
```powershell
py -3 local_server.py
```
Or use `Start-Haven-Windows.bat`.

Open **http://127.0.0.1:8765** in Chrome or Edge on the same laptop. Create a password (12+ characters) and keep the terminal running. Ctrl+C stops it. The default server binds only to loopback; a phone cannot access it.

Use the same browser, profile and URL for existing records. Opening `index.html` directly is a standalone visual/paper demo and **bypasses server authentication**.

## Try the product
1. Settings: enter your name and a hypothetical/manual allocation.
2. Overview: “I'm available now” → record available time and check readiness.
3. Overview/Markets: “Your research, on demand” → select a symbol and fetch a snapshot.
4. Markets: “Put a rule to the test” → run a historical experiment. Inspect losses and limitations, not just returns.
5. Markets: create a fictional paper order; Portfolio: simulate an exit.
6. Overview: Talk to your assistant → microphone → red hang-up. On mobile-sized screens it occupies the entire app viewport, not the browser's own controls.

### Voice examples
“What is my balance?”, “Show my positions”, “I am available”, “Explain privacy”, “Pause”.

Voice is a limited **rule-based command interface**, not an LLM. Browser speech recognition can require internet, permissions, and external processing. Haven does not save raw audio or transcripts. Speech synthesis uses available browser voices. Hindi recognition coverage is partial; responses are English.

## Share on GitHub
Create a new empty repository, then run from this folder:

```bash
git init
git add .
git commit -m "Initial Haven portfolio release"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```
Replace `YOUR_REPOSITORY_URL` with your actual repository URL. Review files before pushing. Never commit account databases, exports, passwords, environment files or broker credentials. Included `.gitignore` helps, but is not a guarantee.

### Optional GitHub Pages visual demo
GitHub Pages can serve `index.html` from this repository as a **static visual/paper demo only**. It cannot execute the Python server, provide server sign-in, or expose historical research endpoints. GitHub Pages hosting is not private application access control; a repository being private does not by itself prove a Pages site is private.

Do not call the Pages demo a live trading product. Do not publicly deploy `local_server.py` unchanged. It is intentionally designed for a trusted single-user laptop, not public hosting.

## Sources and costs
Pressing Fetch requests prices from Yahoo Finance's unofficial chart endpoint and headlines from Google News RSS via your laptop. No balance or broker credentials are sent. Providers can see your network address and selected query. Linked sites have their own policies. Terms, availability and permitted use can change; review provider terms and do not redistribute data without permission.

No paid service is enabled. Prices are historical, may be delayed or inaccurate, and today's daily bar is omitted. Price adjustment/corporate-action basis is unverified. Headlines are not independently verified or a complete event calendar. Source failures appear as unavailable, not invented data.

## Security and privacy
Password hash: salted PBKDF2-SHA256, 600,000 iterations. Session tokens: random, server-side, one-hour expiry; HttpOnly and SameSite=Strict cookies. Requests changing auth state require the local browser Origin. Five valid-length failed login attempts trigger a five-minute in-memory rate limit.

Account hash is in `~/.haven-local/account.sqlite3`. Paper records/preferences are in **unencrypted browser localStorage**. OS access, malware or developer tools can bypass the app's privacy boundary. No biometric lock, encrypted record database or cross-device sync is implemented. Session locking does not erase records. Authenticated shell caching is disabled by the local server. Loopback HTTP is not a public hosting configuration.

Password recovery: stop the server, rename `~/.haven-local`, restart and create a new password. Browser records remain unchanged. This recovery method also illustrates why your OS account is the true security boundary.

## Historical test limitations
The fixed rule holds at most one share when prior 20-observation average exceeds prior 50-observation average, using next-observed-open execution proxies. ₹1 per filled side and 0.10% adverse slippage per side are hypothetical—not Groww fees. The last holding is forcibly liquidated at the test endpoint. No protective stops, dividends, complete taxes, spread/impact model, or corporate-action normalization.

The four selected stocks have selection/survivorship bias. No independent walk-forward validation, robust out-of-sample evidence or prospective strategy approval is provided. A profitable run would not establish future profitability. A zero-trade result does not establish safety. No strategy is approved for live use.

## Tests
```bash
python3 tests/local_auth_test.py
python3 tests/paper_research_test.py
python3 tests/assessment_test.py
```
Use `py -3` instead of `python3` on Windows.

Optional browser smoke test needs Node/Playwright and a **separate static demo server** on port 3000. See `tests/smoke.cjs`; it is not a complete authenticated-server browser regression. Microphone/provider access, real Android devices and profitability are not covered by automated checks. No security audit has been performed.

## Roadmap, not implemented promises
Official broker access, licensed live feeds, conversational AI, strategy validation, prospective paper monitoring, reliable server-push notifications, hardened hosted authentication, and real-money execution require separate engineering and assessment.

## Reel / portfolio assets
Use `docs/REEL-KIT.md` for a truthful shot list and copy-paste caption. No caption or hashtag set guarantees reach or virality.

## License
MIT for original project code; see LICENSE. Third-party source content and data remain subject to their own rights and terms.
