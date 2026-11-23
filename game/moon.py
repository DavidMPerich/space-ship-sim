"""The moon that grows as the rocket gets closer, and the picture-only progress indicator."""

import math
from collections import OrderedDict
from pathlib import Path

import pygame

import config

ROOT = Path(__file__).resolve().parent.parent


def _clamp01(value):
    return max(0.0, min(1.0, value))


def moon_size(progress):
    """Moon diameter in pixels (always even, so it stays centered as it grows)."""
    grown = _clamp01(progress) ** config.MOON_GROWTH
    size = config.MOON_MIN_SIZE + (config.MOON_MAX_SIZE - config.MOON_MIN_SIZE) * grown
    return 2 * int(size / 2)


def moon_center(heading):
    """Screen position of the moon. Turning right slides it left, at the same rate as the stars."""
    return (config.SCREEN_WIDTH / 2 - heading * config.STAR_FOCAL, config.SCREEN_HEIGHT / 2)


def draw_moon_picture(size):
    """A friendly cratered moon, drawn large and shrunk for smooth edges."""
    big = size * 2
    picture = pygame.Surface((big, big), pygame.SRCALPHA)
    pygame.draw.circle(picture, config.MOON_COLOR, (big / 2, big / 2), big / 2)
    for x, y, radius in config.MOON_CRATERS:
        pygame.draw.circle(picture, config.MOON_CRATER_COLOR, (x * big, y * big), radius * big)
    return pygame.transform.smoothscale(picture, (size, size))


def load_moon_picture(size, path=None):
    """The moon image at the given size, or a drawn moon if the file is missing or broken."""
    path = ROOT / config.MOON_IMAGE if path is None else path
    try:
        image = pygame.image.load(path)
        if pygame.display.get_surface():
            image = image.convert_alpha()
        return pygame.transform.smoothscale(image, (size, size))
    except (pygame.error, OSError, ValueError):
        return draw_moon_picture(size)


class Moon:
    def __init__(self, image_path=None):
        self.picture = load_moon_picture(config.MOON_MAX_SIZE, image_path)
        self.cache = OrderedDict()  # size -> scaled picture, oldest first

    def scaled(self, size):
        """The moon at this size, reusing recent ones instead of rescaling every frame."""
        if size in self.cache:
            self.cache.move_to_end(size)
        else:
            self.cache[size] = pygame.transform.smoothscale(self.picture, (size, size))
            while len(self.cache) > config.MOON_CACHE_SIZE:
                self.cache.popitem(last=False)
        return self.cache[size]

    def draw(self, screen, progress, heading):
        size = moon_size(progress)
        x, y = moon_center(heading)
        if x + size < 0 or x - size > config.SCREEN_WIDTH:
            return  # turned away
        screen.blit(self.scaled(size), (round(x - size / 2), round(y - size / 2)))


def draw_rocket_picture(size):
    """A little rocket pointing right, drawn large and shrunk for smooth edges."""
    big = size * 4
    picture = pygame.Surface((big, big), pygame.SRCALPHA)

    def points(*pairs):
        return [(x * big, y * big) for x, y in pairs]

    pygame.draw.polygon(picture, (255, 190, 60), points((0.22, 0.38), (0.0, 0.5), (0.22, 0.62)))   # flame
    pygame.draw.polygon(picture, (230, 70, 70), points((0.2, 0.36), (0.1, 0.12), (0.5, 0.36)))     # top fin
    pygame.draw.polygon(picture, (230, 70, 70), points((0.2, 0.64), (0.1, 0.88), (0.5, 0.64)))     # bottom fin
    pygame.draw.polygon(picture, (230, 70, 70), points((0.7, 0.32), (1.0, 0.5), (0.7, 0.68)))      # nose
    pygame.draw.rect(picture, (240, 240, 250), (0.18 * big, 0.32 * big, 0.54 * big, 0.36 * big),
                     border_radius=int(0.06 * big))                                                # body
    pygame.draw.circle(picture, (90, 180, 255), (0.54 * big, 0.5 * big), 0.1 * big)                # window
    return pygame.transform.smoothscale(picture, (size, size))


def indicator_x(progress):
    """Screen x of the rocket icon: the left end of the track at launch, the right end at the moon."""
    left = config.INDICATOR_MARGIN
    right = config.SCREEN_WIDTH - config.INDICATOR_MARGIN
    return left + (right - left) * _clamp01(progress)


class ProgressIndicator:
    def __init__(self):
        self.rocket = draw_rocket_picture(config.INDICATOR_ICON_SIZE)
        self.moon = draw_moon_picture(config.INDICATOR_ICON_SIZE)

    def draw(self, screen, progress):
        y = config.SCREEN_HEIGHT - config.INDICATOR_BOTTOM
        here = indicator_x(progress)
        for i in range(config.INDICATOR_DOTS):
            x = indicator_x(i / (config.INDICATOR_DOTS - 1))
            color = config.INDICATOR_DONE_COLOR if x <= here else config.INDICATOR_TODO_COLOR
            pygame.draw.circle(screen, color, (x, y), config.INDICATOR_DOT_RADIUS)
        # The moon waits just past the end of the track so the rocket lands beside it.
        screen.blit(self.moon, self.moon.get_rect(center=(indicator_x(1.0) + config.INDICATOR_ICON_SIZE, y)))
        screen.blit(self.rocket, self.rocket.get_rect(center=(round(here), y)))
