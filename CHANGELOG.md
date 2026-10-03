# MineNova 7.0 — Analysis Lab

## New: Analysis Lab
- Stores recent field replays per account/browser.
- Replays show the board state, mouse/cursor path, reveal inputs, flags, chords and timing.
- Scrubbable timeline plus 0.5x / 1x / 2x / 4x playback.
- Field IQ score and grade.
- Tracks first-action time, reveal/flag/chord inputs, wrong flags, missed mines, risky reveals, max hesitation, accuracy, efficiency, mouse travel and score.
- Tracks 25/50/75/100% pacing splits live during a field.
- Tracks completion time for each board quadrant.
- Adds a live pace estimate and grade in the game sidebar.
- Lifetime analysis summary syncs with signed-in cloud progress; detailed replay traces stay local to that account/browser to keep cloud saves small.

## Practice / seed integrity
- Replaying the same seed is now explicitly Practice mode.
- Manually entering a seed also starts a Practice field.
- Practice fields never change XP, records, flag drops, streaks, total chords or daily mission progress.
- Added a visible “Practice seed · no progression” indicator.
- Replaying now preserves the exact displayed seed label and exact original field across repeated replays.

## Fixes
- Final elapsed time is captured exactly when a field ends instead of depending on the last 120 ms timer tick.
- Fixed practice chords being able to increment daily mission progress.
- Fixed repeated seed replay state drifting after replaying more than once.
- Bot/local race analysis now finalizes even when the opponent finishes first.
- Ranked Analysis Lab replays use server snapshots rather than exposing hidden mine locations.
- Analysis history is isolated by signed-in account, matching the rest of MineNova progression.

## Compatibility
- Server version is now 7.0.
- Existing accounts, ratings, flags, profiles, matchmaking and SQLite volume remain compatible.
- Do not wipe the Railway volume when upgrading.
