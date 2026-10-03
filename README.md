# MineNova 8.0 - Field Economy

MineNova is a full-stack modern Minesweeper game with solo play, Infinity runs, Bot Arena, local co-op, profiles, cosmetic progression, advanced match analysis, and server-backed ranked PvP.

Created by **Tibot101**.

## What is new in 8.0

### Field Shop and coin economy

MineNova now has an account-scoped coin wallet and a rotating 24-hour cosmetic shop.

Eligible wins pay coins based on:
- safe-cell count
- mine count and field density
- game mode
- clear speed
- clean play
- Infinity round or Bot Arena difficulty where relevant

Large and difficult fields pay substantially more than small fields. Ranked wins and stronger bots have higher payout multipliers. Replayed seeds and manually entered practice seeds pay **zero coins** and cannot be used to farm progression.

The shop rotates globally once every 24 hours and contains eight offers per rotation:
- 3 shop-exclusive flags
- 2 shop-exclusive profile pictures
- 1 profile banner
- 1 nametag
- 1 animated name effect

Shop prices are deterministic for the rotation. Purchases and wallet history are saved per account and cloud synced through the existing progress system.

### New cosmetic types

In addition to the existing field-drop flag collection, players can now collect:
- shop-only flags
- profile banners
- profile pictures
- nametags
- animated username effects

Purchased profile cosmetics can be equipped from the Profile page. Nametags and name effects also appear on supported leaderboard/player-name surfaces. Shop flags cannot appear in normal victory drops.

### Shareable replays

Analysis Lab replays can now be uploaded to the MineNova server and shared with an eight-character replay link. Opening the link loads the replay directly into Analysis Lab.

Replay uploads are sanitized and size-limited by the server. Sharing requires a signed-in account, while viewing a shared replay is public. The server keeps a bounded replay library to prevent uncontrolled database growth.

### Analysis Lab Pro

The post-game analysis system now includes:
- Field IQ
- Pace, Precision, Efficiency, Logic, and Consistency scores
- first-action time
- reveal, flag, and chord input counts
- wrong flags
- missed mines
- flag accuracy
- flag corrections
- repeated inputs
- risky reveals
- longest and average hesitation
- idle-time percentage
- actions per minute
- safe cells per input
- input efficiency
- cursor travel distance
- 25%, 50%, 75%, and 100% board milestones
- quadrant completion times
- personal comparison against recent eligible runs on the same difficulty
- automatic coaching notes
- action heatmap overlay
- replay speeds from 0.25x through 8x
- shareable replay links

The live analysis panel now also shows current efficiency, risk-click count, and inputs per minute in addition to pace and section splits.

### Advanced settings

Settings are now split into Gameplay, Visual, Audio, and Controls sections.

New options include:
- chord-ready glow
- auto pause when an eligible solo tab loses focus
- live-analysis visibility
- timer tenths
- motion level
- victory effect selection
- number color palette
- board grid texture
- board zoom
- sound-effects volume
- the existing fully remappable keybind editor

Victory effects currently include Confetti Burst, Nova Fireworks, Golden Field Sweep, and None.

### Question marks removed

MineNova now uses a simple two-state mark system:

`unmarked -> flag -> unmarked`

There is no question-mark tile state or setting anymore.

### Fixes and integrity changes

- Shop-exclusive flags are excluded from normal victory-drop rolls.
- Economy state uses a timestamp-aware account merge so an older cloud save is less likely to overwrite newer offline wallet progress.
- Replay/practice boards remain excluded from XP, records, flag drops, missions, coins, and competitive progression.
- Public profiles now safely expose equipped banners, nametags, and name effects.
- Ranked leaderboard rows can display equipped profile pictures and username cosmetics.
- Shared replay payloads are sanitized and capped server-side.
- Progress payload capacity was increased for the expanded cosmetic/economy state.
- Long em/en dash characters were removed from website copy.

## Existing modes

### Classic / Sprint / Zen
Beginner, Intermediate, Expert, Master, Custom, seeded practice, and Daily Field.

### Infinity
Clear progressively harder fields in a single run. One loss ends the run.

### Bot Arena
Race an identical board against Rookie, Club Player, Expert, or Nightmare bots.

### Local co-op
Two players share a field. All keyboard controls are remappable in Settings.

### Ranked online
- account login and cloud progress
- Beginner, Intermediate, and Expert queues
- Overall plus three independent ranked leaderboards
- server-authoritative ranked fields/actions
- WebSocket realtime with authenticated HTTP fallback
- reconnect grace, emotes, rematches, and match history

## Account-scoped progression

Each signed-in player keeps separate:
- XP and solo records
- Infinity progress
- Bot Arena record
- keybinds and settings
- Analysis lifetime stats
- coin wallet and purchase history
- profile picture, banner, nametag, and name effect
- flags and duplicate counts
- equipped cosmetics
- daily drill progress

Guest data remains separate from every signed-in account.

## Run locally

```bash
python -m pip install -r requirements.txt
python server.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Update Railway

Keep the same Railway project, service, GitHub repository, `/data` volume, domain, and `MINENOVA_SECRET`.

Replace the source files in the same GitHub repository with the 8.0 files and commit them. Do not wipe `minenova-volume`.

After Railway reports **Active**, check:

```text
https://YOUR-SITE/health
```

It should include:

```json
{"ok":true,"version":"8.0"}
```

Then hard-refresh once with `Ctrl + Shift + R`.

8.0 adds the `shared_replays` SQLite table automatically with `CREATE TABLE IF NOT EXISTS`, so existing accounts, ranked ratings, history, and progress remain compatible.

## Production notes

- Keep `MINENOVA_SECRET` private.
- Keep SQLite on the persistent `/data` volume.
- Keep one Railway replica for now because active matchmaking state is in process memory.
- Do not commit `minenova.db` or a real `.env` file.
- Replay sharing uses database storage. The server keeps only the newest bounded set of shared replays.
