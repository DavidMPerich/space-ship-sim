"""Shared drawing helpers: easing, big outlined text, random texture and zoomed pictures."""

import math

import pygame

import config


def draw_text_picture(text, size):
    """Big outlined text, made smaller if needed so it always fits on screen."""
    pygame.font.init()
    edge = config.TEXT_OUTLINE
    limit = config.SCREEN_WIDTH * config.TEXT_MAX_WIDTH - 2 * edge
    width = pygame.font.Font(None, size).size(text)[0]
    if width > limit:
        size = int(size * limit / width)
    font = pygame.font.Font(None, size)
    front = font.render(text, True, config.TEXT_COLOR)
    back = font.render(text, True, config.TEXT_OUTLINE_COLOR)
    picture = pygame.Surface((front.get_width() + 2 * edge, front.get_height() + 2 * edge), pygame.SRCALPHA)
    for i in range(16):
        angle = i * math.tau / 16
        picture.blit(back, (edge + math.cos(angle) * edge, edge + math.sin(angle) * edge))
    picture.blit(front, (edge, edge))
    return picture


def smooth_share(value, start, end):
    """How far value is from start to end, 0 to 1, easing gently at both ends."""
    share = max(0.0, min(1.0, (value - start) / (end - start)))
    return share * share * (3 - 2 * share)


def draw_zoomed(screen, picture, rect, smooth=True, alpha=255):
    """Draw picture stretched to rect. Only the part on screen is scaled, so huge sizes stay cheap."""
    shown = rect.clip(screen.get_rect())
    if not shown.width or not shown.height:
        return
    width, height = picture.get_size()
    across, down = rect.width / width, rect.height / height
    left, top = int((shown.left - rect.left) / across), int((shown.top - rect.top) / down)
    right = min(width, math.ceil((shown.right - rect.left) / across))
    bottom = min(height, math.ceil((shown.bottom - rect.top) / down))
    part = picture.subsurface((left, top, right - left, bottom - top))
    target = (max(1, round(part.get_width() * across)), max(1, round(part.get_height() * down)))
    resize = pygame.transform.smoothscale if smooth else pygame.transform.scale
    zoomed = resize(part, target)
    zoomed.set_alpha(alpha)
    screen.blit(zoomed, (round(rect.left + left * across), round(rect.top + top * down)))


def draw_noise(size, rng):
    """A soft cloudy pattern: big random blobs, with finer and finer detail added. Brightness 0-255."""
    cells = 5
    picture = pygame.Surface((cells, cells), depth=24)
    strength = 255
    while True:
        for x in range(cells):
            for y in range(cells):
                value = picture.get_at((x, y)).r if strength < 255 else 128
                value = max(0, min(255, value + int(rng.uniform(-0.5, 0.5) * strength)))
                picture.set_at((x, y), (value, value, value))
        if cells >= size:
            return pygame.transform.smoothscale(picture, (size, size))
        cells *= 2
        strength *= 0.55
        picture = pygame.transform.smoothscale(picture, (cells, cells))
