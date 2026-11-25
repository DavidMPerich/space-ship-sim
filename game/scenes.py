"""Game scenes: ready -> opening -> countdown -> flight -> landing -> arrival -> ready again, forever."""

import math

import pygame

import config
from game import effects, launch
from game.input import InputState
from game.landing import Landing
from game.moon import Moon, ProgressIndicator
from game.rocket import Rocket
from game.starfield import Starfield

READY = "ready"
OPENING = "opening"
COUNTDOWN = "countdown"
FLIGHT = "flight"
LANDING = "landing"
ARRIVAL = "arrival"


def _ease(value, target, rate, dt):
    return target + (value - target) * math.exp(-rate * dt)


class Flight:
    """Flying to the moon: controls drive the rocket, and the rocket drives the starfield."""

    def __init__(self):
        self.rocket = Rocket()
        self.stars = Starfield()
        self.moon = Moon()
        self.indicator = ProgressIndicator()
        self.sky = launch.Sky()
        self.landing = Landing(self.moon.picture)
        self.reset()

    def reset(self):
        """Back to the launch pad. Pictures are kept, so this is instant."""
        self.rocket.reset()
        self.altitude = 0.0   # 0 = in the hangar, 1 = out in space
        self.landing_time = None   # seconds since the landing began, None before that
        self.landing_speed = 0.0
        self.star_flow = 0.0  # eases to 1 at launch and back to 0 after arrival

    def update(self, controls, dt):
        self.rocket.update(controls, dt)
        dt = max(0.0, dt)
        if self.rocket.arrived:
            if self.landing_time is None:
                self.landing_time, self.landing_speed = 0.0, self.rocket.speed
            self.landing_time += min(dt, config.MAX_FRAME_TIME)
            self.star_flow = _ease(self.star_flow, 0.0, config.STAR_STOP_RATE, dt)
        else:
            self.star_flow = _ease(self.star_flow, 1.0, config.LAUNCH_RATE, dt)
        self._climb(self.rocket.speed * self.star_flow, dt)
        self.stars.update(self.rocket.speed * self.star_flow, dt, self.rocket.turn_rate)

    def _climb(self, speed, dt):
        ascent = min(config.ASCENT_DISTANCE, config.TRIP_DISTANCE * config.ASCENT_MAX_SHARE)
        self.altitude = min(1.0, self.altitude + speed * min(dt, config.MAX_FRAME_TIME) / ascent)

    def draw(self, screen):
        self.draw_view(screen)
        self.draw_indicator(screen)

    def draw_view(self, screen):
        background = launch.sky_color(self.altitude)
        brightness = launch.star_brightness(self.altitude)
        heading = self.rocket.heading
        screen.fill(background)
        self.stars.draw(screen, background, brightness)
        if self.landing_time is not None:
            self.landing.draw(screen, self.landing_time, self.landing_speed, heading)
            return
        self.moon.draw(screen, self.rocket.progress, heading, brightness)
        self.sky.draw_clouds(screen, self.altitude, heading)

    def draw_indicator(self, screen):
        self.indicator.draw(screen, self.rocket.progress)


class Game:
    """Runs the scenes in order. Buttons can start the launch, but never skip anything else."""

    def __init__(self):
        self.flight = Flight()
        self.hangar = launch.Hangar()
        self.glow = launch.ThrusterGlow()
        self.numbers = [effects.draw_text_picture(word, config.COUNTDOWN_SIZE) for word in config.COUNTDOWN_WORDS]
        self.blast_off = effects.draw_text_picture(config.BLAST_OFF_TEXT, config.BLAST_OFF_SIZE)
        self.arrival_text = effects.draw_text_picture(config.ARRIVAL_TEXT, config.ARRIVAL_SIZE)
        self.cover = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.cover.fill(config.BACKGROUND_COLOR)
        self.last = InputState()  # last frame's controls, to notice new presses
        self.lean = 0.0           # smoothed stick, so the countdown numbers follow it
        self.begin_ready()

    def _enter(self, scene):
        self.scene = scene
        self.time = 0.0  # seconds in this scene
        self.pop = 0.0   # 1 = number just appeared or button pressed, easing to 0

    def begin_ready(self):
        self.flight.reset()
        self.fade = 1.0  # 1 = screen covered, 0 = clear
        self._enter(READY)

    def begin_opening(self):
        self._enter(OPENING)
        self.pop = 1.0

    def begin_countdown(self):
        self._enter(COUNTDOWN)
        self.pop = 1.0

    def begin_flight(self):
        self._enter(FLIGHT)

    def begin_landing(self):
        self._enter(LANDING)

    def begin_arrival(self):
        self._enter(ARRIVAL)

    def update(self, controls, dt):
        dt = max(0.0, min(config.MAX_FRAME_TIME, dt))
        pressed = self._new_press(controls)
        self.lean = _ease(self.lean, controls.steer, config.LEAN_RATE, dt)
        self.pop = _ease(self.pop, 0.0, config.POP_RATE, dt)
        self.time += dt
        if self.scene == READY:
            self._update_ready(pressed)
        elif self.scene == OPENING:
            self._update_opening(pressed)
        elif self.scene == COUNTDOWN:
            self._update_countdown(pressed, dt)
        elif self.scene == FLIGHT:
            self._update_flight(controls, dt)
        elif self.scene == LANDING:
            self._update_landing(dt)
        else:
            self._update_arrival(pressed, dt)
        self._update_fade(dt)

    def _new_press(self, controls):
        """True when any button went down this frame. Holding one doesn't count."""
        pressed = (controls.start_pressed or (controls.faster and not self.last.faster)
                   or (controls.slower and not self.last.slower))
        self.last = controls
        return pressed

    def _update_ready(self, pressed):
        if pressed or self.time >= config.AUTO_START_DELAY:
            self.begin_opening()

    def _update_opening(self, pressed):
        if self.time >= config.DOOR_TIME:
            self.begin_countdown()
        elif pressed:
            self.pop = 1.0

    def _update_countdown(self, pressed, dt):
        if self.time >= config.COUNTDOWN_STEP * len(self.numbers):
            self.begin_flight()
        elif self.number_index(self.time) != self.number_index(self.time - dt):
            self.pop = 1.0
        elif pressed:
            self.pop = max(self.pop, config.POP_PRESS)

    def _update_flight(self, controls, dt):
        self.flight.update(controls, dt)
        if self.flight.rocket.arrived:
            self.begin_landing()

    def _update_landing(self, dt):
        self.flight.update(InputState(), dt)  # hands off: the ship settles facing the moon
        if self.time >= config.LANDING_TIME:
            self.begin_arrival()

    def _update_arrival(self, pressed, dt):
        self.flight.update(InputState(), dt)
        if pressed:
            self.pop = 1.0
        if self.time >= config.ARRIVAL_PAUSE:
            self.begin_ready()

    def _update_fade(self, dt):
        leaving = self.scene == ARRIVAL and self.time >= config.ARRIVAL_PAUSE - config.SCENE_FADE
        step = dt / config.SCENE_FADE
        self.fade = max(0.0, min(1.0, self.fade + (step if leaving else -step)))

    def doors_open(self):
        """0 = roof shut, 1 = wide open. Starts and stops gently."""
        if self.scene == READY:
            return 0.0
        if self.scene == OPENING:
            return 0.5 - 0.5 * math.cos(math.pi * min(1.0, self.time / config.DOOR_TIME))
        return 1.0

    def thrust(self):
        """Thruster glow, building up at the end of the countdown."""
        if self.scene == COUNTDOWN:
            return launch.thrust_glow(self.time - config.COUNTDOWN_STEP * len(self.numbers))
        if self.scene == FLIGHT:
            return launch.thrust_glow(self.time)
        return 0.0

    def number_index(self, time):
        """Which countdown number shows at this time."""
        return max(0, min(len(self.numbers) - 1, int(time / config.COUNTDOWN_STEP)))

    def draw(self, screen):
        self.flight.draw_view(screen)
        if self.scene not in (LANDING, ARRIVAL):
            self.hangar.draw(screen, self.doors_open(), self.flight.altitude, self.pop)
            self.glow.draw(screen, self.thrust())
        self.flight.draw_indicator(screen)
        if self.scene == COUNTDOWN:
            self._draw_countdown(screen)
        elif self.scene == FLIGHT:
            self._draw_blast_off(screen)
        elif self.scene == ARRIVAL:
            self._draw_arrival(screen)
        if self.fade > 0.0:
            self.cover.set_alpha(round(255 * self.fade))
            screen.blit(self.cover, (0, 0))

    def _leaning_x(self):
        return config.SCREEN_WIDTH / 2 + self.lean * config.LEAN_DISTANCE

    def _bob(self):
        return math.sin(self.time * config.BOB_SPEED)

    def _draw_countdown(self, screen):
        picture = self.numbers[self.number_index(self.time)]
        if self.pop > 0.01:
            picture = pygame.transform.smoothscale_by(picture, 1.0 + config.POP_SIZE * self.pop)
        center = (self._leaning_x(), config.SCREEN_HEIGHT / 2)
        screen.blit(picture, picture.get_rect(center=center))

    def _draw_blast_off(self, screen):
        left = config.BLAST_OFF_TIME - self.time
        if left <= 0.0:
            return
        self.blast_off.set_alpha(round(255 * min(1.0, left / config.BLAST_OFF_FADE)))
        center = (config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2)
        screen.blit(self.blast_off, self.blast_off.get_rect(center=center))

    def _draw_arrival(self, screen):
        picture = self.arrival_text
        if self.pop > 0.01:
            picture = pygame.transform.smoothscale_by(picture, 1.0 + config.ARRIVAL_POP * self.pop)
        center = (config.SCREEN_WIDTH / 2, config.ARRIVAL_TEXT_Y + self._bob() * config.BOB_HEIGHT)
        screen.blit(picture, picture.get_rect(center=center))
