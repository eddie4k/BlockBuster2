# BlockBuster2

Python CLI that sends a configured sequence of keypresses to the focused window
(keyboard automation prototype for private Jstris practice/testing). Entry point:
`src/jstris_keyboard_controller.py`. See `README.md` for full usage.

## Cursor Cloud specific instructions

- Dependencies: `pip install -r requirements.txt` (just `PyAutoGUI`). The update
  script already does this on startup.
- System dependency `python3-tk` is required and is baked into the VM snapshot.
  Reason: `import pyautogui` pulls in `mouseinfo`, which calls `sys.exit()` (not
  `ImportError`) when `tkinter` is missing. Because `pyautogui` only catches
  `ImportError`, a missing `tkinter` makes `import pyautogui` terminate the whole
  process with exit code 1 — silently breaking the real key-send path. If a future
  VM lacks it, reinstall with `sudo apt-get install -y python3-tk`.
- `PyAutoGUI` sends OS-level keystrokes to the X display. The cloud desktop is on
  `DISPLAY=:1`. To run the real (non-dry-run) controller from a non-GUI shell,
  export `DISPLAY=:1` first; otherwise keypresses have no target.
- Commands:
  - Tests: `python3 -m unittest discover` (run from repo root).
  - Run (no display needed): `python3 src/jstris_keyboard_controller.py --dry-run <seq>`
    or `--list-actions`.
  - Run (real keystrokes, needs display): focus the target window, then
    `DISPLAY=:1 python3 src/jstris_keyboard_controller.py --start-delay 0 <seq>`.
- No linter is configured in the repo; `python3 -m py_compile` is a reasonable
  syntax check.
