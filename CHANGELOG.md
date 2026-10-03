# MineNova changelog

## 8.0 - Field Economy

### Added
- Account-scoped coin wallet.
- Size, density, mode, speed, and clean-play based coin payouts.
- 24-hour global rotating Field Shop.
- Shop-exclusive flags.
- Shop-exclusive profile pictures.
- Profile banners.
- Collectible nametags.
- Animated username effects.
- Lifetime earned/spent and daily wallet stats.
- Shareable Analysis Lab replay links.
- Server-backed replay storage with public replay viewing.
- Replay action heatmap.
- Personal same-difficulty performance comparisons.
- Analysis coaching notes.
- Pace, Precision, Efficiency, Logic, and Consistency breakdowns.
- Flag accuracy, flag correction, repeated-input, idle-time, APM, and safe-cells-per-input metrics.
- Live efficiency, risk, and input-rate stats.
- Advanced Gameplay / Visual / Audio / Controls settings pages.
- Multiple victory effect styles.
- Sound volume control.
- Motion-level, timer-tenths, board-grid, number-palette, and chord-glow controls.
- Leaderboard profile pictures, nametags, and name effects.

### Changed
- Question-mark marking was removed. Right-click now strictly toggles flags.
- Shop-only flags are visible in the locker but cannot drop from normal wins.
- Analysis Lab was renamed and expanded to Analysis Lab Pro.
- Progress payload allowance increased for expanded account data.
- Website copy no longer uses em or en dashes.

### Fixed
- Replayed/manual seeds cannot earn coins or other progression.
- Same eligible seed reward keys prevent accidental duplicate coin payout.
- Shop flags no longer leak into the normal flag-drop table.
- Economy merge prefers the newer wallet state when cloud/local progress differs.
- Shop avatar/profile ownership is validated before equipping.
- Public cosmetic rendering falls back safely for unknown IDs.
- Shared replays are validated, sanitized, size capped, and database bounded.

## 7.0 - Analysis Lab
- Detailed local replay telemetry and cursor playback.
- Field IQ, live pacing, splits, mistakes, hesitation, accuracy, efficiency, and travel metrics.
- Practice-seed progression integrity.
