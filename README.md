# Combine Them! (Pygame)

Combine Them! is a small, single-file prototype of a "merge" incremental game built with Pygame. Merge coins to produce higher-value coins, sell them to influence a simple market, unlock more slots, and prestige for permanent bonuses.

This repository is intended for experimentation and quick iteration — the main game file is `game.py` so you can inspect and modify gameplay quickly.

Badges
- Python 3.8+ recommended
- Pygame 2.x

Quick start

1. Create and activate a virtual environment (optional but recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the game:

```bash
python3 game.py
```

Core features

- Drag-and-drop coin placement and merging.
- "Deal" spawns coins (one per unlocked slot).
- Buy specific coin levels or unlock additional slots via the Upgrades menu.
- Sell coins to earn currency — sales affect a simple market price model and a small chart.
- Prestige resets progress for a permanent multiplier.
-- Save/load game state to `save.json`.

Controls

- Click `Deal Coins` to spawn coins.
- Click `Buy Coins` → choose `Buy C#` to purchase a coin at that level.
- Click `Upgrades` → `Buy Slot` to expand your board, or buy Worker / Time Thief upgrades.
- Shift+click a slot to open the Sell popup (sell 1 / 5 / all).
- Drag a coin from a slot to another to add or merge.
- Use `Save` / `Load` buttons to persist progress.

Developer notes

-- Main code: `game.py` (single-file prototype).
- Dependencies are listed in `requirements.txt` (Pygame 2.x).
- The game attempts to use `pygame.font` or `pygame.freetype` and falls back to a tiny 5x7 bitmap renderer if neither is available.
- The spawn/market logic is intentionally simple and designed to be easy to tweak while you experiment.

Recommended edits

- Tweak constants near the top of `game.py` (cooldowns, costs, slot caps) to experiment with balance.
- The bitmap glyphs live in `BITMAP_FONT` inside `game.py` — add glyphs if you need more characters in the fallback renderer.

Contributing

This is a small prototype — open an issue or submit a PR with improvements. Helpful contributions include UI polish, balancing changes, or packaging the project for distribution.

License

This project is provided under the MIT License.

---
