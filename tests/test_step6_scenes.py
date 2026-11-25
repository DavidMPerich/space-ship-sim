"""Step 6: countdown, flight, arrival celebration and restart."""

import random

import pygame
import pytest

import config
from game import effects
from game.input import InputState
from game.scenes import ARRIVAL, COUNTDOWN, FLIGHT, READY, Game

DT = 1 / 60
NEUTRAL = InputState()
START = InputState(start_pressed=True)
MASH = [START, NEUTRAL, InputState(faster=True, slower=True, start_pressed=True, steer=-1.0)]


@pytest.fixture
def game():
    return Game()


def run_for(game, seconds, controls=NEUTRAL):
    """Advance on a fake clock."""
    for _ in range(round(seconds / DT)):
        game.update(controls, DT)


def countdown_time():
    return config.COUNTDOWN_STEP * len(config.COUNTDOWN_WORDS)


def to_arrival(game):
    game.begin_flight()
    game.flight.rocket.distance = 0.01
    game.update(NEUTRAL, DT)
    assert game.scene == ARRIVAL


def test_three_full_loops_run_in_order(game):
    seen = [game.scene]
    trip = config.TRIP_DISTANCE / config.START_SPEED
    loop = config.AUTO_START_DELAY + countdown_time() + trip + config.ARRIVAL_PAUSE
    for _ in range(int((3 * loop + 2) * 60)):
        game.update(NEUTRAL, DT)
        if game.scene != seen[-1]:
            seen.append(game.scene)
    assert seen == [READY, COUNTDOWN, FLIGHT, ARRIVAL] * 3 + [READY]


@pytest.mark.parametrize("controls", [START, InputState(faster=True), InputState(slower=True)])
def test_any_button_starts_the_countdown(game, controls):
    game.update(NEUTRAL, DT)
    assert game.scene == READY
    game.update(controls, DT)
    assert game.scene == COUNTDOWN


def test_ready_waits_then_starts_by_itself(game):
    run_for(game, config.AUTO_START_DELAY - 0.1)
    assert game.scene == READY
    run_for(game, 0.2)
    assert game.scene == COUNTDOWN


def test_countdown_shows_every_number_for_its_time(game):
    game.begin_countdown()
    shown = []
    while game.scene == COUNTDOWN:
        shown.append(game.number_index(game.time))
        game.update(NEUTRAL, DT)
    assert shown == sorted(shown)
    assert set(shown) == set(range(len(config.COUNTDOWN_WORDS)))
    for index in set(shown):
        assert shown.count(index) * DT == pytest.approx(config.COUNTDOWN_STEP, abs=0.05)


def test_rocket_waits_on_the_pad_until_blast_off(game):
    game.begin_countdown()
    run_for(game, countdown_time() - 0.1, InputState(steer=1.0, faster=True))
    assert game.flight.rocket.distance == config.TRIP_DISTANCE
    assert game.flight.rocket.heading == 0.0


def test_stars_get_moving_gently_at_launch(game):
    game.begin_flight()
    flows = [game.flight.star_flow]
    for _ in range(300):
        game.update(NEUTRAL, DT)
        flows.append(game.flight.star_flow)
    assert flows[0] == 0.0 and flows[-1] > 0.95
    assert max(b - a for a, b in zip(flows, flows[1:])) < 0.03


def test_restart_after_pause_resets_everything(game):
    to_arrival(game)
    game.flight.rocket.heading = 0.1
    run_for(game, config.ARRIVAL_PAUSE - 0.1)
    assert game.scene == ARRIVAL
    run_for(game, 0.2)
    assert game.scene == READY
    rocket = game.flight.rocket
    assert not rocket.arrived
    assert rocket.distance == config.TRIP_DISTANCE
    assert rocket.speed == rocket.target_speed == config.START_SPEED
    assert rocket.heading == rocket.steer_offset == 0.0
    assert game.flight.star_flow == 0.0


def test_fade_is_smooth_and_hides_the_restart(game):
    game.fade = 0.0
    to_arrival(game)
    fades = []
    restart = None
    for i in range(round((config.ARRIVAL_PAUSE + 2) * 60)):
        game.update(NEUTRAL, DT)
        fades.append(game.fade)
        if restart is None and game.scene == READY:
            restart = i
    assert fades[restart] > 0.95
    assert max(abs(b - a) for a, b in zip(fades, fades[1:])) < 0.05
    assert fades[-1] == 0.0


def test_mashing_cannot_skip_the_countdown(game):
    game.begin_countdown()
    frames = 0
    while game.scene == COUNTDOWN:
        game.update(MASH[frames % 3], DT)
        frames += 1
    assert game.scene == FLIGHT
    assert frames * DT == pytest.approx(countdown_time(), abs=0.05)


def test_mashing_cannot_skip_the_celebration(game):
    to_arrival(game)
    frames = 0
    while game.scene == ARRIVAL:
        game.update(MASH[frames % 3], DT)
        assert len(game.confetti.pieces) <= config.CONFETTI_MAX
        frames += 1
    assert game.scene == READY
    assert frames * DT == pytest.approx(config.ARRIVAL_PAUSE, abs=0.05)


def test_button_held_through_the_restart_does_not_launch(game):
    to_arrival(game)
    run_for(game, config.ARRIVAL_PAUSE + 1.0, InputState(faster=True))
    assert game.scene == READY


def test_random_mashing_and_odd_frames_never_break(game, monkeypatch):
    monkeypatch.setattr(config, "TRIP_DISTANCE", 20.0)
    game.begin_ready()
    rng = random.Random(1)
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    following = {READY: COUNTDOWN, COUNTDOWN: FLIGHT, FLIGHT: ARRIVAL, ARRIVAL: READY}
    seen = set()
    for i in range(6000):
        before = game.scene
        controls = InputState(rng.choice([-1.0, 0.0, 1.0]), rng.random() < 0.5, rng.random() < 0.5,
                              rng.random() < 0.5)
        game.update(controls, rng.choice([0.0, -1.0, DT, DT, 5.0]))
        assert game.scene in (before, following[before])
        seen.add(game.scene)
        if i % 20 == 0:
            game.draw(screen)
    assert seen == set(following)


def test_presses_give_visible_feedback(game):
    game.begin_countdown()
    run_for(game, 0.9)
    before = game.pop
    game.update(START, DT)
    assert game.pop > before
    to_arrival(game)
    count = len(game.confetti.pieces)
    game.update(START, DT)
    assert len(game.confetti.pieces) == count + config.CONFETTI_BURST


def test_burst_pieces_leave_but_steady_confetti_stays():
    confetti = effects.Confetti(random.Random(2))
    confetti.start()
    confetti.burst()
    for _ in range(10 * 60):
        confetti.update(DT)
    assert len(confetti.pieces) == config.CONFETTI_COUNT


def test_text_fits_on_screen(game):
    for picture in [game.blast_off, game.arrival_text, *game.numbers]:
        assert picture.get_width() <= config.SCREEN_WIDTH * config.TEXT_MAX_WIDTH + 2
        assert picture.get_height() * (1 + config.POP_SIZE) < config.SCREEN_HEIGHT


def test_every_scene_draws(game):
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    for begin in (game.begin_ready, game.begin_countdown, game.begin_flight, game.begin_arrival):
        begin()
        run_for(game, 0.5)
        game.draw(screen)
