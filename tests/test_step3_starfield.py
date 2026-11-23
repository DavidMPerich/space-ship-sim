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


@pytest.mark.parametrize("steer", [-1.0, -0.3, 0.0, 0.5, 1.0])
def test_centre_star_is_at_vanishing_point(steer):
    center = starfield.vanishing_point(steer)
    for z in (config.STAR_NEAR, 0.5, config.STAR_FAR):
        assert starfield.project(0, 0, z, center) == center


def test_vanishing_point_moves_with_steering():
    left, middle, right = (starfield.vanishing_point(s) for s in (-1.0, 0.0, 1.0))
    assert middle == (config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2)
    assert left[0] > middle[0] > right[0]
    assert left[0] - middle[0] == config.STEER_SHIFT
    assert 0 < right[0] and left[0] < config.SCREEN_WIDTH


def test_stars_stream_outward():
    center = starfield.vanishing_point(0)
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
    """Holds in every direction, at full steering."""
    reach = config.STAR_MIN_RADIUS * config.STAR_FOCAL / config.STAR_NEAR
    farthest_corner = math.hypot(config.SCREEN_WIDTH / 2 + config.STEER_SHIFT, config.SCREEN_HEIGHT / 2)
    assert reach > farthest_corner


def test_hiccups_and_extreme_values_are_harmless():
    screen = make_screen()
    field = make_field()
    for speed, dt, steer in ((0, 0, 0), (9, -1, -1), (1000, 60, 1), (-5, 0.5, 5)):
        field.update(speed, dt)
        field.draw(screen, steer)
    assert all(config.STAR_NEAR < s.z <= config.STAR_FAR for s in field.stars)


def test_drawing_puts_stars_on_screen():
    screen = make_screen()
    blank = pygame.image.tobytes(screen, "RGB")
    make_field().draw(screen, 0.0)
    assert pygame.image.tobytes(screen, "RGB") != blank


def test_frame_stays_under_time_budget():
    screen = make_screen()
    field = make_field()
    times = []
    for _ in range(60):
        start = time.perf_counter()
        field.update(config.MAX_SPEED, 1 / 60)
        field.draw(screen, 0.5)
        times.append(time.perf_counter() - start)
    times.sort()
    assert times[len(times) // 2] < 0.008  # median; half a 60 FPS frame on a desktop


def test_game_runs_with_starfield():
    assert main.run(["--windowed", "--frames", "30"]) == 0
