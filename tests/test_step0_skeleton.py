"""Step 0: project skeleton and test harness."""

import os
import subprocess
import sys

import pygame

import config
import main
from conftest import ROOT


def test_config_values_are_sane():
    for value in (config.FPS, config.SCREEN_WIDTH, config.SCREEN_HEIGHT):
        assert isinstance(value, int) and value > 0
    assert len(config.BACKGROUND_COLOR) == 3
    assert all(0 <= c <= 255 for c in config.BACKGROUND_COLOR)


def test_run_for_fixed_frames_returns_zero():
    assert main.run(["--windowed", "--frames", "30"]) == 0


def test_escape_and_window_close_quit():
    assert main.is_quit_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert main.is_quit_event(pygame.event.Event(pygame.QUIT))


def test_other_keys_do_not_quit():
    for key in (pygame.K_SPACE, pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
        assert not main.is_quit_event(pygame.event.Event(pygame.KEYDOWN, key=key))
    assert not main.is_quit_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_ESCAPE))


def test_windowed_flag_parsing():
    assert main.parse_args(["--windowed"]).windowed is True
    assert main.parse_args([]).windowed is False
    assert main.parse_args(["--frames", "5"]).frames == 5


def test_main_script_runs_headless():
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    result = subprocess.run(
        [sys.executable, "main.py", "--windowed", "--frames", "30"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
