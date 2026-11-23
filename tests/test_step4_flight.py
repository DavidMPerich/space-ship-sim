"""Step 4: flight scene wired into main.py."""

import pygame
import pytest

import config
import main
from game.input import InputState
from game.scenes import Flight


def run_scripted(monkeypatch, frames, script, frame_ms=1000 / 60):
    """Run the real game loop without waiting. script maps frame number to [(event type, key), ...]."""
    flights = []

    class RecordedFlight(Flight):
        def __init__(self):
            super().__init__()
            flights.append(self)

    class FakeClock:
        frame = 0

        def tick(self, fps):
            for kind, key in script.get(self.frame, []):
                pygame.event.post(pygame.event.Event(kind, key=key))
            self.frame += 1
            return frame_ms

        def get_fps(self):
            return 60.0

    monkeypatch.setattr(main, "Flight", RecordedFlight)
    monkeypatch.setattr(pygame.time, "Clock", FakeClock)
    assert main.run(["--windowed", "--debug", "--frames", str(frames)]) == 0
    assert len(flights) == 1
    return flights[0].rocket


def travelled(rocket):
    return config.TRIP_DISTANCE - rocket.distance


def test_600_frames_with_no_input(monkeypatch):
    rocket = run_scripted(monkeypatch, 600, {})
    assert travelled(rocket) == pytest.approx(config.START_SPEED * 10, rel=0.01)
    assert rocket.heading == 0.0


def test_600_frames_with_scripted_input(monkeypatch):
    rocket = run_scripted(monkeypatch, 600, {
        60: [(pygame.KEYDOWN, pygame.K_UP)],
        180: [(pygame.KEYUP, pygame.K_UP)],
        480: [(pygame.KEYDOWN, pygame.K_RIGHT)],
    })
    # 1 s at cruising speed, then a couple of seconds climbing to top speed.
    assert config.START_SPEED * 10 * 1.15 < travelled(rocket) < config.MAX_SPEED * 10
    assert rocket.speed == pytest.approx(config.MAX_SPEED, abs=0.1)
    assert rocket.heading > 0.5
    assert not rocket.arrived


def test_slower_input_covers_less_distance(monkeypatch):
    rocket = run_scripted(monkeypatch, 600, {0: [(pygame.KEYDOWN, pygame.K_DOWN)]})
    assert config.MIN_SPEED * 10 < travelled(rocket) < config.START_SPEED * 10 * 0.85


def test_full_trip_arrives_once_and_keeps_running(monkeypatch, capsys):
    frames = int((config.TRIP_DISTANCE / config.START_SPEED + 5) * 60)
    rocket = run_scripted(monkeypatch, frames, {})
    assert rocket.arrived
    assert capsys.readouterr().out.count("You made it to the Moon!") == 1


def test_escape_ends_the_loop(monkeypatch):
    rocket = run_scripted(monkeypatch, 600, {30: [(pygame.KEYDOWN, pygame.K_ESCAPE)]})
    assert travelled(rocket) < config.START_SPEED


def test_flight_survives_odd_frame_times():
    flight = Flight()
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    for dt in (0.0, -1.0, 30.0, 1 / 60):
        flight.update(InputState(steer=1.0, faster=True), dt)
        flight.draw(screen)
