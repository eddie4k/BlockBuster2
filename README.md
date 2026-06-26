# BlockBuster2

Keyboard automation prototype for controlling
[Jstris](https://jstris.jezevec10.com/) in private practice or testing sessions.

This project does **not** read game state or play competitively on your behalf.
It sends a configured sequence of keypresses to the active browser window, so use
it only where automation is allowed, such as local practice, private rooms, or
accessibility experiments.

## Setup

```bash
python -m pip install -r requirements.txt
```

PyAutoGUI sends OS-level keyboard input. On Linux, you may need a desktop session
with keyboard automation permissions and packages that support screen/keyboard
control for your display server.

## Basic usage

1. Open <https://jstris.jezevec10.com/> in a browser.
2. Start a private practice game.
3. Run the controller with a short start delay.
4. Click/focus the Jstris game before the countdown finishes.

Dry-run a sequence first:

```bash
python src/jstris_keyboard_controller.py --dry-run left*2 rotate hard_drop
```

Send the same sequence after a 3 second focus countdown:

```bash
python src/jstris_keyboard_controller.py left*2 rotate hard_drop
```

Useful examples:

```bash
# Hold, rotate counter-clockwise, hard drop.
python src/jstris_keyboard_controller.py hold ccw drop

# Move right three times, wait briefly, rotate, then hard drop.
python src/jstris_keyboard_controller.py right*3 wait:0.15 cw hd

# Use a slower cadence between keypresses.
python src/jstris_keyboard_controller.py --delay 0.12 left left rotate drop
```

## Supported actions

Run:

```bash
python src/jstris_keyboard_controller.py --list-actions
```

Default action mappings:

| Action | Default key |
| --- | --- |
| `left` | Left arrow |
| `right` | Right arrow |
| `soft_drop` | Down arrow |
| `hard_drop` | Space |
| `rotate_cw` | Up arrow |
| `rotate_ccw` | Z |
| `rotate_180` | A |
| `hold` | C |

Aliases include `l`, `r`, `sd`, `drop`, `hd`, `cw`, `ccw`, `180`, and `h`.

## Custom key bindings

If your Jstris controls differ from the defaults, create a JSON file such as:

```json
{
  "hold": "shift",
  "rotate_cw": "x",
  "hard_drop": "space"
}
```

Then run:

```bash
python src/jstris_keyboard_controller.py --config my-keys.json hold rotate drop
```

The key names are PyAutoGUI key names.

## Tests

```bash
python -m unittest discover
```
