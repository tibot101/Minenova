# MineNova Infinity — Online Arena Edition

MineNova is a polished Minesweeper game with classic solo play, guided training, local co-op, and real server-backed ranked PvP.

## What changed in this version

### Real accounts + cloud progress
- Create an account with a username and password.
- Passwords are stored as salted PBKDF2-SHA256 hashes, never as plaintext.
- Login sessions use signed JWT access tokens.
- Solo progression/settings can sync to the account: XP, wins, chord totals, personal bests, theme, flag style, and accessibility settings.
- Profiles show rating, tier, wins, losses, streak, and match count.

### Real online ranked PvP
- Two signed-in players join the same matchmaking queue.
- The server pairs players by board difficulty.
- Both players receive their own board based on the exact same hidden server field.
- The browser does **not** receive the hidden mine layout in ranked play.
- Reveals, flags, and chords are validated by the server.
- Each player has 2 lives; hitting a mine costs a life and 75 score.
- First player to clear the safe field wins. Running out of lives also loses the match.
- Live opponent progress, lives, score, connection status, emotes, and result are synchronized over WebSockets.
- Disconnects get a 30-second reconnect grace period before a forfeit.
- Players can request a rematch after the result.

### Ranking + leaderboard
- Elo-style rating starts at 1000.
- Tiers: Bronze, Silver, Gold, Platinum, Diamond, Nova.
- Global leaderboard shows rating, record, and match count.
- Match history stores opponent, result, difficulty, duration, reason, and rating change.

### Improved local co-op controls
Player 1:
- `W A S D` — move
- `Space` — reveal
- `E` — flag
- `Q` — chord

Player 2:
- Arrow keys — move
- `Enter` — reveal
- `Right Shift` — flag
- `Backslash` — chord

Shared:
- `Tab` — switch which player owns mouse/touch actions
- Mouse click — reveal / chord
- Right-click — mark
- Long-press on touch — mark

### Everything from the earlier edition remains
- Beginner / Intermediate / Expert / Master solo boards
- Classic, Sprint, and Zen
- Chording with click, Shift-click, double-click, middle-click, and keyboard
- Guided interactive tutorial
- Safe Hint, Pulse Scan, Undo Mark, Nova Shield
- XP, missions, statistics, seed replay, daily field
- Multiple themes and flag designs
- Responsive desktop/mobile layout
- Generated sound effects, haptics, particles, confetti
- Local solo play still works if the server is unavailable

---

## Run it locally

The online features require the server; do **not** just double-click `index.html` if you want accounts or matchmaking.

### 1. Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Start MineNova

Windows:

```text
start.bat
```

macOS / Linux:

```bash
./start.sh
```

Or directly:

```bash
python server.py
```

### 3. Open it

Visit:

```text
http://127.0.0.1:8000
```

Open that URL in two separate browser profiles/windows, create two accounts, and queue the same difficulty to test real matchmaking.

The server creates `minenova.db` automatically next to `server.py`.

---

## Play on two devices on the same network

By default `server.py` listens on `127.0.0.1`. To expose it to your LAN:

macOS / Linux:

```bash
HOST=0.0.0.0 python server.py
```

Windows PowerShell:

```powershell
$env:HOST="0.0.0.0"
python server.py
```

Then visit `http://YOUR-COMPUTER-LAN-IP:8000` from both devices.

---

## Put it on the real internet

For actual internet matchmaking between people in different homes, deploy this folder to a Python host that supports WebSockets (for example a VPS or a WebSocket-capable Python app host).

Production environment variables:

```text
MINENOVA_SECRET=<a long random secret>
MINENOVA_DB=/persistent/storage/minenova.db
HOST=0.0.0.0
PORT=<port supplied by your host>
```

Important production notes:
- Use HTTPS/WSS through your hosting provider or reverse proxy.
- Set a strong `MINENOVA_SECRET`; do not use the built-in development fallback publicly.
- Put `minenova.db` on persistent storage.
- Back up the database if accounts matter.
- The current matchmaking process is in-memory, so a single server process is recommended. A multi-instance deployment would need Redis or another shared queue/state layer.

---

## Project files

- `index.html` — complete game client/UI
- `server.py` — FastAPI HTTP API + WebSocket matchmaking + SQLite persistence
- `requirements.txt` — Python dependencies
- `start.sh` — macOS/Linux launcher
- `start.bat` — Windows launcher
- `minenova.db` — generated at runtime, not included in the clean package

## API overview

- `POST /api/register` — create account
- `POST /api/login` — login
- `GET /api/me` — profile + cloud progress
- `POST /api/progress` — save cloud progress
- `GET /api/leaderboard` — global ranking
- `GET /api/matches` — signed-in player's match history
- `GET /api/status` — server/queue activity
- `WS /ws/arena?token=...` — queue, live actions, reconnect, emotes, rematches

## Ranked fairness model

Ranked boards are generated and held by the Python server. The client receives only revealed clue values, its own marks/hits, and aggregate opponent progress. Ranked results and rating updates are therefore decided server-side rather than trusting a browser to claim a win.

---

## Easiest hosted deployment

For a ready-to-follow Railway deployment path, see `DEPLOY_RAILWAY.md`. This package also includes a `Dockerfile`, automatic Railway volume detection for `minenova.db`, and `.env.example`.
