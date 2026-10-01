# MineNova 4.0 — Field Desk

MineNova 4.0 is a full-stack Minesweeper game with solo play, Infinity runs, bot races, local co-op, account-scoped progression, and real server-backed ranked PvP.

## What changed in 4.0

### New visual direction
- Reworked the site into a darker field-desk / minefield style instead of a neon dashboard.
- Added a permanent left navigation rail for Play, Infinity, Bot Arena, Online PvP, Leaderboards, Tutorial, and Settings.
- Redesigned the board frame, cells, panels, buttons, stats, flags, overlays, and background to feel more like a deliberately designed game UI.
- Reduced decorative gradients/glass effects and made the visual hierarchy flatter and more tactile.

### Power system removed
- Safe Hint, Pulse Scan, Shield, and the old power panel are gone from normal play.
- Core Minesweeper mechanics are now the focus: revealing, flagging, deduction, chording, speed, seeds, and modes.

### Infinity Mode
- Starts with a small field.
- Every clear advances to a larger and/or denser round.
- One loss ends the run.
- Tracks best round and total Infinity clears.
- Infinity progress is included in account cloud progress.

### Bot Arena
Race your own field against a bot on an identical board.

Bot levels:
- **Rookie** — slow and guess-heavy.
- **Club Player** — uses basic forced moves and moderate risk selection.
- **Expert** — faster clue solving and better risk selection.
- **Nightmare** — very fast and rarely makes intentionally poor choices.

The bot works from revealed clues/flags and risk estimates rather than simply reading the hidden answer map for every move.

### Account-scoped progress fix
Solo progress no longer follows you when you switch accounts.

Each signed-in account now gets its own browser cache and its own server-side cloud progress for:
- XP / level
- solo wins
- chord totals
- personal best times
- daily mission progress
- Infinity best / clears
- Bot Arena records
- theme / flag style / gameplay preferences

Guest progress is stored separately too.

Existing ranked rating, ranked wins/losses, mode ratings, and match history remain server-side as before.

The account screen also has **Reset solo progress** for cleaning up an account that may already have inherited old shared-browser progress from pre-4.0 versions. It does not reset ranked ratings/history.

### Local co-op control cleanup
Player 1:
- `W A S D` — move
- `Space` — reveal
- `F` — flag
- `G` — chord

Player 2:
- Arrow keys — move
- `Enter` — reveal
- `M` — flag
- `N` — chord

Shared:
- `Tab` — switch mouse/touch ownership
- click — reveal / chord
- right-click / touch long-press — mark

### Online ranked remains server-authoritative
- Real account login and JWT sessions
- Beginner / Intermediate / Expert matchmaking queues
- Separate boards generated from the same server-owned hidden field
- Server validates reveal, flag, and chord actions
- WebSocket realtime with authenticated HTTP fallback
- reconnect grace period
- rematches and quick emotes
- Overall + Beginner + Intermediate + Expert leaderboards
- persistent match history and ratings in SQLite

### Update/cache fix
The server now serves `index.html` with no-cache headers, so deployments are less likely to leave players stuck on an older client after Railway updates.

---

## Run locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start MineNova:

```bash
python server.py
```

Then open:

```text
http://127.0.0.1:8000
```

The server creates `minenova.db` automatically if no persistent database path is configured.

## Railway

Keep the same Railway project, `/data` volume, and `MINENOVA_SECRET` when upgrading an existing deployment. Do **not** wipe the volume.

Upload/commit the new project files to the same connected GitHub repository. Railway should redeploy automatically. After deployment, check:

```text
https://YOUR-SITE/health
```

MineNova 4.0 returns a response containing:

```json
{"ok":true,"version":"4.0"}
```

See `DEPLOY_RAILWAY.md` for the full deployment setup.

## Main files

- `index.html` — complete game client and UI
- `server.py` — FastAPI API, accounts, ranked matchmaking, WebSockets, SQLite
- `requirements.txt` — Python dependencies
- `Dockerfile` — hosted deployment image
- `start.sh` / `start.bat` — local launchers

## Production notes

- Keep `MINENOVA_SECRET` private.
- Keep the SQLite database on persistent storage (`/data` on the recommended Railway setup).
- Keep MineNova at one server replica for now because live matchmaking state is in memory.
- Do not commit `minenova.db` or `.env`.
