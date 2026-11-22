"""Step 1: keyboard input module."""

import random

import pygame
import pytest

import main
from game.input import InputHandler


@pytest.fixture
def controls():
    pygame.init()
    yield InputHandler()
    pygame.quit()


def down(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def up(key):
    return pygame.event.Event(pygame.KEYUP, key=key)


def feed(controls, *events):
    controls.begin_frame()
    for event in events:
        controls.handle_event(event)
    return controls.state()


def test_nothing_pressed_is_neutral(controls):
    state = feed(controls)
    assert (state.steer, state.faster, state.slower, state.start_pressed) == (0.0, False, False, False)


def test_left_and_right_steer(controls):
    assert feed(controls, down(pygame.K_LEFT)).steer == -1.0
    assert feed(controls, up(pygame.K_LEFT), down(pygame.K_RIGHT)).steer == 1.0
    assert feed(controls, up(pygame.K_RIGHT)).steer == 0.0


def test_both_directions_cancel(controls):
    assert feed(controls, down(pygame.K_LEFT), down(pygame.K_RIGHT)).steer == 0.0


def test_steering_holds_across_frames(controls):
    feed(controls, down(pygame.K_LEFT))
    assert feed(controls).steer == -1.0  # no new events, key still held


def test_faster_and_slower(controls):
    state = feed(controls, down(pygame.K_UP))
    assert state.faster and not state.slower
    state = feed(controls, up(pygame.K_UP), down(pygame.K_DOWN))
    assert state.slower and not state.faster
    assert feed(controls, down(pygame.K_SPACE)).faster  # Space is also "faster"


def test_start_is_one_frame_only(controls):
    assert feed(controls, down(pygame.K_SPACE)).start_pressed
    assert not feed(controls).start_pressed  # still held, but the press was last frame
    assert feed(controls, up(pygame.K_SPACE), down(pygame.K_RETURN)).start_pressed


def test_focus_loss_releases_everything(controls):
    feed(controls, down(pygame.K_LEFT), down(pygame.K_UP))
    state = feed(controls, pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert state.steer == 0.0 and not state.faster


def test_key_up_without_key_down_is_harmless(controls):
    assert feed(controls, up(pygame.K_LEFT), up(pygame.K_SPACE)).steer == 0.0


def test_button_mashing_never_breaks(controls):
    rng = random.Random(1234)
    keys = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE,
            pygame.K_RETURN, pygame.K_a, pygame.K_z, pygame.K_F1]
    for _ in range(100):
        events = [rng.choice([down, up])(rng.choice(keys)) for _ in range(10)]  # 1,000 events total
        state = feed(controls, *events)
        assert state.steer in (-1.0, 0.0, 1.0)
        assert isinstance(state.faster, bool) and isinstance(state.slower, bool)


def test_debug_overlay_text(controls):
    state = feed(controls, down(pygame.K_LEFT), down(pygame.K_SPACE))
    lines = main.debug_lines(state, 60.0)
    assert "steer: -1.0" in lines
    assert "start: PRESSED" in lines


def test_debug_mode_runs_headless():
    assert main.run(["--windowed", "--debug", "--frames", "10"]) == 0
