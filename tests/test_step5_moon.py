"""Step 5: moon, progress indicator and turning back toward the moon."""

import math
import random

import pygame
import pytest

import config
import main
from game import moon
from game.input import InputState
from game.rocket import Rocket
from game.scenes import Flight

NEUTRAL = InputState()


def make_screen():
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    screen.fill(config.BACKGROUND_COLOR)
    return screen


def pixels(surface):
    return pygame.image.tobytes(surface, "RGBA")


# Moon

def test_moon_only_grows_and_is_full_size_at_arrival():
    sizes = [moon.moon_size(i / 1000) for i in range(1001)]
    assert sizes == sorted(sizes)
    assert sizes[0] == config.MOON_MIN_SIZE
    assert sizes[-1] == config.MOON_MAX_SIZE


def test_moon_growth_has_no_jumps_at_top_speed():
    frames = int(config.TRIP_DISTANCE / config.MAX_SPEED * 60)
    sizes = [moon.moon_size(i / frames) for i in range(frames + 1)]
    assert max(b - a for a, b in zip(sizes, sizes[1:])) <= 4


def test_moon_size_is_inversely_proportional_to_distance():
    """1 / size falls in a straight line with progress, as it does for a real object."""
    inverse = [1 / moon.moon_size(p) for p in (0.0, 0.5, 1.0)]
    assert inverse[1] == pytest.approx((inverse[0] + inverse[2]) / 2, rel=0.05)


def test_stars_come_to_rest_after_arrival():
    flight = Flight()
    flight.rocket.distance = 0.01
    for _ in range(5 * 60):
        flight.update(NEUTRAL, 1 / 60)
    assert flight.rocket.arrived
    before = [s.z for s in flight.stars.stars]
    flight.update(NEUTRAL, 1 / 60)
    assert [s.z for s in flight.stars.stars] == pytest.approx(before, abs=1e-4)


def test_moon_size_is_clamped():
    assert moon.moon_size(-1) == config.MOON_MIN_SIZE
    assert moon.moon_size(2) == config.MOON_MAX_SIZE


def test_missing_or_broken_image_falls_back_to_a_drawn_moon(tmp_path):
    broken = tmp_path / "moon.png"
    broken.write_text("not a picture")
    for path in (tmp_path / "nothing.png", broken):
        picture = moon.Moon(path).picture
        assert picture.get_size() == (config.MOON_MAX_SIZE, config.MOON_MAX_SIZE)
        assert picture.get_at((config.MOON_MAX_SIZE // 2, config.MOON_MAX_SIZE // 2)).a == 255
        assert picture.get_at((0, 0)).a == 0  # round, not square


def test_image_file_is_used_when_present(tmp_path):
    image = pygame.Surface((20, 20), pygame.SRCALPHA)
    image.fill((1, 200, 3))
    path = tmp_path / "moon.png"
    pygame.image.save(image, path)
    assert moon.Moon(path).picture.get_at((100, 100))[:3] == (1, 200, 3)


def test_scale_cache_is_bounded_and_reused():
    m = moon.Moon()
    screen = make_screen()
    for i in range(1001):
        m.draw(screen, i / 1000, 0.0)
        assert len(m.cache) <= config.MOON_CACHE_SIZE
    assert m.scaled(config.MOON_MAX_SIZE) is m.scaled(config.MOON_MAX_SIZE)


def test_moon_slides_opposite_to_the_turn():
    middle = moon.moon_center(0.0)
    assert middle == (config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2)
    assert moon.moon_center(0.5)[0] < middle[0] < moon.moon_center(-0.5)[0]


def test_moon_is_hidden_when_facing_away():
    m = moon.Moon()
    for heading in (math.pi, -math.pi):
        screen = make_screen()
        m.draw(screen, 1.0, heading)
        assert pixels(screen) == pixels(make_screen())


# Progress indicator

def test_indicator_runs_from_start_to_end():
    positions = [moon.indicator_x(i / 100) for i in range(101)]
    assert positions == sorted(positions)
    assert positions[0] == config.INDICATOR_MARGIN
    assert positions[-1] == config.SCREEN_WIDTH - config.INDICATOR_MARGIN
    assert moon.indicator_x(-5) == positions[0] and moon.indicator_x(5) == positions[-1]
    assert moon.indicator_x(0.5) == pytest.approx((positions[0] + positions[-1]) / 2)


def test_indicator_draws_and_moves():
    indicator = moon.ProgressIndicator()
    start, later = make_screen(), make_screen()
    indicator.draw(start, 0.0)
    indicator.draw(later, 0.5)
    assert pixels(start) != pixels(make_screen())
    assert pixels(start) != pixels(later)


def test_earth_and_flag_fit_on_screen_and_are_not_covered():
    icon = config.INDICATOR_ICON_SIZE
    earth, flag = moon.indicator_x(0.0) - icon, moon.indicator_x(1.0) + icon
    assert earth - icon / 2 >= 0 and flag + icon / 2 <= config.SCREEN_WIDTH
    assert moon.indicator_x(0.0) - earth >= icon and flag - moon.indicator_x(1.0) >= icon
    for picture in (moon.draw_earth_picture(icon), moon.draw_flag_picture(icon)):
        assert picture.get_size() == (icon, icon)
        assert picture.get_bounding_rect().width > icon * 0.8
    assert moon.draw_earth_picture(icon).get_at((0, 0)).a == 0  # round, not square


# Turning back toward the moon

@pytest.mark.parametrize("heading", [0.3, -0.3, 1.5, -1.5, 3.1, -3.1, math.pi])
def test_release_turns_smoothly_back_to_the_moon(heading):
    rocket = Rocket()
    rocket.heading = heading
    for _ in range(20 * 60):
        before, offset = rocket.heading, rocket.steer_offset
        rocket.update(NEUTRAL, 1 / 60)
        assert abs(rocket.heading) <= abs(before) + 1e-6  # always the short way, no overshoot swing
        assert rocket.heading * heading > -0.01
        assert abs(rocket.steer_offset - offset) < 0.1  # no sudden jumps
    assert rocket.heading == pytest.approx(0.0, abs=0.02)


def test_stick_still_turns_freely_during_the_trip():
    rocket = Rocket()
    for _ in range(4 * 60):
        rocket.update(InputState(steer=1.0), 1 / 60)
    assert rocket.heading > 1.5


@pytest.mark.parametrize("faster", [True, False])
@pytest.mark.parametrize("steer", [1.0, -1.0])
def test_moon_is_in_view_at_arrival_even_when_holding_the_stick(steer, faster):
    rocket = Rocket()
    previous = 0.0
    while not rocket.arrived:
        rocket.update(InputState(steer=steer, faster=faster), 1 / 60)
        assert abs(rocket.steer_offset - previous) < 0.1
        previous = rocket.steer_offset
    assert abs(moon.moon_center(rocket.heading)[0] - config.SCREEN_WIDTH / 2) < config.SCREEN_WIDTH / 2


def test_moon_is_in_view_at_arrival_after_mashing():
    for seed in range(10):
        rng = random.Random(seed)
        rocket = Rocket()
        steer = 0.0
        while not rocket.arrived:
            if rng.random() < 0.05:
                steer = rng.choice([-1.0, 0.0, 1.0])
            rocket.update(InputState(steer=steer, faster=rng.random() < 0.5), 1 / 60)
        assert 0 < moon.moon_center(rocket.heading)[0] < config.SCREEN_WIDTH


def test_game_runs_with_moon():
    assert main.run(["--windowed", "--frames", "30"]) == 0
