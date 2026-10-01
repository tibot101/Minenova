# MineNova changelog

## 6.0 — Modern Field
- Refreshed the entire UI toward a modern Minesweeper look while keeping recognizable tile/clue gameplay.
- Rebuilt board rendering so unchanged cells are reused instead of destroyed/recreated.
- Fixed planted flags flickering/restarting their animation during timer and online sync updates.
- Flags now animate only once when actually planted.
- Added an 8-lesson MineNova Academy with visual clue/pattern teaching and a real guided reveal → flag → chord practice board.
- Added fully remappable keyboard controls for solo/online/general actions and both co-op players.
- Fixed local co-op key conflicts with global shortcuts.
- Added 12 selectable account-scoped profile pictures and exposed them safely in public profiles.
- Changed cosmetic rewards to weighted duplicate-capable drops; rare/epic/legendary/mythic flags are substantially harder to pull.
- Added per-flag copy counts and duplicate salvage rewards.
- Added more UI motion: modal/screen transitions, tile reveals, hover/press motion, tutorial pulses, and one-shot flag planting.
- Removed unnecessary board/sidebar rerenders from hot update paths.
- Added visible credits for creator Tibot101.
- Server version bumped to 6.0; no SQLite schema reset is required.

## 5.0 — Mine Room
- Added Mine Room, public profiles, the 36-flag locker, victory drops, board zoom/focus controls, and quality-of-life shortcuts.
- Added account-scoped cosmetic/profile progress and fixed auth initialization.

## 4.0 — Field Desk
- Added Infinity, Bot Arena, left navigation, account-isolated solo progress, and cleaned-up local co-op controls.
