# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project overview

A simple **rocket ship simulator** for a 3-year-old, running on a **Raspberry Pi**.
The player flies through space in first person until the rocket reaches the **moon**.
Speed and direction are controlled with kid-friendly physical inputs (arcade joystick + big buttons).

The audience is a toddler. Every decision should favor **simple, bright, forgiving, and fun**
over realism or complexity.

## Tech stack

- **Language:** Python 3 (whatever ships with Raspberry Pi OS)
- **Graphics/input/audio:** `pygame-ce` (import name is still `pygame`)
- **Optional GPIO input:** `gpiozero` (only if buttons are wired directly to GPIO pins)
- **Target hardware:** Raspberry Pi (model TBD), fullscreen display, USB arcade joystick/encoder (shows up as a gamepad)

Avoid adding heavy dependencies. Anything new must install cleanly on Raspberry Pi OS (ARM).

## Project status

`docs/plan.md` has the step-by-step build plan and the sign-off log. Work one step at a time, and only
start the next step after the user signs off the current one. Steps 0–5 (skeleton, keyboard input,
rocket state, starfield, flight scene, moon and progress indicator) are signed off.

## Project structure

```
Space-Ship-Sim/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── requirements-dev.txt # Adds pytest; not needed on the Pi
├── main.py              # Entry point: init, game loop
├── config.py            # Tunable constants (speeds, distances, colors, FPS, input mapping)
├── docs/
│   └── plan.md          # Build plan and sign-off log
├── game/
│   ├── starfield.py     # 3D-projected starfield (the "flying" effect)
│   ├── rocket.py        # Player state: speed, turning, heading, distance to moon
│   ├── input.py         # Unified input: keyboard (joystick and buttons planned)
│   ├── moon.py          # Moon that grows as distance shrinks, and the progress indicator
│   ├── audio.py         # (planned) Engine rumble, beeps, arrival sounds
│   ├── effects.py       # Outlined text, start button and confetti
│   └── scenes.py        # Ready, countdown, flight, arrival celebration and restart
├── tests/               # pytest, one file per plan step; runs headless
└── assets/              # (planned)
    ├── images/
    └── sounds/
```

## How to run

```bash
pip install -r requirements.txt   # on Pi OS, may need --break-system-packages or a venv
python3 main.py
```

- `--windowed`: run in a window for development on a desktop machine.
- `--debug`: show live input and rocket values on screen.
- `--frames N`: quit after N frames (for headless smoke tests).
- Tests: `python -m pytest` from the venv (headless; `tests/conftest.py` sets the dummy SDL drivers).
- **Keyboard fallback** must always work so the game can be developed and tested without the joystick:
  Left/Right or A/D = steer, Up/Space/W = faster, Down/S = slower, Space/Enter = start,
  Esc = quit (Esc is dev-only; see Safety).

## Core gameplay

1. **Launch:** big "3… 2… 1… BLAST OFF!" countdown (start with a button press or automatically).
2. **Flight:** starfield streams outward from the center. Higher speed makes the stars move faster.
   Stars are round dots in white to soft yellow, with no streaks (streaks are saved for a possible
   "warp speed" effect later). Speed stays where it is set when a button is released.
   Steering really turns the ship: stars sweep sideways, the ship always flies toward the screen center,
   and releasing the stick lets the ship gently turn itself back toward the moon. Near the end, turning away
   is gently limited so the moon is always in view at arrival.
3. **Approach:** the moon starts as a small dot and grows steadily as distance decreases.
   A simple, picture-based progress indicator (a rocket icon moving from a little Earth to a finish line flag) beats numbers.
4. **Arrival:** celebration (sound, confetti/stars, "You made it to the Moon!"), then auto-restart after a pause.

There is **no failure state**: no crashing, no game over, no timers that punish. Steering changes
the ship's heading, but it never changes distance or arrival, so the player can never miss the moon.

## Design principles (toddler-first)

- **Big, bright, high-contrast visuals.** Minimal text; icons and colors over words.
- **Instant feedback.** Every button press produces a visible and audible response.
- **Forgiving controls.** Clamp speed to a gentle range; smooth (ease) all changes; no sudden jumps.
- **Short sessions.** A full trip to the moon should take about 1–3 minutes (tunable in `config.py`).
- **Nothing scary.** No loud harsh sounds, flashing/strobing, or dark/intense imagery.
- **Button mashing is fine.** Rapid or simultaneous presses must never break or crash the game.

## Coding conventions

- Keep it simple and readable. This is a hobby project for a parent, not a game engine.
- All tunable numbers (speed limits, trip length, star count, colors, FPS) live in `config.py`.
- Use frame-rate-independent movement (multiply by `dt` from `clock.tick()`).
- Target **60 FPS** but degrade gracefully on slower Pis (fewer stars, not lower responsiveness).
- Input handling is centralized in `game/input.py` so controls can be remapped in one place.
- Load assets once at startup; handle missing assets gracefully (fall back to drawn shapes or silence).
- Prefer small functions and plain classes; avoid clever abstractions.
- Type hints and short docstrings are welcome but not required everywhere.

## Performance notes (Raspberry Pi)

- Use `pygame.display.set_mode(..., pygame.FULLSCREEN)` with a fixed internal resolution and scale if needed.
- Use `convert()` / `convert_alpha()` on loaded images.
- Pre-render the moon at a few sizes, or cache scaled surfaces, instead of rescaling every frame.
- Keep the star count configurable (start around 200–400).

## Safety and robustness

- The game should start automatically on boot (systemd service or autostart; see README) and run unattended.
- In "kid mode" (default on the Pi), disable easy exits: no quit on a single key.
  Use a hidden combo (e.g., hold two specific buttons for 5 seconds) to exit.
- Catch and log unexpected exceptions, then restart the scene instead of crashing to the desktop.
- Handle the joystick being unplugged or replugged without crashing.

## Working with Claude

- Make small, incremental changes and keep the game runnable after each one.
- When adding a feature, add any new tunables to `config.py`.
- Don't introduce new dependencies without asking.
- If something affects the toddler experience (difficulty, sounds, visuals), call it out in the summary.
- Test with the keyboard fallback when no joystick is present.

## Open questions / TBD

- Raspberry Pi model and display resolution
- Exact input hardware (USB arcade encoder vs. GPIO-wired buttons)
- Whether to add a cockpit frame/overlay
- Sound assets (source or create)
