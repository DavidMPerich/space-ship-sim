"""Landing: the moon keeps growing, its edge becomes the horizon, and the ship settles on the ground."""

import functools
import math
import random

import pygame

import config
from game import effects
from game.moon import draw_earth_picture, moon_center


def _closest():
    """How far away the moon still is when the landing starts (see moon_size)."""
    return config.TRIP_DISTANCE * config.MOON_MIN_SIZE / (config.MOON_MAX_SIZE - config.MOON_MIN_SIZE)


def landing_size(seconds, speed):
    """Moon diameter in pixels. Carries on at the flight speed, then slows gently to a stop."""
    start = _closest()
    end = start * config.MOON_MAX_SIZE / config.LANDING_SIZE
    t = max(0.0, min(1.0, seconds / config.LANDING_TIME))
    # A smooth curve from start to end that begins at -speed and finishes at rest.
    gap = ((2 * t**3 - 3 * t**2 + 1) * start + (t**3 - 2 * t**2 + t) * -speed * config.LANDING_TIME
           + (3 * t**2 - 2 * t**3) * end)
    return config.MOON_MAX_SIZE * start / gap


def horizon_y(seconds):
    """Screen height of the moon's top edge, sinking to the horizon as the ship levels out."""
    start = (config.SCREEN_HEIGHT - config.MOON_MAX_SIZE) / 2
    share = effects.smooth_share(seconds / config.LANDING_TIME, 0.0, 1.0)
    return start + (config.LANDING_HORIZON - start) * share


def _crater(picture, x, y, radius, flat):
    """A crater lying on the ground: a lit far wall, a shadowed floor and a pale rim."""
    tall = radius * flat
    rim = pygame.Rect(0, 0, radius * 2.2, tall * 2.2)
    rim.center = (x, y)
    floor = pygame.Rect(0, 0, radius * 2, tall * 2)
    floor.center = (x, y)
    lit = pygame.Rect(0, 0, radius * 1.7, tall * 1.5)
    lit.center = (x + radius * 0.1, y + tall * 0.25)
    for color, rect in (((206, 205, 202), rim), ((138, 138, 140), floor), ((165, 164, 163), lit)):
        if rect.width >= 2 and rect.height >= 2:
            pygame.draw.ellipse(picture, color, rect)


@functools.lru_cache(maxsize=None)
def draw_ground_picture():
    """The moon's surface, from the horizon down. Drawn large and shrunk for smooth edges."""
    rng = random.Random(config.MOON_SEED)
    width, height = config.SCREEN_WIDTH * 2, (config.SCREEN_HEIGHT - config.LANDING_HORIZON + config.GROUND_EXTRA) * 2
    picture = pygame.Surface((width, height), pygame.SRCALPHA)
    picture.fill(config.GROUND_COLOR)
    noise = effects.draw_noise(256, rng)
    rows = 40
    for row in range(rows):  # squeezed together toward the horizon, like ground seen at a slant
        near, far = ((row + 1) / rows) ** 2, (row / rows) ** 2
        strip = noise.subsurface((0, int(row / rows * 250), 256, 6))
        top, bottom = int(far * height), int(math.ceil(near * height))
        zoomed = pygame.transform.smoothscale(strip, (width, max(1, bottom - top)))
        zoomed.fill((70, 70, 70), special_flags=pygame.BLEND_RGB_MULT)
        zoomed.fill((180, 180, 180), special_flags=pygame.BLEND_RGB_ADD)
        picture.blit(zoomed, (0, top), special_flags=pygame.BLEND_RGB_MULT)
    soft = pygame.transform.smoothscale(picture, (width // 8, height // 8))
    picture = pygame.transform.smoothscale(soft, (width, height))
    craters = sorted(rng.random() ** 1.6 for _ in range(config.GROUND_CRATERS))  # far ones first
    for depth in craters:
        radius = (6 + 150 * depth) * rng.uniform(0.35, 1.0)
        _crater(picture, rng.uniform(0, width), height * (0.03 + 0.97 * depth), radius, 0.2 + 0.18 * depth)
    for _ in range(config.GROUND_ROCKS):
        depth = rng.random() ** 1.5
        size = 3 + 18 * depth * rng.random()
        x, y = rng.uniform(0, width), height * (0.05 + 0.95 * depth)
        pygame.draw.ellipse(picture, (105, 105, 110), (x - size, y - size * 0.3, size * 2.6, size))
        pygame.draw.ellipse(picture, (205, 204, 202), (x - size, y - size, size * 2, size * 1.5))
    # Cut the top along the moon's curve.
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    radius = config.LANDING_SIZE  # in this double-size picture
    pygame.draw.circle(mask, (255, 255, 255, 255), (width // 2, radius), radius)
    picture.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return pygame.transform.smoothscale(picture, (width // 2, height // 2))


def draw_dust_picture(size):
    """One soft puff of dust."""
    small = pygame.Surface((size // 4, size // 4), pygame.SRCALPHA)
    middle = size / 8
    for x in range(size // 4):
        for y in range(size // 4):
            out = math.hypot(x + 0.5 - middle, y + 0.5 - middle) / middle
            alpha = round(220 * (1.0 - effects.smooth_share(out, 0.0, 1.0)))
            small.set_at((x, y), (*config.DUST_COLOR, alpha))
    return pygame.transform.smoothscale(small, (size, size))


class Landing:
    def __init__(self, moon_picture):
        self.moon_picture = moon_picture
        self.ground = draw_ground_picture()
        self.earth = draw_earth_picture(config.LANDING_EARTH_SIZE)
        self.dust = draw_dust_picture(config.DUST_SIZE)
        rng = random.Random(config.MOON_SEED)
        self.puffs = [(rng.uniform(-1, 1), rng.uniform(0.4, 1.0)) for _ in range(config.DUST_COUNT)]

    def draw(self, screen, seconds, speed, heading):
        """seconds since the landing began. Afterward it stays on the ground."""
        share = seconds / config.LANDING_TIME
        self._draw_earth(screen, effects.smooth_share(share, 0.65, 1.0))
        ground = effects.smooth_share(share, *config.GROUND_FADE)
        top = horizon_y(seconds)
        if ground < 1.0:
            size = round(landing_size(seconds, speed))
            rect = pygame.Rect(0, 0, size, size)
            rect.midtop = (round(moon_center(heading)[0]), round(top))
            effects.draw_zoomed(screen, self.moon_picture, rect)
        if ground > 0.0:
            self.ground.set_alpha(round(255 * ground))
            # It rises into place with the horizon.
            screen.blit(self.ground, (0, round(top)))
        self._draw_dust(screen, seconds - config.LANDING_TIME + config.DUST_LEAD)

    def _draw_earth(self, screen, strength):
        if strength > 0.0:
            self.earth.set_alpha(round(255 * strength))
            screen.blit(self.earth, self.earth.get_rect(center=config.LANDING_EARTH_CENTER))

    def _draw_dust(self, screen, seconds):
        """Dust drifts up and outward around touchdown, then settles."""
        share = seconds / config.DUST_TIME
        if not 0.0 < share < 1.0:
            return
        self.dust.set_alpha(round(255 * math.sin(math.pi * share)))
        spread = 0.35 + 0.65 * math.sqrt(share)
        for side, lift in self.puffs:
            center = (config.SCREEN_WIDTH / 2 * (1 + side * spread * 1.1),
                      config.SCREEN_HEIGHT + 40 - config.DUST_RISE * lift * math.sin(math.pi * 0.5 * share))
            screen.blit(self.dust, self.dust.get_rect(center=center))
