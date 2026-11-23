"""Step 2: rocket state."""

import random

import pytest

import config
import main
from game.input import InputState
from game.rocket import Rocket

NEUTRAL = InputState()
FASTER = InputState(faster=True)
SLOWER = InputState(slower=True)


def fly(rocket, controls, seconds, fps=60):
    for _ in range(round(seconds * fps)):
        rocket.update(controls, 1 / fps)


def trip_seconds(controls, speed):
    rocket = Rocket()
    rocket.speed = rocket.target_speed = speed
    seconds = 0.0
    while not rocket.arrived:
        rocket.update(controls, 1 / 60)
        seconds += 1 / 60
        assert seconds < 1000, "never arrived"
    return seconds


def test_starts_at_launch():
    rocket = Rocket()
    assert rocket.distance == config.TRIP_DISTANCE
    assert rocket.progress == 0.0
    assert not rocket.arrived
    assert config.MIN_SPEED <= rocket.speed <= config.MAX_SPEED


def test_faster_and_slower_reach_the_limits():
    rocket = Rocket()
    fly(rocket, FASTER, 5)
    assert rocket.speed == pytest.approx(config.MAX_SPEED, abs=0.1)
    fly(rocket, SLOWER, 5)
    assert rocket.speed == pytest.approx(config.MIN_SPEED, abs=0.1)


def test_speed_keeps_after_release():
    rocket = Rocket()
    fly(rocket, FASTER, 5)
    fly(rocket, NEUTRAL, 3)
    assert rocket.speed == pytest.approx(config.MAX_SPEED, abs=0.1)


def test_both_buttons_cancel():
    rocket = Rocket()
    fly(rocket, InputState(faster=True, slower=True), 2)
    assert rocket.speed == pytest.approx(config.START_SPEED)


def test_mashing_stays_in_range_and_never_jumps():
    rng = random.Random(1234)
    rocket = Rocket()
    for _ in range(5000):
        before = rocket.speed
        dt = rng.choice([1 / 120, 1 / 60, 1 / 30, 1 / 10])
        controls = InputState(rng.uniform(-1, 1), rng.random() < 0.5, rng.random() < 0.5)
        rocket.update(controls, dt)
        assert config.MIN_SPEED <= rocket.speed <= config.MAX_SPEED
        assert abs(rocket.speed - before) <= config.MAX_SPEED_CHANGE * dt + 1e-9
        assert -1.0 <= rocket.steer_offset <= 1.0
        assert 0.0 <= rocket.distance <= config.TRIP_DISTANCE


def test_speed_change_limit_holds_for_a_big_gap():
    rocket = Rocket()
    rocket.speed, rocket.target_speed = config.MIN_SPEED, config.MAX_SPEED
    rocket.update(NEUTRAL, 1 / 60)
    assert 0 < rocket.speed - config.MIN_SPEED <= config.MAX_SPEED_CHANGE / 60 + 1e-9


def test_same_trip_at_30_and_60_fps():
    results = []
    for fps in (30, 60):
        rocket = Rocket()
        for controls in (FASTER, NEUTRAL, SLOWER, InputState(steer=1.0, faster=True)):
            fly(rocket, controls, 2, fps)
        results.append(rocket)
    slow, fast = results
    travelled = [config.TRIP_DISTANCE - r.distance for r in results]
    assert travelled[0] == pytest.approx(travelled[1], rel=0.005)
    assert slow.speed == pytest.approx(fast.speed, rel=0.01)
    assert slow.steer_offset == pytest.approx(fast.steer_offset)


@pytest.mark.parametrize("controls, speed", [(SLOWER, config.MIN_SPEED), (FASTER, config.MAX_SPEED)])
def test_trip_length_is_toddler_sized(controls, speed):
    assert 60 <= trip_seconds(controls, speed) <= 180


def test_steering_never_changes_distance_or_arrival():
    straight, wiggly = Rocket(), Rocket()
    rng = random.Random(99)
    while not straight.arrived:
        straight.update(NEUTRAL, 1 / 60)
        wiggly.update(InputState(steer=rng.choice([-1.0, 1.0])), 1 / 60)
        assert wiggly.distance == straight.distance
        assert wiggly.arrived == straight.arrived
    assert straight.progress == 1.0


def test_steering_is_smooth_and_recentres():
    rocket = Rocket()
    rocket.update(InputState(steer=1.0), 1 / 60)
    assert 0 < rocket.steer_offset < 0.2
    fly(rocket, InputState(steer=1.0), 3)
    assert rocket.steer_offset == pytest.approx(1.0, abs=0.01)
    fly(rocket, NEUTRAL, 3)
    assert rocket.steer_offset == pytest.approx(0.0, abs=0.01)


def test_odd_frame_times_are_harmless():
    rocket = Rocket()
    rocket.update(FASTER, 0.0)
    rocket.update(FASTER, -5.0)
    assert rocket.distance == config.TRIP_DISTANCE
    rocket.update(FASTER, 60.0)  # a long hiccup must not teleport the rocket
    assert config.TRIP_DISTANCE - rocket.distance <= config.MAX_SPEED * config.MAX_FRAME_TIME


def test_stays_arrived_then_resets():
    rocket = Rocket()
    fly(rocket, FASTER, 100)
    assert rocket.arrived and rocket.distance == 0.0 and rocket.progress == 1.0
    fly(rocket, SLOWER, 2)
    assert rocket.arrived and rocket.distance == 0.0
    rocket.reset()
    assert not rocket.arrived
    assert rocket.distance == config.TRIP_DISTANCE
    assert rocket.speed == rocket.target_speed == config.START_SPEED
    assert rocket.steer_offset == 0.0


def test_rocket_overlay_text():
    lines = main.rocket_lines(Rocket())
    assert any(line.startswith(f"speed: {config.START_SPEED:.1f}") for line in lines)
    assert "arrived: no" in lines


def test_overlay_shows_rocket_headless():
    assert main.run(["--windowed", "--debug", "--frames", "30"]) == 0
