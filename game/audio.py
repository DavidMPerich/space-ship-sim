"""Sound: steady loops (engine, thrusters, roof) and one-time sounds. Missing sound or speakers mean silence."""

import math
from pathlib import Path

import pygame

import config

ROOT = Path(__file__).resolve().parent.parent
LOOPS = ["engine_low", "engine_high", "thrusters", "roof"]
ONE_TIME = ["roof_stop", "count", "touchdown"]  # each has its own channel, so it always plays
BUTTON = "button"                                         # shares what is left, so mashing can overlap


def prepare():
    """Call before pygame.init(), for low-delay sound."""
    pygame.mixer.pre_init(config.SOUND_RATE, -16, 2, config.SOUND_BUFFER)


def capped(volume):
    return max(0.0, min(config.MAX_VOLUME, volume))


def engine_volumes(speed, flow):
    """(low, high) engine loop volumes. Faster is louder and brighter. flow fades it in and out (0 to 1)."""
    share = (speed - config.MIN_SPEED) / (config.MAX_SPEED - config.MIN_SPEED)
    share = max(0.0, min(1.0, share))
    volume = (config.ENGINE_SLOW_VOLUME + (config.ENGINE_FAST_VOLUME - config.ENGINE_SLOW_VOLUME) * share) * flow
    return (volume * (1.0 - share), volume * share)


def landing_thrust(seconds):
    """Thrusters slowing the ship down (0 to 1): swells, then dies away just as it touches down."""
    rise = max(0.0, min(1.0, seconds / config.LANDING_THRUST_RISE))
    fall = max(0.0, min(1.0, (config.LANDING_TIME - seconds) / config.LANDING_THRUST_FALL))
    return min(rise, fall)


class Audio:
    def __init__(self, folder=None):
        self.folder = Path(folder) if folder else ROOT / config.SOUND_FOLDER
        self.sounds = {}
        self.channels = {}
        self.levels = dict.fromkeys(LOOPS, 0.0)  # where each loop's volume is now
        self.targets = dict.fromkeys(LOOPS, 0.0)  # and where it is easing to
        if not pygame.mixer.get_init():
            return
        pygame.mixer.set_num_channels(config.SOUND_CHANNELS)
        pygame.mixer.set_reserved(len(LOOPS) + len(ONE_TIME))
        for number, name in enumerate(LOOPS + ONE_TIME):
            self.channels[name] = pygame.mixer.Channel(number)
        for name in LOOPS + ONE_TIME + [BUTTON]:
            self._load(name)

    def _load(self, name):
        for ending in (".wav", ".ogg"):
            path = self.folder / (name + ending)
            if path.is_file():
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(path))
                    return
                except (pygame.error, OSError) as error:
                    print(f"Could not load {path.name}: {error}", flush=True)

    def play(self, name):
        """Play a one-time sound or the button beep."""
        sound = self.sounds.get(name)
        if sound is None:
            return
        volume = capped(config.SOUND_VOLUMES[name])
        try:
            if name in self.channels:
                self.channels[name].play(sound)
                self.channels[name].set_volume(volume)  # after play(), in case it resets the volume
            else:
                sound.set_volume(volume)
                sound.play()
        except pygame.error:
            self.sounds.clear()  # the speakers went away: carry on in silence

    def set_loop(self, name, volume):
        """Ask for a loop's volume. It gets there smoothly in update()."""
        self.targets[name] = capped(volume)

    def update(self, dt):
        share = 1.0 - math.exp(-config.SOUND_EASE_RATE * max(0.0, dt))
        for name in LOOPS:
            self.levels[name] += (self.targets[name] - self.levels[name]) * share
            self._apply_loop(name, self.levels[name])

    def _apply_loop(self, name, level):
        sound = self.sounds.get(name)
        if sound is None:
            return
        try:
            channel = self.channels[name]
            if level < 0.002 and self.targets[name] == 0.0:
                if channel.get_busy():
                    channel.stop()
                return
            channel.set_volume(capped(level))
            if not channel.get_busy():
                channel.play(sound, loops=-1)
                channel.set_volume(capped(level))  # in case play() reset the volume
        except pygame.error:
            self.sounds.clear()
