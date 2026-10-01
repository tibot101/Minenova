# MineNova 5.0 — Mine Room

MineNova is a full-stack Minesweeper game with classic solo play, Infinity runs, bot races, local co-op, cloud accounts, public player profiles, cosmetic flag collecting, and server-backed ranked PvP.

## What is new in 5.0

### Mine Room redesign
- New Mine Room home hub instead of dropping straight into a dashboard.
- Handcrafted workbench / clubhouse visual direction with a physical-looking board frame.
- Classic beveled Minesweeper tiles with clearer revealed squares and number colors.
- Left navigation for Mine Room, Play, Infinity, Bot Arena, Online PvP, Flag Locker, Profiles, Leaderboards, Tutorial, and Settings.
- New classic face/replay button in the field console.
- Cleaner typography, less glass/neon styling, and fewer decorative panels.

### Flag Locker and victory drops
There are **36 collectible flags** across six rarities:
- Common
- Uncommon
- Rare
- Epic
- Legendary
- Mythic

Eligible victories award a new flag until the collection is complete. Rewards come from solo clears, Infinity rounds, Bot Arena wins, local co-op clears, and ranked wins. Once the collection is complete, wins convert to bonus XP instead.

Each flag has its own colors, shape, marking, and rarity. The equipped flag appears on the game board and on the public profile.

### Public player profiles
- Player profile card with username, title, equipped flag, joined date, ranked record, solo wins, Infinity best, Bot Arena wins, and collection size.
- Beginner / Intermediate / Expert ranked ratings shown on the profile.
- Editable public field note for the current account.
- Unlockable profile titles based on actual progress.
- Leaderboard names open their player profile.

### Quality-of-life pass
- Per-account board zoom with `− / 100% / +` controls.
- Focus mode for a distraction-free board.
- Face button instantly replays the current seed.
- Copy-seed button.
- `N` opens New Field.
- `R` replays the current field.
- `H` returns to the Mine Room.
- `L` opens the Flag Locker.
- `Esc` exits focus mode.
- Existing keyboard reveal/flag/chord controls remain.
- Home screen shows quick play, daily field, account stats, current flag, recent drops, and server status.

### Bugs fixed in 5.0
- Added the missing automatic authentication initializer. Stored login sessions now actually restore the account, cloud progress, and realtime connection on page load.
- Fixed tutorial progress dots using the wrong CSS class.
- Kept account progress isolated when switching users.
- Public profile data is sanitized on the server and never exposes password hashes or private session data.
- Ranked matchmaking, HTTP fallback, mode leaderboards, and the existing SQLite schema remain compatible.

## Existing game modes

### Solo
- Beginner, Intermediate, Expert, Master, and Custom boards.
- Classic, Sprint, Zen, seeded games, and Daily Field.
- First-click protection and chording.

### Infinity
Clear a board to move into a larger/denser round. One loss ends the run. Best round and total clears are saved per account.

### Bot Arena
Race an identical board against:
- Rookie
- Club Player
- Expert
- Nightmare

The bot uses visible clues, forced moves, and risk estimates instead of simply revealing every hidden mine location.

### Local co-op
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

`Tab` switches mouse ownership.

### Ranked online
- Real accounts and JWT sessions.
- Beginner / Intermediate / Expert queues.
- Server-authoritative minefields and actions.
- WebSocket realtime with authenticated HTTP fallback.
- Reconnect grace period, rematches, emotes, and match history.
- Overall + three independent mode leaderboards.

## Account-scoped cloud progress

Each account has separate:
- XP and level
- solo wins and best times
- chords and daily drill
- Infinity progress
- Bot Arena records
- settings and board zoom
- public profile note/title
- unlocked flags and equipped flag
- reward history

Guest progress is separate from every signed-in account.

## Run locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start MineNova:

```bash
python server.py
```

Open:

```text
http://127.0.0.1:8000
```

## Railway update

Keep your existing Railway service, `/data` volume, database, domain, and `MINENOVA_SECRET`.

Replace the old project files in the same GitHub repository with the 5.0 files and commit them. Railway should redeploy automatically.

After deployment, open:

```text
https://YOUR-SITE/health
```

You should see a response containing:

```json
{"ok":true,"version":"5.0"}
```

Do **not** wipe the Railway volume when updating. Existing accounts, ratings, match history, and progress are migrated through the existing `progress_json` field and remain compatible.

See `DEPLOY_RAILWAY.md` for the hosting setup.

## Main files

- `index.html` — full game client/UI
- `server.py` — FastAPI API, accounts, public profiles, matchmaking, WebSockets, SQLite
- `requirements.txt` — Python dependencies
- `Dockerfile` — deployment image
- `start.sh` / `start.bat` — local launchers

## Production notes

- Keep `MINENOVA_SECRET` private.
- Keep SQLite on persistent storage (`/data` on Railway).
- Keep one server replica for now because active matchmaking state is held in memory.
- Do not commit `minenova.db` or `.env`.
