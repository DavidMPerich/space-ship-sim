"""Makes the game's sound files in assets/sounds. Run once on a desktop; the game only plays the results.

    python tools/make_sounds.py

Standard library only. To use a sound of your own instead, replace the file (same name) and don't rerun this,
or rerun it with the names of only the sounds to remake: python tools/make_sounds.py button count
"""

import array
import math
import random
import sys
import wave
from pathlib import Path

RATE = 22050
FOLDER = Path(__file__).resolve().parent.parent / "assets" / "sounds"


def tone(freq, t):
    return math.sin(math.tau * freq * t)


def low_pass(samples, cutoff):
    """Soften: remove what is above the cutoff (run twice for a steeper slope)."""
    share = 1.0 - math.exp(-math.tau * cutoff / RATE)
    for _ in range(2):
        level, result = 0.0, []
        for sample in samples:
            level += (sample - level) * share
            result.append(level)
        samples = result
    return samples


def high_pass(samples, cutoff):
    low = low_pass(samples, cutoff)
    return [a - b for a, b in zip(samples, low)]


def scaled(samples, peak):
    """Set the loudest point, after removing any constant offset."""
    middle = sum(samples) / len(samples)
    samples = [s - middle for s in samples]
    loudest = max(abs(s) for s in samples)
    return [s * peak / loudest for s in samples]


def leveled(samples, loudness, peak=0.8):
    """Set the average loudness, softly rounding off anything that would go over the peak."""
    middle = sum(samples) / len(samples)
    rms = math.sqrt(sum((s - middle) ** 2 for s in samples) / len(samples))
    return [peak * math.tanh((s - middle) * loudness / rms / peak) for s in samples]


def looped_noise(seconds, rng, low, high):
    """Noise between two frequencies whose end blends into its start, so it repeats without a seam."""
    count, blend = int(seconds * RATE), RATE // 2
    warm = RATE // 2  # lets the filters settle
    noise = [rng.uniform(-1, 1) for _ in range(warm + count + blend)]
    noise = scaled(high_pass(low_pass(noise, high), low)[warm:], 1.0)
    for i in range(blend):
        share = i / blend
        noise[i] = noise[i] * math.sqrt(share) + noise[count + i] * math.sqrt(1 - share)
    return noise[:count]


def steadied(samples, window=0.12):
    """Even out the loudness all the way around a loop, so it never swells like waves or wind."""
    size, half = len(samples), int(window * RATE / 2)
    power = sum(samples[i % size] ** 2 for i in range(-half, half))
    result = []
    for i in range(size):
        result.append(samples[i] / math.sqrt(max(power, 1e-9) / (2 * half)))
        power += samples[(i + half) % size] ** 2 - samples[(i - half) % size] ** 2
    return result


def rumble(seconds, seed, low, high, tones, tone_level):
    """A steady engine loop. Tones complete whole turns, so they repeat without a seam."""
    noise = steadied(looped_noise(seconds, random.Random(seed), low, high))
    result = []
    for i, sample in enumerate(noise):
        t = i / RATE
        hum = sum(level * tone(freq, t) for freq, level in tones)
        result.append(sample + hum * tone_level)
    return steadied(result)


def note(freq, seconds, decay, overtones=((1, 1.0),), attack=0.008):
    """A soft bell-like note that starts and ends without a click."""
    count = int(seconds * RATE)
    result = []
    for i in range(count):
        t = i / RATE
        shape = min(1.0, t / attack) * math.exp(-decay * t) * min(1.0, (count - i) / (0.02 * RATE))
        result.append(shape * sum(level * tone(freq * k, t) for k, level in overtones))
    return result


def engine_low():
    return leveled(rumble(12, 1, 40, 220, ((55, 1.0), (82.5, 0.6), (110, 0.5), (165, 0.25)), 0.25), 0.22)


def engine_high():
    return leveled(rumble(12, 2, 70, 480, ((82.5, 0.8), (123.75, 0.6), (165, 0.6), (247.5, 0.3)), 0.25), 0.22)


def thrusters():
    """Big, soft whoosh with a deep rumble underneath."""
    deep = leveled(rumble(5, 3, 35, 180, ((45, 1.0), (67.6, 0.5)), 0.2), 0.2)
    hiss = leveled(looped_noise(5, random.Random(4), 120, 900), 0.12)
    return leveled([a + b for a, b in zip(deep, hiss)], 0.24)


def roof():
    """A heavy electric motor, with a gentle pulse as it turns."""
    noise = leveled(looped_noise(4, random.Random(5), 80, 400), 0.06)
    result = []
    for i, sample in enumerate(noise):
        t = i / RATE
        pulse = 0.85 + 0.15 * tone(6, t)
        motor = tone(90, t) + 0.5 * tone(180, t) + 0.3 * tone(270, t) + 0.12 * tone(360, t)
        result.append(sample + 0.12 * motor * pulse)
    return leveled(result, 0.18)


def thump(seconds, start_freq, end_freq, decay, seed, puff):
    """A soft, low thud with a puff of filtered noise."""
    rng = random.Random(seed)
    count = int(seconds * RATE)
    noise = scaled(low_pass([rng.uniform(-1, 1) for _ in range(count)], 400), 1.0)
    result, phase = [], 0.0
    for i in range(count):
        t = i / RATE
        freq = end_freq + (start_freq - end_freq) * math.exp(-12 * t)
        phase += math.tau * freq / RATE
        ease = min(1.0, t / 0.015) * min(1.0, (count - i) / (0.05 * RATE))
        result.append(ease * (math.sin(phase) * math.exp(-decay * t) + puff * noise[i] * math.exp(-decay * 0.6 * t)))
    return result


def roof_stop():
    return scaled(thump(0.6, 120, 70, 9, 6, 0.3), 0.6)


def touchdown():
    """A cushioned thud, then dust settling."""
    return scaled(thump(2.0, 110, 50, 4.5, 7, 0.5), 0.75)


def button():
    return scaled(note(660, 0.16, 24, ((1, 1.0), (2, 0.2))), 0.5)


def count():
    return scaled(note(440, 0.45, 7, ((1, 1.0), (2, 0.3), (3, 0.08)), 0.012), 0.6)


SOUNDS = [engine_low, engine_high, thrusters, roof, roof_stop, touchdown, button, count]


def save(name, samples):
    data = array.array("h", (round(max(-1.0, min(1.0, s)) * 32767) for s in samples))
    if sys.byteorder == "big":
        data.byteswap()
    with wave.open(str(FOLDER / f"{name}.wav"), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(data.tobytes())


def main(names):
    FOLDER.mkdir(parents=True, exist_ok=True)
    for make in SOUNDS:
        if not names or make.__name__ in names:
            save(make.__name__, make())
            print("made", make.__name__)


if __name__ == "__main__":
    main(sys.argv[1:])
