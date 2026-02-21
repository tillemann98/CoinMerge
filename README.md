# Combine Them! (Pygame)

A small prototype combine/merge incremental game built with Pygame.

## Prerequisites

- Python 3.8+ (use your system Python or a virtualenv)
- `pygame` (listed in `requirements.txt`)

## Install

```bash
python3 -m venv venv        # optional
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 "CombinerGame2/game.py"
```

## Controls

- `Deal Coins`: deal coins (one per unlocked slot)
- `Buy Slot`: buy another slot (cost scales)
- `Buy C#`: purchase a specific coin level (labels show price)
- `Prestige`: reset progress to gain a permanent multiplier
- Drag a coin from one slot to another to place or combine it

## Save / Load

- Use the Save and Load buttons to write/read `CombinerGame2/save.json`.

## Notes & Troubleshooting

- The game attempts to use pygame font backends and falls back to a small bitmap renderer if platform font modules fail; if text looks incorrect, try updating `pygame` or installing system fonts.
- If you see crashes related to fonts, reinstalling pygame in a fresh virtualenv often helps.

## Development

- Main code: `CombinerGame2/game.py`
- If you want UI layout, font, or color tweaks, tell me what to change and I'll update the code.
