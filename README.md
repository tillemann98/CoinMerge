# Combine Them! (Pygame)

Combine Them! is a small prototype "combine/merge" incremental game built with Pygame. Merge coins to create higher-value coins, sell to influence an in-game market, and unlock slots and prestige upgrades.

This repository contains a single-file prototype ideal for experimentation and iteration.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/pygame-%3E%3D2.1-brightgreen.svg)](https://www.pygame.org/)

## Features

- Drag-and-drop coin placement and merging
- Deal (spawn) coins, buy specific coin levels, buy additional slots
- Sell coins — sales affect a simple market price model and chart
- Prestige mechanic that grants a permanent multiplier
- Save/load to JSON

## Prerequisites

- Python 3.8+ (system Python or virtualenv)
- See `requirements.txt` for Python package requirements

## Install

```bash
python3 -m venv venv   # optional
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 "CombinerGame2/game.py"
```

## Controls

- Click `Deal Coins` to spawn coins (one per unlocked slot)
- Click `Buy Coins` → choose `Buy C#` to purchase a coin of that level
- Click `Upgrades` → `Buy Slot` to expand your board
- Shift+click a slot to open the Sell popup (sell 1 / 5 / all)
- Drag a coin from a slot to another slot to add or merge
- Use `Save` / `Load` to persist progress to `CombinerGame2/save.json`

## Screenshot

Screenshot from the game

![screenshot placeholder](/assets/screenshot.png)

## Development notes

- Main code: [CombinerGame2/game.py](CombinerGame2/game.py)
- Requirements: `requirements.txt` (install via pip)
- The game tries `pygame.font` and `pygame.freetype` and falls back to a small bitmap renderer if needed.
- The market uses recent sales history to compute prices; player sells have amplified immediate impact to make market feedback visible in a prototype setting.

### Project layout

- `CombinerGame2/game.py` — main prototype file
- `CombinerGame2/save.json` — save file created by the game (not tracked by git by default)
- `CombinerGame2/assets/` — optional screenshots or assets

### Notes on fonts and display

The prototype attempts to use system font backends. If text looks off, try running in a virtualenv and ensure `pygame` is installed correctly on your platform.

## Contributing

Open an issue or submit a PR with improvements. For UI or balancing tweaks mention expected behavior and screenshots if possible.

## License

This project is provided under the MIT license — see `LICENSE` in the repository for details.

---

If you'd like, I can also add CI badges, a small contributing guide, or create a sample GitHub Actions workflow to run a simple static check. Which would you prefer next?
