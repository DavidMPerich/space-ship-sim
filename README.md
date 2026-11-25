# Rocket to the Moon

A simple, toddler-friendly rocket ship simulator for the Raspberry Pi, built with pygame-ce.
Fly through space in first person until you reach the moon. See `docs/plan.md` for the build plan.

## Run

```bash
pip install -r requirements.txt   # on Raspberry Pi OS, use a venv or --break-system-packages
python3 main.py                   # fullscreen
python3 main.py --windowed        # in a window, for development
```

Keyboard (remap in `config.py`):

| Action | Keys |
|--------|------|
| Steer | Left/Right arrows, A/D |
| Faster | Up arrow, Space, W |
| Slower | Down arrow, S |
| Start | Space, Enter (or any faster/slower button) |
| Quit (development only) | Esc |

Add `--debug` to show live input and rocket values on screen. On Windows, use `python` instead of `python3`.

## Sounds

The sounds in `assets/sounds` were made with `python3 tools/make_sounds.py`. To use your own, replace a file
with a `.wav` of the same name. Volumes are in `config.py`. Missing sounds are simply silent.

## Develop and test

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt     # Windows: .venv\Scripts\pip
.venv/bin/python -m pytest                         # runs headless, no window or sound needed
```

`requirements-dev.txt` adds pytest and is not needed on the Pi.
