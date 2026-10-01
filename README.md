# MineNova 6.0 — Modern Field

MineNova is a full-stack Minesweeper game with solo play, Infinity runs, Bot Arena, local co-op, account-scoped progression, collectible flags, public profiles, and server-backed ranked PvP.

Created by **Tibot101**.

## What is new in 6.0

### Modern Minesweeper visual refresh
- Reworked the 5.0 workbench/classic look into a cleaner modern field UI while keeping recognizable Minesweeper tiles and clue colors.
- Modern dark minefield backdrop, cleaner navigation, softer depth, tighter board chrome, and responsive hover/press/reveal motion.
- High-contrast clue colors for 1–8.
- Stable planted flags: unchanged cells are no longer destroyed and rebuilt during timer/online updates.
- One-shot planting motion only when a flag is actually placed.
- Modal, screen, board-reveal, button, tutorial-target, and reward animations with `prefers-reduced-motion` support.

### MineNova Academy tutorial
The tutorial is now an 8-lesson visual course:
1. Clear safe tiles
2. Read number clues
3. Flag known mines
4. Chord safely
5. Recognize the 1–2–1 pattern
6. Mouse and keyboard controls
7. Game modes
8. Guided practice

The guided practice runs on a real training board and walks through **reveal → flag → chord**. The controls lesson displays the player's current remapped keys.

### Fully remappable controls
Settings now contains a keybind editor for:
- Solo/online movement
- Reveal, flag, and chord
- Pause, New Field, replay, home, locker, and focus mode
- Both local co-op players
- Mouse-owner swap

Keybinds are saved per account and synced with cloud progress. Mouse/touch controls always remain available.

### Profile pictures
- Added 12 selectable profile-picture badges.
- The selected picture appears in the account chip, Mine Room, and public profile.
- Profile picture, title, and field note are account-scoped and cloud synced.

### Duplicate flag drops
The Flag Locker still contains 36 flags across:
- Common
- Uncommon
- Rare
- Epic
- Legendary
- Mythic

Wins now roll from the **entire** loot table, so duplicates are possible from the beginning. Higher rarities have much lower drop weights, making strong cosmetics genuinely difficult to collect.

The locker tracks copy counts (`×2`, `×3`, etc.). Duplicate drops also give a small salvage bonus, with rarer duplicates worth more salvage.

### Performance and bug fixes
- Fixed flags appearing to reload/flicker on repeated HUD and online updates.
- Board rendering now reuses existing cell DOM nodes and only updates cells whose visible state changed.
- Removed an expensive full sidebar/home rerender from the 120 ms HUD timer.
- Fixed a local co-op/global-shortcut conflict by routing multiplayer controls before global shortcuts.
- Settings no longer rebuild the board for unrelated preference changes.
- Public profiles now expose the selected profile picture safely through the server API.
- Existing WebSocket + HTTP fallback matchmaking remains compatible.

## Game modes

### Classic / Sprint / Zen
Beginner, Intermediate, Expert, Master, Custom, seeded boards, and the Daily Field.

### Infinity
Clear increasingly difficult boards in one run. One loss ends the run. Best round and total clears are saved per account.

### Bot Arena
Race an identical board against:
- Rookie
- Club Player
- Expert
- Nightmare

The bot uses visible clues and risk estimates rather than reading hidden mines directly.

### Local co-op
All keyboard controls are remappable in Settings. Defaults:

Player 1:
- `W A S D` move
- `Space` reveal
- `F` flag
- `G` chord

Player 2:
- Arrow keys move
- `Enter` reveal
- `Right Shift` flag
- `\\` chord

`Tab` swaps mouse ownership.

### Ranked online
- Account login and cloud progress
- Beginner / Intermediate / Expert queues
- Overall + three independent ranked leaderboards
- Server-authoritative boards/actions
- WebSocket realtime with authenticated HTTP-sync fallback
- Reconnect grace, emotes, rematches, and match history

## Account-scoped progress

Each signed-in account has its own:
- XP and level
- best times and solo wins
- Infinity progress
- Bot Arena record
- keybinds and gameplay settings
- board zoom
- profile picture, title, and field note
- equipped flag, flag copies, and reward history
- daily drill progress

Guest progress is stored separately from every account.

## Run locally

```bash
python -m pip install -r requirements.txt
python server.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Update the live Railway deployment

Use the **same Railway service, GitHub repository, `/data` volume, domain, and `MINENOVA_SECRET`**.

Replace the old source files in the same GitHub repository with the 6.0 files and commit them. Let Railway deploy the newest commit.

Do **not** wipe `minenova-volume`.

After Railway reports **Active**, check:

```text
https://YOUR-SITE/health
```

It should contain:

```json
{"ok":true,"version":"6.0"}
```

Then hard-refresh the game once (`Ctrl + Shift + R`).

Existing accounts, ratings, match history, leaderboards, and progress remain compatible because the new profile/cosmetic data continues to live inside the existing `progress_json` field.

## Main files

- `index.html` — game client and UI
- `server.py` — FastAPI accounts, profiles, rankings, matchmaking, WebSockets, and SQLite
- `requirements.txt` — Python dependencies
- `Dockerfile` — Railway/container deployment
- `DEPLOY_RAILWAY.md` — hosting/update instructions
- `CHANGELOG.md` — release history

## Production notes

- Keep `MINENOVA_SECRET` private.
- Keep the SQLite database on persistent `/data` storage.
- Keep one Railway replica for now because active match state is in server memory.
- Do not commit `minenova.db` or a real `.env` file.
