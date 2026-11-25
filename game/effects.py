"""Celebration and launch visuals: outlined text, the start button and confetti."""

import math
import random

import pygame

import config
from game.moon import draw_rocket_picture


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


def draw_ready_rocket():
    """The launch screen rocket, pointing up."""
    return pygame.transform.rotate(draw_rocket_picture(config.READY_ROCKET_SIZE), 90)


def draw_button(screen, center, down):
    """A big round push button. down runs from 0 (up) to 1 (pushed in)."""
    radius, (x, y) = config.READY_BUTTON_RADIUS, center
    pygame.draw.circle(screen, config.READY_BUTTON_SHADE, (x, y + radius * 0.25), radius)
    pygame.draw.circle(screen, config.READY_BUTTON_COLOR, (x, y + radius * 0.2 * down), radius)


class ConfettiPiece:
    def __init__(self, x, y, vx, vy, fall, color, phase, extra):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.fall = fall    # steady falling speed
        self.color = color
        self.phase = phase  # where it is in its side-to-side sway and tumble
        self.extra = extra  # burst pieces leave for good; the others start again at the top


class Confetti:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.pieces = []

    def start(self):
        """Fresh confetti, waiting above the screen to drift down."""
        self.pieces = []
        for _ in range(config.CONFETTI_COUNT):
            y = self.rng.uniform(-config.SCREEN_HEIGHT, -config.CONFETTI_SIZE)
            self._add(self.rng.uniform(0, config.SCREEN_WIDTH), y, 0.0, 0.0, False)

    def burst(self):
        """A little fountain, for a button press."""
        for _ in range(min(config.CONFETTI_BURST, config.CONFETTI_MAX - len(self.pieces))):
            angle = self.rng.uniform(0, math.tau)
            speed = config.CONFETTI_BURST_SPEED * self.rng.uniform(0.3, 1.0)
            self._add(config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2,
                      math.cos(angle) * speed, math.sin(angle) * speed, True)

    def _add(self, x, y, vx, vy, extra):
        self.pieces.append(ConfettiPiece(
            x, y, vx, vy, self.rng.uniform(*config.CONFETTI_FALL), self.rng.choice(config.CONFETTI_COLORS),
            self.rng.uniform(0, math.tau), extra))

    def update(self, dt):
        bottom = config.SCREEN_HEIGHT + config.CONFETTI_SIZE
        for piece in self.pieces:
            piece.phase += 3.0 * dt
            if piece.extra:
                piece.vy += config.CONFETTI_GRAVITY * dt
                piece.x += piece.vx * dt
                piece.y += piece.vy * dt
            else:
                piece.x += math.sin(piece.phase) * config.CONFETTI_SWAY * dt
                piece.y += piece.fall * dt
                if piece.y > bottom:
                    piece.y = -config.CONFETTI_SIZE
                    piece.x = self.rng.uniform(0, config.SCREEN_WIDTH)
        self.pieces = [piece for piece in self.pieces if piece.y <= bottom]

    def draw(self, screen):
        for piece in self.pieces:
            # A gentle tumble: the piece gets thinner and thicker as it turns.
            height = config.CONFETTI_SIZE * (0.35 + 0.65 * abs(math.cos(piece.phase)))
            screen.fill(piece.color, (piece.x, piece.y, config.CONFETTI_SIZE, height))
