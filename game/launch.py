"""The launch: a hangar roof that opens, the sky and clouds above it, and the thruster glow."""

import functools
import math
import random
from collections import OrderedDict

import pygame

import config
from game.effects import draw_noise, draw_zoomed, smooth_share


def _blend(low, high, share):
    return tuple(round(a + (b - a) * share) for a, b in zip(low, high))


def sky_color(altitude):
    """Light blue at the ground (0), darkening to space (1)."""
    stops = [*config.SKY_STOPS, (1.0, config.BACKGROUND_COLOR)]
    for (low, low_color), (high, high_color) in zip(stops, stops[1:]):
        if altitude <= high:
            return _blend(low_color, high_color, max(0.0, (altitude - low) / (high - low)))
    return config.BACKGROUND_COLOR


def star_brightness(altitude):
    """Stars (and the moon) are hidden by daylight until the ship is above the clouds."""
    return smooth_share(altitude, config.STARS_APPEAR, 1.0)


def mist_strength(altitude):
    """How thick the cloud around the ship is: rises and clears again while passing through."""
    start, middle, end = config.MIST_START, config.MIST_MIDDLE, config.MIST_END
    if altitude < middle:
        return config.MIST_MAX * smooth_share(altitude, start, middle)
    return config.MIST_MAX * (1.0 - smooth_share(altitude, middle, end))


def thrust_glow(seconds):
    """Thruster glow, 0 to 1. seconds counts from liftoff and is negative during the countdown."""
    if seconds < config.THRUST_PEAK:
        return smooth_share(seconds, -config.THRUST_LEAD, config.THRUST_PEAK)
    return 1.0 - smooth_share(seconds, config.THRUST_PEAK, config.THRUST_PEAK + config.THRUST_FADE)


@functools.lru_cache(maxsize=None)
def draw_cloud_picture(seed, cover, picture_size):
    """A cloud seen from underneath: a gray, shadowed middle with thin, sunlit edges. Same every time."""
    rng = random.Random(seed)
    size = config.CLOUD_DETAIL
    shape, texture = draw_noise(size, rng), draw_noise(size, rng)
    picture = pygame.Surface((size, size), pygame.SRCALPHA)
    for x in range(size):
        for y in range(size):
            out = math.hypot(2 * (x + 0.5) / size - 1, 2 * (y + 0.5) / size - 1)
            thick = shape.get_at((x, y)).r / 255 + 0.45 * (1 - out * out) - 0.25 - cover
            solid = smooth_share(thick, 0.0, config.CLOUD_EDGE) * smooth_share(1.0 - out, 0.0, 0.3)
            bumps = texture.get_at((x, y)).r / 255 - 0.5
            shadow = max(0.0, min(1.0, smooth_share(thick, 0.02, 0.6 + config.CLOUD_COVER - cover) + bumps * 1.1 * solid))
            picture.set_at((x, y), (*_blend(config.CLOUD_COLOR, config.CLOUD_SHADE, shadow), round(255 * solid)))
    return pygame.transform.smoothscale(picture, picture_size)


class Cloud:
    def __init__(self, x, y, height, width, picture):
        self.x = x
        self.y = y
        self.height = height  # altitude where the ship reaches it
        self.width = width
        self.picture = picture


class Clouds:
    def __init__(self):
        rng = random.Random(config.CLOUD_SEED)
        self.pictures = [draw_cloud_picture(config.CLOUD_SEED + i, config.CLOUD_COVER, config.CLOUD_PICTURE_SIZE)
                         for i in range(config.CLOUD_KINDS)]
        self.ahead = draw_cloud_picture(config.CLOUD_SEED, config.CLOUD_AHEAD_COVER, config.CLOUD_AHEAD_SIZE)
        self.cache = OrderedDict()  # (picture, width) -> scaled picture, oldest first
        self.clouds = []
        for i in range(config.CLOUD_COUNT):
            # More of them up high, so there are always clouds ahead.
            height = config.CLOUD_LOW + (config.CLOUD_HIGH - config.CLOUD_LOW) * rng.random() ** 0.6
            self.clouds.append(Cloud(
                rng.uniform(-1, 1) * config.CLOUD_SPREAD * height, rng.uniform(-0.6, 0.6) * config.CLOUD_SPREAD * height,
                height,
                rng.uniform(config.CLOUD_MIN_WIDTH, config.CLOUD_MAX_WIDTH), i % config.CLOUD_KINDS))
        self.clouds.sort(key=lambda cloud: -cloud.height)  # far ones are drawn first

    def _scaled(self, picture, width):
        key = (picture, width)
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            size = (width, width * config.CLOUD_PICTURE_SIZE[1] // config.CLOUD_PICTURE_SIZE[0])
            self.cache[key] = pygame.transform.smoothscale(self.pictures[picture], size)
            while len(self.cache) > config.CLOUD_CACHE_SIZE:
                self.cache.popitem(last=False)
        return self.cache[key]

    def draw(self, screen, altitude, heading):
        area = screen.get_rect()
        ahead_drawn = False
        for cloud in self.clouds:
            if not ahead_drawn and cloud.height < config.CLOUD_AHEAD_HEIGHT:
                self._draw_ahead(screen, altitude, heading)
                ahead_drawn = True
            gap = cloud.height - altitude
            if gap <= 0.0:
                continue  # already passed
            scale = config.STAR_FOCAL / gap
            width = round(cloud.width * scale)
            if width >= config.CLOUD_GONE_SIZE:
                continue  # so close it has melted into mist
            spot = pygame.Rect(0, 0, width, width * config.CLOUD_PICTURE_SIZE[1] // config.CLOUD_PICTURE_SIZE[0])
            spot.center = (area.centerx + cloud.x * scale - heading * config.STAR_FOCAL,
                           area.centery + cloud.y * scale)
            if not area.colliderect(spot):
                continue
            picture = self._scaled(cloud.picture, width)
            picture.set_alpha(round(255 * (1.0 - smooth_share(width, config.CLOUD_FADE_SIZE, config.CLOUD_GONE_SIZE))))
            screen.blit(picture, spot)

    def ahead_rect(self, altitude, heading):
        """Where the cloud dead ahead is on screen. None once the ship is through it."""
        gap = config.CLOUD_AHEAD_HEIGHT - altitude
        if gap <= 0.0 or altitude >= config.CLOUD_AHEAD_FADE[1]:
            return None
        width = round(config.CLOUD_AHEAD_WIDTH * config.STAR_FOCAL / gap)
        rect = pygame.Rect(0, 0, width, width * config.CLOUD_AHEAD_SIZE[1] // config.CLOUD_AHEAD_SIZE[0])
        # It follows the steering a little, but never far enough to fly past it.
        limit = config.CLOUD_AHEAD_SHIFT
        shift = limit * math.tanh(heading * config.STAR_FOCAL / limit)
        rect.center = (round(config.SCREEN_WIDTH / 2 - shift), config.SCREEN_HEIGHT // 2)
        return rect

    def _draw_ahead(self, screen, altitude, heading):
        rect = self.ahead_rect(altitude, heading)
        if rect is None:
            return
        # Smooth while small; up close the picture is soft enough for the faster way.
        smooth = rect.width < 0.6 * config.CLOUD_AHEAD_SIZE[0]
        alpha = round(255 * (1.0 - smooth_share(altitude, *config.CLOUD_AHEAD_FADE)))
        draw_zoomed(screen, self.ahead, rect, smooth, alpha)


class Sky:
    """Everything between the hangar and space: sky color, clouds and the mist inside them."""

    def __init__(self):
        self.clouds = Clouds()
        self.mist = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.mist.fill(config.CLOUD_COLOR)

    def draw_clouds(self, screen, altitude, heading):
        self.clouds.draw(screen, altitude, heading)
        strength = mist_strength(altitude)
        if strength > 0.0:
            self.mist.set_alpha(round(255 * strength))
            screen.blit(self.mist, (0, 0))


class ThrusterGlow:
    """A warm oval border: yellow in the corners, through orange to red, then clear in the middle."""

    def __init__(self):
        columns, rows = config.SCREEN_WIDTH // 8, config.SCREEN_HEIGHT // 8
        small = pygame.Surface((columns, rows), pygame.SRCALPHA)
        for x in range(columns):
            for y in range(rows):
                out = math.hypot(2 * (x + 0.5) / columns - 1, 2 * (y + 0.5) / rows - 1)
                heat = smooth_share(out, config.THRUST_INNER, config.THRUST_OUTER)
                small.set_at((x, y), (*self._color(heat), round(255 * config.THRUST_MAX * heat)))
        picture = pygame.transform.smoothscale(small, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.strips = [(picture.subsurface(rect).copy(), rect) for rect in self._strip_rects()]

    def _strip_rects(self):
        """Thin rows that leave out the clear oval, so the empty middle of the screen costs nothing."""
        width, height, tall = config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 40
        rects = []
        for top in range(0, height, tall):
            bottom = min(height, top + tall)
            off = max(abs(2 * top / height - 1), abs(2 * bottom / height - 1)) / config.THRUST_INNER
            clear = config.THRUST_INNER * math.sqrt(max(0.0, 1 - off * off)) * width / 2
            side = math.ceil(width / 2 - clear) + 8  # a little extra for the soft edge
            if side * 2 >= width:
                rects.append(pygame.Rect(0, top, width, bottom - top))
            else:
                rects.append(pygame.Rect(0, top, side, bottom - top))
                rects.append(pygame.Rect(width - side, top, side, bottom - top))
        return rects

    def _color(self, heat):
        red, orange, yellow = config.THRUST_COLORS
        if heat < 0.6:
            return _blend(red, orange, heat / 0.6)
        return _blend(orange, yellow, (heat - 0.6) / 0.4)

    def draw(self, screen, strength):
        if strength <= 0.0:
            return
        for picture, rect in self.strips:
            picture.set_alpha(round(255 * strength))
            screen.blit(picture, rect)


class Hangar:
    """The room the rocket starts in, looking straight up at two roof doors hinged at the sides."""

    def __init__(self):
        self.half_width = config.HANGAR_HALF_WIDTH
        self.half_height = config.HANGAR_HALF_HEIGHT

    def frame_scale(self, altitude):
        """The opening grows as the ship rises through it. None once it is behind the ship."""
        gap = 1.0 - altitude * config.HANGAR_RISE
        if gap <= 0.0:
            return None
        scale = 1.0 / gap
        if self.half_width * scale > config.SCREEN_WIDTH / 2 and self.half_height * scale > config.SCREEN_HEIGHT / 2:
            return None
        return scale

    def door_point(self, share, opened):
        """A point on the right door, share 0 (hinge) to 1 (free edge). Returns (x from center, size)."""
        width = self.half_width / config.STAR_FOCAL  # door width, with the roof 1 unit away
        # At the widest angle the door lines up with the eye, so it is hidden edge-on behind the frame.
        angle = opened * (math.pi - math.atan(1.0 / width))
        size = 1.0 / (1.0 + share * width * math.sin(angle))  # farther away looks smaller
        return (self.half_width * (1.0 - share * math.cos(angle)) * size, size)

    def draw(self, screen, opened, altitude, lights):
        """opened: 0 shut to 1 open. lights: 0 to 1, how brightly the lamps shine."""
        scale = self.frame_scale(altitude)
        if scale is None:
            return
        if opened < 1.0:
            self._draw_doors(screen, opened)
        self._draw_frame(screen, scale, lights)

    def _draw_doors(self, screen, opened):
        middle_x, middle_y = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        slats = config.HANGAR_SLATS
        for side in (-1, 1):
            for i in range(slats):
                near_x, near = self.door_point(i / slats, opened)
                far_x, far = self.door_point((i + 1) / slats, opened)
                color = config.HANGAR_EDGE_COLOR if i == slats - 1 else config.HANGAR_DOOR_COLORS[i % 2]
                points = [(middle_x + side * near_x, middle_y - self.half_height * near),
                          (middle_x + side * far_x, middle_y - self.half_height * far),
                          (middle_x + side * far_x, middle_y + self.half_height * far),
                          (middle_x + side * near_x, middle_y + self.half_height * near)]
                pygame.draw.polygon(screen, color, points)
                pygame.draw.polygon(screen, config.HANGAR_LINE_COLOR, points, 2)

    def _draw_frame(self, screen, scale, lights):
        hole = pygame.Rect(0, 0, round(2 * self.half_width * scale), round(2 * self.half_height * scale))
        hole.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        width, height = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        for rect in ((0, 0, width, hole.top), (0, hole.bottom, width, height - hole.bottom),
                     (0, hole.top, hole.left, hole.height), (hole.right, hole.top, width - hole.right, hole.height)):
            if rect[2] > 0 and rect[3] > 0:
                screen.fill(config.HANGAR_WALL_COLOR, rect)
        pygame.draw.rect(screen, config.HANGAR_RIM_COLOR, hole.inflate(24, 24), 12)
        # Walls leading up from the room to the corners of the opening.
        for x, corner_x in ((0, hole.left), (width, hole.right)):
            for y, corner_y in ((0, hole.top), (height, hole.bottom)):
                pygame.draw.line(screen, config.HANGAR_LINE_COLOR, (x, y), (corner_x, corner_y), 4)
        lamp = _blend(config.HANGAR_LAMP_OFF, config.HANGAR_LAMP_ON, max(0.0, min(1.0, lights)))
        for i in range(config.HANGAR_LAMPS):
            x = hole.left + hole.width * (i + 0.5) / config.HANGAR_LAMPS
            pygame.draw.circle(screen, lamp, (x, hole.top - 40 * scale), 13 * scale)
