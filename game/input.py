"""Unified input. Every control the game reads comes through here, so remapping happens in one place.

Step 1 covers the keyboard. Joystick and buttons are added in Step 8 and feed the same InputState.
"""

from dataclasses import dataclass

import pygame

import config


@dataclass
class InputState:
    """What the player is asking for this frame."""

    steer: float = 0.0          # -1 = full left, 0 = straight, +1 = full right
    faster: bool = False        # held
    slower: bool = False        # held
    start_pressed: bool = False  # True only on the frame a start button went down


def _key_codes(names):
    return {pygame.key.key_code(name) for name in names}


class InputHandler:
    """Turns pygame events into an InputState. Call begin_frame(), feed events, then read state()."""

    def __init__(self):
        self.left_keys = _key_codes(config.KEYS_STEER_LEFT)
        self.right_keys = _key_codes(config.KEYS_STEER_RIGHT)
        self.faster_keys = _key_codes(config.KEYS_FASTER)
        self.slower_keys = _key_codes(config.KEYS_SLOWER)
        self.start_keys = _key_codes(config.KEYS_START)
        self.held = set()
        self.start_pressed = False

    def begin_frame(self):
        """Clear one-frame events (presses). Held keys carry over."""
        self.start_pressed = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.held.add(event.key)
            if event.key in self.start_keys:
                self.start_pressed = True
        elif event.type == pygame.KEYUP:
            self.held.discard(event.key)
        elif event.type == pygame.WINDOWFOCUSLOST:
            # Key-ups are missed while unfocused; drop everything so nothing gets stuck on.
            self.held.clear()

    def state(self):
        left = bool(self.held & self.left_keys)
        right = bool(self.held & self.right_keys)
        return InputState(
            steer=float(right) - float(left),  # both held cancels out
            faster=bool(self.held & self.faster_keys),
            slower=bool(self.held & self.slower_keys),
            start_pressed=self.start_pressed,
        )
