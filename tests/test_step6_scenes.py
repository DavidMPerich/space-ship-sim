"""Step 6: countdown, flight, arrival celebration and restart."""

import random

import pygame
import pytest

import config
from game import effects, launch
from game.input import InputState
from game.scenes import ARRIVAL, COUNTDOWN, FLIGHT, OPENING, READY, Game

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
    loop = config.AUTO_START_DELAY + config.DOOR_TIME + countdown_time() + trip + config.ARRIVAL_PAUSE
    for _ in range(int((3 * loop + 2) * 60)):
        game.update(NEUTRAL, DT)
        if game.scene != seen[-1]:
            seen.append(game.scene)
    assert seen == [READY, OPENING, COUNTDOWN, FLIGHT, ARRIVAL] * 3 + [READY]


@pytest.mark.parametrize("controls", [START, InputState(faster=True), InputState(slower=True)])
def test_any_button_starts_the_launch(game, controls):
    game.update(NEUTRAL, DT)
    assert game.scene == READY
    game.update(controls, DT)
    assert game.scene == OPENING


def test_ready_waits_then_starts_by_itself(game):
    run_for(game, config.AUTO_START_DELAY - 0.1)
    assert game.scene == READY
    run_for(game, 0.2)
    assert game.scene == OPENING


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
    assert game.flight.altitude == 0.0


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
    following = {READY: OPENING, OPENING: COUNTDOWN, COUNTDOWN: FLIGHT, FLIGHT: ARRIVAL, ARRIVAL: READY}
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
    for begin in (game.begin_ready, game.begin_opening, game.begin_countdown, game.begin_flight, game.begin_arrival):
        begin()
        run_for(game, 0.5)
        game.draw(screen)


def brightness(color):
    return sum(color[:3])


def test_mashing_cannot_skip_the_roof_opening(game):
    game.begin_opening()
    frames = 0
    while game.scene == OPENING:
        game.update(MASH[frames % 3], DT)
        frames += 1
    assert game.scene == COUNTDOWN
    assert frames * DT == pytest.approx(config.DOOR_TIME, abs=0.05)


def test_roof_opens_smoothly_from_the_middle_outward(game):
    assert game.hangar.door_point(1.0, 0.0)[0] == pytest.approx(0.0)  # shut: the doors meet
    edges = [game.hangar.door_point(1.0, i / 100)[0] for i in range(101)]
    assert edges == sorted(edges)
    assert edges[-1] == pytest.approx(config.HANGAR_HALF_WIDTH)  # open: hidden behind the frame
    game.begin_opening()
    opened = []
    while game.scene == OPENING:
        opened.append(game.doors_open())
        game.update(NEUTRAL, DT)
    assert opened == sorted(opened) and opened[0] == 0.0 and opened[-1] > 0.99
    assert max(b - a for a, b in zip(opened, opened[1:])) < 0.02


def test_roof_hides_the_sky_until_it_opens(game):
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    game.fade = 0.0
    spot = (config.SCREEN_WIDTH // 2 - 250, config.SCREEN_HEIGHT // 2)
    game.draw(screen)
    assert screen.get_at(spot)[:3] in [*config.HANGAR_DOOR_COLORS, config.HANGAR_LINE_COLOR]
    game.begin_countdown()
    game.draw(screen)
    assert brightness(screen.get_at(spot)) >= brightness(launch.sky_color(0.0))


def test_countdown_is_five_seconds():
    assert countdown_time() == 5.0


def test_thruster_glow_starts_at_two_seconds_peaks_after_liftoff_then_fades(game):
    game.begin_countdown()
    values = []  # (seconds from liftoff, glow)
    for _ in range(round((countdown_time() + 12) / DT)):
        offset = countdown_time() if game.scene == COUNTDOWN else 0.0
        values.append((game.time - offset, game.thrust()))
        game.update(NEUTRAL, DT)
    glows = [glow for _, glow in values]
    assert all(glow == 0.0 for t, glow in values if t < -2.0)
    assert any(0.0 < glow for t, glow in values if t < -1.5)
    peak = glows.index(max(glows))
    assert values[peak][0] == pytest.approx(config.THRUST_PEAK, abs=0.05)
    assert glows[:peak] == sorted(glows[:peak])
    assert glows[peak:] == sorted(glows[peak:], reverse=True)
    assert glows[-1] == 0.0
    assert max(abs(b - a) for a, b in zip(glows, glows[1:])) < 0.02  # no flashing


def test_glow_only_tints_the_border(game):
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    game.glow.draw(screen, 1.0)
    edge = screen.get_at((2, config.SCREEN_HEIGHT // 2))
    assert edge.r > 80 and edge.r > edge.g > edge.b
    # Oval: the corners are hotter than the middles of the edges, and the sides match.
    assert brightness(screen.get_at((2, 2))) > brightness(edge)
    assert screen.get_at((2, config.SCREEN_HEIGHT // 2 - 1)).r == pytest.approx(
        screen.get_at((config.SCREEN_WIDTH - 3, config.SCREEN_HEIGHT // 2 - 1)).r, abs=3)
    assert screen.get_at((config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2))[:3] == (0, 0, 0)


def test_sky_darkens_while_stars_brighten():
    steps = [i / 100 for i in range(101)]
    sky = [brightness(launch.sky_color(a)) for a in steps]
    stars = [launch.star_brightness(a) for a in steps]
    assert sky == sorted(sky, reverse=True)
    assert launch.sky_color(1.0) == config.BACKGROUND_COLOR
    assert stars == sorted(stars)
    assert stars[0] == 0.0 and stars[-1] == 1.0


def test_stars_appear_only_after_the_thickest_cloud_and_mist_clears():
    assert config.STARS_APPEAR > config.MIST_MIDDLE
    assert launch.mist_strength(0.0) == launch.mist_strength(1.0) == 0.0
    assert launch.mist_strength(config.MIST_MIDDLE) == config.MIST_MAX
    mist = [launch.mist_strength(i / 1000) for i in range(1001)]
    assert max(abs(b - a) for a, b in zip(mist, mist[1:])) < 0.01


def test_ship_climbs_smoothly_to_space_at_any_speed(game):
    for controls in (NEUTRAL, InputState(slower=True), InputState(faster=True)):
        game.begin_ready()
        game.begin_flight()
        heights = [0.0]
        for _ in range(40 * 60):
            game.update(controls, DT)
            heights.append(game.flight.altitude)
        assert heights == sorted(heights)
        assert max(b - a for a, b in zip(heights, heights[1:])) < 0.002
        assert heights[-1] == 1.0 and not game.flight.rocket.arrived


def test_ascent_draws_at_every_height_and_the_cloud_cache_is_bounded(game):
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    game.begin_flight()
    for i in range(101):
        game.flight.altitude = i / 100
        game.flight.rocket.heading = (i - 50) / 50 * 3
        game.draw(screen)
        assert len(game.flight.sky.clouds.cache) <= config.CLOUD_CACHE_SIZE
    assert game.hangar.frame_scale(1.0) is None
