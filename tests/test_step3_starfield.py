"""Step 3: starfield."""

import math
import random
import time

import pygame
import pytest

import config
import main
from game import starfield
from game.starfield import Star, Starfield


def make_field(count=None):
    return Starfield(count, random.Random(7))


def make_screen():
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    screen.fill(config.BACKGROUND_COLOR)
    return screen


def test_star_count_stays_constant_and_depth_in_range():
    field = make_field()
    for _ in range(600):
        field.update(config.MAX_SPEED, 1 / 30)
        assert len(field.stars) == config.STAR_COUNT
        assert all(config.STAR_NEAR < s.z <= config.STAR_FAR for s in field.stars)


def test_star_passing_camera_is_recycled_far_away():
    field = make_field(1)
    star = field.stars[0]
    star.z = config.STAR_NEAR + 0.001
    before = (star.x, star.y)
    field.update(config.MAX_SPEED, 1 / 60)
    assert star.z > config.STAR_FAR - 0.1
    assert (star.x, star.y) != before


def on_screen(star):
    x, y = starfield.project(star.x, star.y, star.z, starfield.vanishing_point())
    return 0 <= x < config.SCREEN_WIDTH and 0 <= y < config.SCREEN_HEIGHT


def test_centre_star_is_at_vanishing_point():
    center = starfield.vanishing_point()
    assert center == (config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2)
    for z in (config.STAR_NEAR, 0.5, config.STAR_FAR):
        assert starfield.project(0, 0, z, center) == center


@pytest.mark.parametrize("turn_rate", [config.TURN_RATE, -config.TURN_RATE])
def test_turning_sweeps_stars_the_other_way(turn_rate):
    field = make_field(1)
    star = field.stars[0]
    star.x, star.z = 0.0, 0.5
    field.update(config.MIN_SPEED, 1 / 60, turn_rate)
    assert star.x * turn_rate < 0


@pytest.mark.parametrize("turn_rate", [config.TURN_RATE, -config.TURN_RATE])
@pytest.mark.parametrize("speed", [config.MIN_SPEED, config.MAX_SPEED])
def test_long_turns_keep_the_sky_full_and_never_pop(turn_rate, speed):
    """A star only vanishes from or appears on screen by crossing an edge or while faded out."""
    field = make_field()
    straight = make_field()
    counts = []
    for _ in range(1200):
        before = [(s.x, s.y, s.z, on_screen(s)) for s in field.stars]
        field.update(speed, 1 / 60, turn_rate)
        straight.update(speed, 1 / 60)
        for star, (x, y, z, visible) in zip(field.stars, before):
            moved = abs(star.x / star.z - x / z)
            if visible and star.z > z:  # recycled: it must have been about to leave the screen anyway
                assert not on_screen(Star(x, y, config.STAR_NEAR, None))
            if star.z < z and moved > 1.0:  # wrapped to the other side
                assert not on_screen(star)
        counts.append((sum(map(on_screen, field.stars)), sum(map(on_screen, straight.stars))))
    settled = counts[600:]
    turning, flying = (sum(c[i] for c in settled) / len(settled) for i in (0, 1))
    assert 0.7 * flying < turning < 1.6 * flying


def test_stars_stream_outward():
    center = starfield.vanishing_point()
    far = starfield.project(0.3, 0.2, 0.8, center)
    near = starfield.project(0.3, 0.2, 0.4, center)
    assert math.dist(near, center) > math.dist(far, center)


def test_faster_means_quicker_stars():
    slow, fast = make_field(1), make_field(1)
    slow.stars[0].z = fast.stars[0].z = 0.8
    slow.update(config.MIN_SPEED, 1 / 60)
    fast.update(config.MAX_SPEED, 1 / 60)
    assert fast.stars[0].z < slow.stars[0].z < 0.8


def test_new_stars_start_invisible():
    assert starfield.star_color(Star(0, 0, config.STAR_FAR, (255, 255, 255))) == config.BACKGROUND_COLOR


def test_star_colors_are_white_to_soft_yellow():
    for red, green, blue in config.STAR_COLORS:
        assert red >= green >= blue >= 200


def test_stars_are_off_screen_before_recycling():
    """Turning never changes a star's height, so the height gap alone must clear the screen."""
    reach = config.STAR_MIN_HEIGHT * config.STAR_FOCAL / config.STAR_NEAR
    assert reach > config.SCREEN_HEIGHT / 2 + config.STAR_MAX_SIZE
    assert config.STAR_TURN_EDGE * config.STAR_FOCAL > config.SCREEN_WIDTH / 2 + config.STAR_MAX_SIZE


def test_hiccups_and_extreme_values_are_harmless():
    screen = make_screen()
    field = make_field()
    for speed, dt, steer in ((0, 0, 0), (9, -1, -1), (1000, 60, 1), (-5, 0.5, 5)):
        field.update(speed, dt, steer)
        field.draw(screen)
    assert all(config.STAR_NEAR < s.z <= config.STAR_FAR for s in field.stars)


def test_drawing_puts_stars_on_screen():
    screen = make_screen()
    blank = pygame.image.tobytes(screen, "RGB")
    make_field().draw(screen)
    assert pygame.image.tobytes(screen, "RGB") != blank


def test_frame_stays_under_time_budget():
    screen = make_screen()
    field = make_field()
    times = []
    for _ in range(60):
        start = time.perf_counter()
        field.update(config.MAX_SPEED, 1 / 60, config.TURN_RATE)
        field.draw(screen)
        times.append(time.perf_counter() - start)
    times.sort()
    assert times[len(times) // 2] < 0.008  # median; half a 60 FPS frame on a desktop


def test_game_runs_with_starfield():
    assert main.run(["--windowed", "--frames", "30"]) == 0
