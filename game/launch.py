"""The launch: a hangar roof that opens, the sky and clouds above it, and the thruster glow."""

import math
import random
from collections import OrderedDict

import pygame

import config


def _share(value, start, end):
    """How far value is from start to end, 0 to 1, easing gently at both ends."""
    share = max(0.0, min(1.0, (value - start) / (end - start)))
    return share * share * (3 - 2 * share)


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
    return _share(altitude, config.STARS_APPEAR, 1.0)


def mist_strength(altitude):
    """How thick the cloud around the ship is: rises and clears again while passing through."""
    start, middle, end = config.MIST_START, config.MIST_MIDDLE, config.MIST_END
    if altitude < middle:
        return config.MIST_MAX * _share(altitude, start, middle)
    return config.MIST_MAX * (1.0 - _share(altitude, middle, end))


def thrust_glow(seconds):
    """Thruster glow, 0 to 1. seconds counts from liftoff and is negative during the countdown."""
    if seconds < config.THRUST_PEAK:
        return _share(seconds, -config.THRUST_LEAD, config.THRUST_PEAK)
    return 1.0 - _share(seconds, config.THRUST_PEAK, config.THRUST_PEAK + config.THRUST_FADE)


def draw_cloud_picture(rng):
    """A puffy cloud, drawn large, then shrunk and grown again so its edges are soft."""
    width, height = config.CLOUD_PICTURE_SIZE
    big = pygame.Surface((width * 2, height * 2), pygame.SRCALPHA)
    big.fill((*config.CLOUD_COLOR, 0))
    for shade, shift in ((config.CLOUD_SHADE, 0.05), (config.CLOUD_COLOR, 0.0)):
        puffs = random.Random(rng)  # the same puffs twice: shaded underneath, bright on top
        for i in range(config.CLOUD_PUFFS):
            along = (i + 0.5) / config.CLOUD_PUFFS
            x = 0.16 + 0.68 * along
            radius = puffs.uniform(0.12, 0.2) * (0.6 + 0.6 * math.sin(along * math.pi))
            y = 0.52 + puffs.uniform(-0.12, 0.1) + shift
            center = (x * width * 2, y * height * 2)
            pygame.draw.circle(big, (*shade, 255), center, radius * height * 2.6)
    soft = pygame.transform.smoothscale(big, (width // 4, height // 4))
    return pygame.transform.smoothscale(soft, (width, height))


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
        self.pictures = [draw_cloud_picture(config.CLOUD_SEED + i) for i in range(config.CLOUD_KINDS)]
        self.cache = OrderedDict()  # (picture, width) -> scaled picture, oldest first
        self.clouds = []
        for i in range(config.CLOUD_COUNT):
            height = rng.uniform(config.CLOUD_LOW, config.CLOUD_HIGH)
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
        for cloud in self.clouds:
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
            picture.set_alpha(round(255 * (1.0 - _share(width, config.CLOUD_FADE_SIZE, config.CLOUD_GONE_SIZE))))
            screen.blit(picture, spot)


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
                heat = _share(out, config.THRUST_INNER, config.THRUST_OUTER)
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
