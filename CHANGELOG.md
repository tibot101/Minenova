# MineNova changelog

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
- Server version bumped to 4.0; existing SQLite schema remains compatible.
