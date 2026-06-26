"""Keyboard automation helper for private Jstris practice/testing.

The OS-level keyboard backend intentionally stays behind a tiny interface so
the parser and command planning can be tested without pressing real keys.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Protocol


DEFAULT_KEY_BINDINGS: dict[str, str] = {
    "left": "left",
    "right": "right",
    "soft_drop": "down",
    "hard_drop": "space",
    "rotate_cw": "up",
    "rotate_ccw": "z",
    "rotate_180": "a",
    "hold": "c",
}

ACTION_ALIASES: dict[str, str] = {
    "l": "left",
    "r": "right",
    "sd": "soft_drop",
    "down": "soft_drop",
    "drop": "hard_drop",
    "hd": "hard_drop",
    "space": "hard_drop",
    "cw": "rotate_cw",
    "rotate": "rotate_cw",
    "ccw": "rotate_ccw",
    "z": "rotate_ccw",
    "180": "rotate_180",
    "flip": "rotate_180",
    "h": "hold",
}

WAIT_PREFIXES = ("wait:", "sleep:")


@dataclass(frozen=True)
class PlannedCommand:
    """A resolved keypress or wait in an automation sequence."""

    action: str
    key: str | None = None
    wait_seconds: float | None = None

    @property
    def is_wait(self) -> bool:
        return self.wait_seconds is not None


class KeyboardBackend(Protocol):
    """Sends keyboard input to whichever window currently has focus."""

    def press(self, key: str, press_duration: float) -> None:
        ...


class PyAutoGuiBackend:
    """Keyboard backend using PyAutoGUI."""

    def __init__(self) -> None:
        try:
            import pyautogui
        except ImportError as exc:  # pragma: no cover - exercised manually
            raise RuntimeError(
                "PyAutoGUI is not installed. Install dependencies with "
                "`python -m pip install -r requirements.txt`."
            ) from exc

        pyautogui.FAILSAFE = True
        self._pyautogui = pyautogui

    def press(self, key: str, press_duration: float) -> None:
        if press_duration <= 0:
            self._pyautogui.press(key)
            return

        self._pyautogui.keyDown(key)
        time.sleep(press_duration)
        self._pyautogui.keyUp(key)


def normalize_action(raw_action: str) -> str:
    action = raw_action.strip().lower().replace("-", "_")
    return ACTION_ALIASES.get(action, action)


def parse_wait_seconds(token: str) -> float | None:
    lower_token = token.lower()
    for prefix in WAIT_PREFIXES:
        if lower_token.startswith(prefix):
            raw_seconds = token[len(prefix) :]
            try:
                seconds = float(raw_seconds)
            except ValueError as exc:
                raise ValueError(f"Invalid wait value in token `{token}`") from exc

            if seconds < 0:
                raise ValueError(f"Wait value must be non-negative in token `{token}`")
            return seconds
    return None


def split_sequence(raw_sequence: Iterable[str]) -> list[str]:
    tokens: list[str] = []
    for raw_chunk in raw_sequence:
        for comma_part in raw_chunk.split(","):
            tokens.extend(part for part in comma_part.split() if part)
    return tokens


def expand_token(token: str) -> tuple[str, int]:
    if "*" not in token:
        return token, 1

    base, raw_count = token.rsplit("*", 1)
    if not base:
        raise ValueError(f"Missing action before repeat count in token `{token}`")

    try:
        count = int(raw_count)
    except ValueError as exc:
        raise ValueError(f"Invalid repeat count in token `{token}`") from exc

    if count < 1:
        raise ValueError(f"Repeat count must be at least 1 in token `{token}`")
    return base, count


def plan_sequence(
    raw_sequence: Iterable[str],
    key_bindings: Mapping[str, str] | None = None,
) -> list[PlannedCommand]:
    bindings = dict(DEFAULT_KEY_BINDINGS)
    if key_bindings:
        bindings.update(key_bindings)

    planned: list[PlannedCommand] = []
    for token in split_sequence(raw_sequence):
        base_token, repeat_count = expand_token(token)
        wait_seconds = parse_wait_seconds(base_token)
        if wait_seconds is not None:
            planned.extend(
                PlannedCommand(action="wait", wait_seconds=wait_seconds)
                for _ in range(repeat_count)
            )
            continue

        action = normalize_action(base_token)
        key = bindings.get(action)
        if key is None:
            known_actions = ", ".join(sorted(bindings))
            raise ValueError(f"Unknown action `{base_token}`. Known actions: {known_actions}")

        planned.extend(
            PlannedCommand(action=action, key=key) for _ in range(repeat_count)
        )

    if not planned:
        raise ValueError("No actions were provided")
    return planned


def load_key_bindings(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}

    with path.open("r", encoding="utf-8") as handle:
        raw_bindings = json.load(handle)

    if not isinstance(raw_bindings, dict):
        raise ValueError("Key binding config must be a JSON object")

    bindings: dict[str, str] = {}
    for raw_action, raw_key in raw_bindings.items():
        if not isinstance(raw_action, str) or not isinstance(raw_key, str):
            raise ValueError("Key binding config keys and values must be strings")
        bindings[normalize_action(raw_action)] = raw_key
    return bindings


def run_plan(
    planned_commands: Iterable[PlannedCommand],
    backend: KeyboardBackend,
    *,
    delay: float,
    press_duration: float,
) -> None:
    for command in planned_commands:
        if command.is_wait:
            time.sleep(command.wait_seconds or 0)
            continue

        if command.key is None:
            raise RuntimeError(f"Action `{command.action}` has no resolved key")
        backend.press(command.key, press_duration)
        time.sleep(delay)


def print_countdown(seconds: float) -> None:
    if seconds <= 0:
        return

    deadline = time.monotonic() + seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            print("Sending keys now.")
            return
        print(f"Focus the Jstris game window... {remaining:.1f}s", end="\r")
        time.sleep(min(0.25, remaining))


def format_plan(planned_commands: Iterable[PlannedCommand]) -> str:
    formatted: list[str] = []
    for command in planned_commands:
        if command.is_wait:
            formatted.append(f"wait:{command.wait_seconds:g}")
        else:
            formatted.append(f"{command.action}({command.key})")
    return " -> ".join(formatted)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Send a sequence of keyboard actions to the focused Jstris browser "
            "window. Use only in private practice/testing contexts."
        )
    )
    parser.add_argument(
        "sequence",
        nargs="*",
        help=(
            "Actions to send, separated by spaces or commas. Examples: "
            "`left*2 rotate hard_drop`, `hold,ccw,drop`, `wait:0.2 left drop`."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional JSON object mapping action names to PyAutoGUI key names.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Delay in seconds after each keypress. Default: %(default)s",
    )
    parser.add_argument(
        "--press-duration",
        type=float,
        default=0.0,
        help="How long to hold each key down. Default sends a quick press.",
    )
    parser.add_argument(
        "--start-delay",
        type=float,
        default=3.0,
        help="Seconds to wait before sending keys so you can focus the game.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved sequence without sending keypresses.",
    )
    parser.add_argument(
        "--list-actions",
        action="store_true",
        help="Show available action names and default key bindings.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.delay < 0 or args.press_duration < 0 or args.start_delay < 0:
        parser.error("--delay, --press-duration, and --start-delay must be non-negative")

    bindings = load_key_bindings(args.config)
    effective_bindings = {**DEFAULT_KEY_BINDINGS, **bindings}

    if args.list_actions:
        for action, key in sorted(effective_bindings.items()):
            print(f"{action}: {key}")
        return 0

    try:
        planned_commands = plan_sequence(args.sequence, bindings)
    except ValueError as exc:
        parser.error(str(exc))

    print(format_plan(planned_commands))
    if args.dry_run:
        return 0

    print_countdown(args.start_delay)
    backend = PyAutoGuiBackend()
    run_plan(
        planned_commands,
        backend,
        delay=args.delay,
        press_duration=args.press_duration,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
