"""Step 7: engine, thrusters, roof, beeps, landing and jingle."""

import array
import math
import wave

import pygame
import pytest

import config
import main
from conftest import ROOT
from game import audio
from game.audio import Audio
from game.input import InputHandler, InputState
from game.scenes import ARRIVAL, COUNTDOWN, FLIGHT, LANDING, OPENING, Game

DT = 1 / 60
NEUTRAL = InputState()
NAMES = audio.LOOPS + audio.ONE_TIME + [audio.BUTTON]


class FakeAudio(Audio):
    """Writes down what the game asks for."""

    def __init__(self):
        super().__init__()
        self.sounds = {}
        self.played = []

    def play(self, name):
        self.played.append(name)


class FakeSound:
    def __init__(self):
        self.volumes = []

    def set_volume(self, volume):
        self.volumes.append(volume)

    def play(self, *args, **kwargs):
        return None

    def get_busy(self):
        return False

    def stop(self):
        pass


@pytest.fixture
def game():
    return Game(FakeAudio())


@pytest.fixture
def mixer():
    pygame.mixer.init()
    yield
    pygame.mixer.quit()


def run_for(game, seconds, controls=NEUTRAL):
    for _ in range(round(seconds / DT)):
        game.update(controls, DT)


def read_sound(name):
    with wave.open(str(ROOT / config.SOUND_FOLDER / f"{name}.wav"), "rb") as file:
        assert file.getsampwidth() == 2 and file.getnchannels() == 1
        data = array.array("h", file.readframes(file.getnframes()))
        return [s / 32768 for s in data], file.getframerate()


def test_game_runs_with_the_dummy_audio_driver():
    assert main.run(["--windowed", "--frames", "60"]) == 0


def test_game_runs_without_a_mixer(monkeypatch):
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)
    sound = Audio()
    assert sound.sounds == {}
    game = Game(sound)
    game.begin_opening()
    run_for(game, 12, InputState(faster=True, start_pressed=True))


def test_missing_and_broken_files_are_silent(mixer, tmp_path):
    (tmp_path / "button.wav").write_text("not a sound")
    sound = Audio(tmp_path)
    assert sound.sounds == {}
    game = Game(sound)
    game.begin_opening()
    run_for(game, 12, InputState(faster=True, start_pressed=True))


def test_every_sound_loads_and_plays(mixer):
    sound = Audio()
    assert set(sound.sounds) == set(NAMES)
    for name in audio.ONE_TIME + [audio.BUTTON]:
        sound.play(name)
    for name in audio.LOOPS:
        sound.set_loop(name, 0.3)
    sound.update(DT)
    assert all(sound.channels[name].get_busy() for name in audio.LOOPS)
    for name in audio.LOOPS:
        sound.set_loop(name, 0.0)
    for _ in range(300):
        sound.update(DT)
    assert not any(sound.channels[name].get_busy() for name in audio.LOOPS)


def test_one_time_sounds_play_at_their_own_volume(mixer):
    """Starting a sound must not put its channel back to full volume."""
    sound = Audio()
    for name in audio.ONE_TIME:
        sound.play(name)
        assert sound.channels[name].get_volume() == pytest.approx(config.SOUND_VOLUMES[name], abs=0.02)
    sound.set_loop("thrusters", 0.3)
    for _ in range(120):
        sound.update(DT)
    assert sound.channels["thrusters"].get_volume() == pytest.approx(0.3, abs=0.02)


def test_losing_the_speakers_mid_flight_never_raises():
    pygame.mixer.init()
    game = Game(Audio())
    game.begin_flight()
    run_for(game, 1)
    pygame.mixer.quit()
    run_for(game, 1, InputState(presses=1))
    assert game.scene == FLIGHT


def test_volume_never_exceeds_the_maximum(monkeypatch):
    monkeypatch.setattr(config, "SOUND_VOLUMES", dict.fromkeys(config.SOUND_VOLUMES, 5.0))
    sound = Audio()
    fakes = {name: FakeSound() for name in NAMES}
    sound.sounds = fakes
    sound.channels = {name: fakes[name] for name in audio.LOOPS + audio.ONE_TIME}
    for name in audio.ONE_TIME + [audio.BUTTON]:
        sound.play(name)
    for name in audio.LOOPS:
        sound.set_loop(name, 5.0)
    for _ in range(120):
        sound.update(DT)
    for name in NAMES:
        assert fakes[name].volumes and 0 <= max(fakes[name].volumes) <= config.MAX_VOLUME


def test_loop_volumes_change_smoothly():
    sound = Audio()
    sound.set_loop("thrusters", config.MAX_VOLUME)
    levels = [0.0]
    for _ in range(120):
        sound.update(DT)
        levels.append(sound.levels["thrusters"])
    assert levels == sorted(levels)
    assert max(b - a for a, b in zip(levels, levels[1:])) < 0.15
    assert levels[-1] == pytest.approx(config.MAX_VOLUME, abs=0.01)


def test_engine_gets_louder_and_brighter_with_speed():
    speeds = [config.MIN_SPEED + (config.MAX_SPEED - config.MIN_SPEED) * i / 20 for i in range(21)]
    pairs = [audio.engine_volumes(s, 1.0) for s in speeds]
    totals = [low + high for low, high in pairs]
    brightness = [high / (low + high) for low, high in pairs]
    assert totals == pytest.approx(sorted(totals)) and totals[-1] > totals[0] > 0
    assert brightness == sorted(brightness) and brightness[-1] > brightness[0]
    assert audio.engine_volumes(config.MAX_SPEED, 0.0) == (0.0, 0.0)


@pytest.mark.parametrize("scene", ["ready", "opening", "countdown", "flight", "landing", "arrival"])
def test_every_press_asks_for_a_beep_in_every_scene(game, scene):
    getattr(game, f"begin_{scene}")()
    for controls in (InputState(start_pressed=True), InputState(presses=1, faster=True),
                     InputState(presses=1, faster=True), InputState(presses=1, slower=True)):
        game.audio.played.clear()
        game.update(controls, DT)
        assert game.audio.played.count("button") == 1


def test_holding_a_button_beeps_once(game):
    run_for(game, 1.0, InputState(faster=True))
    assert game.audio.played.count("button") == 1


def test_input_counts_each_button_press_even_while_another_is_held():
    pygame.init()
    controls = InputHandler()
    for key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE, pygame.K_LEFT, pygame.K_q):
        controls.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
    assert controls.state().presses == 3  # steering and unknown keys are not buttons
    controls.begin_frame()
    assert controls.state().presses == 0
    pygame.quit()


def test_one_beep_for_each_countdown_number(game):
    game.begin_countdown()
    times = []
    elapsed = 0.0
    while game.scene == COUNTDOWN:
        if len(times) < game.audio.played.count("count"):
            times.append(elapsed)
        game.update(NEUTRAL, DT)
        elapsed += DT
    assert game.audio.played.count("count") == len(config.COUNTDOWN_WORDS) == len(times)
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert gaps == pytest.approx([config.COUNTDOWN_STEP] * len(gaps), abs=0.05)


def test_roof_sounds_only_while_it_moves(game):
    run_for(game, 1.0)
    assert game.audio.targets["roof"] == 0.0
    game.begin_opening()
    run_for(game, config.DOOR_TIME / 2)
    assert game.scene == OPENING and game.audio.targets["roof"] > 0.1
    assert "roof_stop" not in game.audio.played
    run_for(game, config.DOOR_TIME / 2 + 0.1)
    assert game.scene == COUNTDOWN and game.audio.targets["roof"] == 0.0
    assert game.audio.played.count("roof_stop") == 1


def test_thrusters_follow_the_glow(game):
    game.begin_countdown()
    for _ in range(round(16 / DT)):
        game.update(NEUTRAL, DT)
        assert game.audio.targets["thrusters"] == pytest.approx(
            min(config.MAX_VOLUME, config.THRUSTER_VOLUME * game.thrust()))
    assert game.scene == FLIGHT and game.audio.targets["thrusters"] == 0.0


def test_landing_thrust_swells_then_stops_at_touchdown():
    values = [audio.landing_thrust(i / 60) for i in range(round(config.LANDING_TIME * 60) + 1)]
    assert values[0] == 0.0 and values[-1] == pytest.approx(0.0) and max(values) == 1.0
    assert max(abs(b - a) for a, b in zip(values, values[1:])) < 0.05


def test_landing_thump_then_jingle_once_each(game):
    game.begin_flight()
    game.flight.rocket.distance = 0.01
    game.update(NEUTRAL, DT)
    assert game.scene == LANDING
    run_for(game, 3)
    assert game.audio.targets["thrusters"] > 0.1
    assert "touchdown" not in game.audio.played
    run_for(game, config.LANDING_TIME - 2.9)
    assert game.scene == ARRIVAL
    assert game.audio.played == ["touchdown"]
    run_for(game, config.ARRIVAL_PAUSE - 1)
    assert game.audio.played == ["touchdown", "jingle"]
    assert all(target < 0.01 for target in game.audio.targets.values())


def test_everything_is_quiet_on_the_launch_screen(game):
    game.begin_flight()
    run_for(game, 3)
    game.begin_ready()
    game.update(NEUTRAL, DT)
    assert set(game.audio.targets.values()) == {0.0}


@pytest.mark.parametrize("name", NAMES)
def test_sound_files_are_gentle(name):
    samples, _ = read_sound(name)
    assert max(abs(s) for s in samples) <= 0.85  # never clips
    assert abs(sum(samples) / len(samples)) < 0.01
    # Soft, not harsh: most of the sound is low and mid, so it changes little from sample to sample.
    power = sum(s * s for s in samples)
    change = sum((b - a) ** 2 for a, b in zip(samples, samples[1:]))
    assert change / power < 0.25


@pytest.mark.parametrize("name", audio.LOOPS)
def test_loops_repeat_without_a_click(name):
    samples, _ = read_sound(name)
    steps = [abs(b - a) for a, b in zip(samples, samples[1:])]
    assert abs(samples[0] - samples[-1]) <= max(steps)


@pytest.mark.parametrize("name", audio.ONE_TIME + [audio.BUTTON])
def test_one_time_sounds_start_and_end_silent(name):
    samples, _ = read_sound(name)
    assert abs(samples[0]) < 0.02 and max(abs(s) for s in samples[-20:]) < 0.02


def test_loops_are_evenly_loud():
    """No pulsing or dropouts in the rumbles."""
    for name in audio.LOOPS:
        samples, rate = read_sound(name)
        size = rate // 4
        levels = [math.sqrt(sum(s * s for s in samples[i:i + size]) / size)
                  for i in range(0, len(samples) - size + 1, size)]
        assert max(levels) / min(levels) < 1.8
