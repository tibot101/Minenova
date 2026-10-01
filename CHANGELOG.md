# MineNova changelog

## 5.0 — Mine Room
- Added the Mine Room home hub with quick play, account summary, daily field, recent flag drops, and online status.
- Completely reworked the board into a more classic physical Minesweeper style with a framed workbench presentation, beveled closed tiles, flat revealed tiles, clearer numbers, and a classic face/replay button.
- Added 36 collectible flags across Common, Uncommon, Rare, Epic, Legendary, and Mythic rarities.
- Added victory flag drops and a full Flag Locker with equipping and collection tracking.
- Added public profiles with field notes, equipped flags, solo stats, ranked stats, mode ratings, joined date, and unlockable titles.
- Leaderboard player names now open profiles.
- Added account-scoped board zoom, focus mode, copy-seed action, and N/R/H/L keyboard shortcuts.
- Added the missing `initAuth()` flow so saved sessions correctly restore account/cloud progress and reconnect multiplayer after page load.
- Fixed tutorial step indicators using a mismatched CSS class.
- Extended account cloud progress to include cosmetics, profiles, board zoom, reward history, and equipped flags.
- Server version bumped to 5.0; the existing SQLite database schema remains compatible.

## 4.0 — Field Desk
- New handcrafted field-desk visual direction and left navigation rail.
- Removed gameplay powers including Pulse Scan, Safe Hint and Shield.
- Added Infinity Mode with escalating endless rounds.
- Added Bot Arena with Rookie, Club Player, Expert and Nightmare bots.
- Fixed solo progress leaking between accounts by namespacing browser caches per account and continuing to use server-side cloud progress per user.
- Added current-account solo progress reset for cleaning up older contaminated profiles without touching ranked ratings/history.
- Improved local co-op/PvP keybinds: P1 Space/F/G, P2 Enter/M/N.
- Fixed bot-board mouse interaction so the human cannot click the bot's field.
- Fixed replay behavior for ranked, bot and Infinity modes.
- Added no-cache response headers for the main client to reduce stale Railway deployments in browsers.
