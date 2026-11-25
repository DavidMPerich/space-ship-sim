"""3D-projected starfield: stars stream outward from the screen center and sweep sideways in turns."""

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


def star_rate(speed):
    """Star depth per second: directly proportional to rocket speed."""
    return max(0.0, min(config.MAX_SPEED, speed)) * config.STAR_RATE


def _mix(low, high, fraction):
    return low + (high - low) * fraction


def vanishing_point():
    """Screen point the rocket flies toward: always dead ahead, whatever the heading."""
    return (config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2)


def project(x, y, z, center):
    """Depth position to screen pixels."""
    scale = config.STAR_FOCAL / z
    return (center[0] + x * scale, center[1] + y * scale)


def star_color(star, background=config.BACKGROUND_COLOR, brightness=1.0):
    """Fade in from the background so new stars never pop. brightness 0 hides stars in daylight."""
    glow = max(0.0, min(1.0, (config.STAR_FAR - star.z) / config.STAR_FADE_DEPTH))
    glow *= brightness
    return tuple(int(_mix(back, full, glow)) for back, full in zip(background, star.color))


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
        if abs(star.y) < config.STAR_MIN_HEIGHT:
            star.y = math.copysign(config.STAR_MIN_HEIGHT, star.y)

    def _turn(self, star, angle):
        """Sweep a star sideways. One that leaves on one side comes back from off screen on the other."""
        star.x -= angle * star.z
        edge = config.STAR_TURN_EDGE
        side = 1 if angle > 0 else -1  # turning right brings new stars in from the right
        if star.x * side < -edge * star.z:
            star.x = side * star.z * (edge + self.rng.uniform(0, config.STAR_TURN_SPREAD))

    def update(self, speed, dt, turn_rate=0.0):
        dt = max(0.0, min(config.MAX_FRAME_TIME, dt))
        step = star_rate(speed) * dt
        angle = turn_rate * dt
        for star in self.stars:
            star.z -= step
            if star.z <= config.STAR_NEAR:
                star.z += config.STAR_FAR - config.STAR_NEAR
                self._place(star)
            if angle:
                self._turn(star, angle)

    def draw(self, screen, background=config.BACKGROUND_COLOR, brightness=1.0):
        if brightness <= 0.0:
            return
        center = vanishing_point()
        area = screen.get_rect().inflate(config.STAR_MAX_SIZE * 2, config.STAR_MAX_SIZE * 2)
        for star in self.stars:
            position = project(star.x, star.y, star.z, center)
            if not area.collidepoint(position):
                continue
            size = star_size(star.z)
            color = star_color(star, background, brightness)
            if size > 2:
                pygame.draw.circle(screen, color, position, size / 2)
            else:
                screen.fill(color, (position[0], position[1], size, size))  # too small for a circle
