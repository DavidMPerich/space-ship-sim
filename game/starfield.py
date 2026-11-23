"""3D-projected starfield: stars stream outward from a vanishing point that shifts with steering."""

import math
import random

import pygame

import config


class Star:
    def __init__(self, x, y, z, color):
        self.x = x
        self.y = y
        self.z = z
        self.color = color


def speed_fraction(speed):
    """0 at MIN_SPEED, 1 at MAX_SPEED."""
    fraction = (speed - config.MIN_SPEED) / (config.MAX_SPEED - config.MIN_SPEED)
    return max(0.0, min(1.0, fraction))


def _mix(low, high, fraction):
    return low + (high - low) * fraction


def streak_length(speed):
    """Streak length as a share of the star's depth."""
    return _mix(config.STREAK_SLOW, config.STREAK_FAST, speed_fraction(speed))


def tail_depth(z, speed):
    """Depth of the trailing end of a star's streak."""
    return min(z * (1 + streak_length(speed)), config.STAR_FAR)


def vanishing_point(steer_offset):
    """Screen point the rocket flies toward. Steering right slides the scene left, like turning your head."""
    return (config.SCREEN_WIDTH / 2 - steer_offset * config.STEER_SHIFT, config.SCREEN_HEIGHT / 2)


def project(x, y, z, center):
    """Depth position to screen pixels."""
    scale = config.STAR_FOCAL / z
    return (center[0] + x * scale, center[1] + y * scale)


def star_color(star):
    """Fade in from the background so new stars never pop."""
    glow = max(0.0, min(1.0, (config.STAR_FAR - star.z) / config.STAR_FADE_DEPTH))
    return tuple(int(_mix(back, full, glow)) for back, full in zip(config.BACKGROUND_COLOR, star.color))


def star_size(z):
    nearness = (config.STAR_FAR - z) / (config.STAR_FAR - config.STAR_NEAR)
    return max(1, round(config.STAR_MAX_SIZE * nearness ** 2))


class Starfield:
    def __init__(self, count=None, rng=None):
        self.rng = rng or random.Random()
        count = config.STAR_COUNT if count is None else count
        self.stars = []
        for _ in range(count):
            z = self.rng.uniform(config.STAR_NEAR, config.STAR_FAR)
            star = Star(0.0, 0.0, z, self.rng.choice(config.STAR_COLORS))
            self._place(star)
            self.stars.append(star)

    def _place(self, star):
        """Give a star a new random spot in a ring around the flight path."""
        angle = self.rng.uniform(0, math.tau)
        radius = self.rng.uniform(config.STAR_MIN_RADIUS, config.STAR_MAX_RADIUS)
        star.x = math.cos(angle) * radius
        star.y = math.sin(angle) * radius

    def update(self, speed, dt):
        dt = max(0.0, min(config.MAX_FRAME_TIME, dt))
        step = _mix(config.STAR_SLOW_RATE, config.STAR_FAST_RATE, speed_fraction(speed)) * dt
        for star in self.stars:
            star.z -= step
            if star.z <= config.STAR_NEAR:
                star.z += config.STAR_FAR - config.STAR_NEAR
                self._place(star)

    def draw(self, screen, speed, steer_offset):
        center = vanishing_point(steer_offset)
        area = screen.get_rect().inflate(config.STAR_MAX_SIZE * 2, config.STAR_MAX_SIZE * 2)
        for star in self.stars:
            tail = project(star.x, star.y, tail_depth(star.z, speed), center)
            if not area.collidepoint(tail):
                continue  # the head is even further out
            head = project(star.x, star.y, star.z, center)
            size = star_size(star.z)
            color = star_color(star)
            pygame.draw.line(screen, color, tail, head, size)
            if size > 2:
                pygame.draw.circle(screen, color, head, size / 2)  # round end for big stars
