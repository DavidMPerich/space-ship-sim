# Rocket to the Moon: Build Plan

## How to use this plan
- Do the steps in order. Each one leaves the game runnable.
- Each step ends with **Automated tests** (`pytest`), a **Manual checklist** and a **Sign-off** box.
- Start the next step only after the current one is signed off (initials and date).
- Automated tests run headless: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest`.
- Every step's sign-off also requires all earlier tests to still pass.

Sign-off template (used at the end of every step):
```
- [ ] All automated tests pass (pytest output pasted or summarized)
- [ ] Manual checklist completed
- [ ] Toddler-experience changes called out (if any)
Signed off by: ______  Date: ______
```

### Step 0: Project skeleton and test harness
Build: `requirements.txt` (pygame-ce), `requirements-dev.txt` (pytest), `config.py` (FPS, resolution, colors),
`main.py` that opens a window (`--windowed`) or fullscreen, fills it with a background colour, and quits on Esc.
Add a `--frames N` flag for headless smoke runs. Add `tests/conftest.py` to set the dummy SDL drivers. Add a README stub.
Automated tests:
- `config` imports, and FPS/resolution are positive ints.
- `main.py --windowed --frames 30` exits cleanly with code 0.
Manual: `python main.py --windowed` shows a coloured window, and Esc closes it.

### Step 1: Keyboard input module (`game/input.py`)
Build: an `InputState` (steer −1..1, faster, slower, start) produced from pygame events and held keys.
The key mapping lives in `config.py`.
Automated tests:
- Posting synthetic KEYDOWN/KEYUP events gives the expected state (left → −1, right → +1, both → 0).
- Mashing: 1,000 random key events never raise, and the values stay in range.
Manual: a debug overlay in the window shows live input values as you press keys.

### Step 2: Rocket state (`game/rocket.py`)
Build: speed eases toward a target that is clamped between `MIN_SPEED` and `MAX_SPEED`, steering is smoothed and turns the ship's heading,
distance shrinks with speed × dt, and an `arrived` flag is set. Pure logic, no drawing.
Automated tests:
- Speed never leaves the clamp range, and a single frame never jumps more than `config` allows.
- The same total time gives the same distance at 30 and 60 FPS (frame-rate independence).
- The trip takes between 60 and 180 s at both the minimum and the maximum speed (trip length tunable).
- Steering never changes distance or arrival, so there is no way to miss the moon.
- Heading changes while steering, and stays bounded when circling.
Manual: the overlay shows speed and distance responding smoothly to the keys.

### Step 3: Starfield (`game/starfield.py`)
Build: 3D-projected stars that stream outward, with star speed directly proportional to rocket speed.
Steering turns the ship: stars sweep sideways.
Stars are round dots in white to soft yellow (no streaks; see the warp speed idea below).
Star count comes from `config.py`.
Automated tests:
- The star count stays constant, and stars that pass the camera are recycled.
- Star colours stay between white and soft yellow.
- Long turns keep the sky full, and stars never pop in or out on screen.
- The projection maps the centre star to the vanishing point (always the screen centre), and turning sweeps stars sideways.
- A frame update at the maximum count stays under a time budget on a desktop (regression guard).
Manual: flying feels smooth, faster means quicker stars, steering visibly turns the ship, and nothing flickers.

### Step 4: Flight scene wired into `main.py`
Build: a game loop using `dt` from `clock.tick(FPS)` that feeds input → rocket → starfield and draws each frame.
Automated tests: a headless run of 600 frames with scripted input reaches the expected distance range without errors.
Manual: a full keyboard flight is playable end to end (arrival can be just a console message for now).

### Step 5: Moon and progress indicator (`game/moon.py`)
Build: a moon that grows from a dot as distance shrinks (true perspective, size ~ 1/distance), using
pre-rendered or cached sizes. The stars come to rest after arrival, so they match the moon.
The moon's screen position follows the ship's heading (it slides off-centre as the ship turns).
When the stick is released, the ship gently turns itself back toward the moon, the shortest way round
(decided 2026-11-23; replaced "heading kept on release" from Steps 2 and 3).
In the last part of the trip, turning away is gently limited so the moon is always in view at arrival.
If the moon image is missing, draw a circle instead. Add a rocket icon that moves along a track from a little Earth to a finish line flag.
Automated tests:
- Moon size is monotonic non-decreasing in progress, and full size at arrival.
- However the stick is held or mashed, the moon is on screen at arrival.
- From any heading, releasing the stick brings the ship smoothly back to facing the moon.
- A missing image file falls back to a drawn surface without raising.
- The scale cache doesn't grow without bound.
- The indicator's position runs from 0 to 1 as progress does.
Manual: the moon's growth looks steady, and the indicator is readable without any text.

### Step 6: Scenes (`game/scenes.py`)
Build: a countdown ("3, 2, 1, BLAST OFF!", started by a button press or automatically) → flight →
arrival celebration ("You made it to the Moon!", stars or confetti) → automatic restart after a pause.
Timings live in `config.py`.
Automated tests:
- Scene transitions run in the right order with a fake clock.
- The game restarts after `ARRIVAL_PAUSE`, and rocket state is reset.
- Pressing buttons during the countdown or arrival never skips into a broken state.
Manual: three full loops in a row, with big, bright text and nothing scary.

### Step 7: Audio (`game/audio.py`)
Build: an engine rumble whose volume and pitch feel follow speed, button beeps, and an arrival jingle,
all loaded once at startup. If the mixer or sound files are missing, the game continues in silence.
Automated tests:
- The game runs with the dummy audio driver and with missing files, without raising.
- Volume never exceeds `MAX_VOLUME`.
- Every button press asks for a beep (checked with a fake sound object).
Manual: the volume is gentle, there are no harsh sounds, and every press gives a sound.

### Step 8: Joystick and buttons
Build: gamepad support in `game/input.py`, with an axis deadzone, a button map in `config.py`,
and hot-plug handling (JOYDEVICEADDED/REMOVED). Optional `gpiozero` support only if the buttons are GPIO-wired, to be decided at this step.
Automated tests:
- A fake joystick axis gives clamped steering, and the deadzone is respected.
- Adding or removing a device mid-flight never raises, and the keyboard keeps working throughout.
- A fuzz test of 10,000 random button and axis events.
Manual: on the real arcade stick, unplug and replug it mid-flight, and mash every button at once.

### Step 9: Kid mode and robustness
Build: kid mode is the default on the Pi. Esc is disabled there, and the exit is a hidden combo
(hold two configured buttons for 5 seconds). Unexpected exceptions are logged to a file and the scene restarts.
Automated tests:
- Esc doesn't quit in kid mode.
- Holding the combo for 4.9 s does nothing, and 5 s quits.
- An exception injected into a scene update is logged and the scene restarts.
Manual: try every "obvious" exit, and confirm only the combo works.

### Step 10: Raspberry Pi performance
Build: fullscreen at a fixed internal resolution, scaled to the display. `convert()`/`convert_alpha()` on all images.
If FPS drops, reduce the star count automatically (never responsiveness). Optional FPS overlay.
Automated tests:
- The scaler keeps the aspect ratio for common display sizes.
- The auto-degrade lowers the star count when FPS is below target, and never goes under `MIN_STARS`.
Manual: on the actual Pi (model to be confirmed), a full trip holds about 60 FPS, or degrades gracefully.

### Step 11: Autostart on boot
Build: a systemd service (or autostart entry) in `deploy/` with Restart=always, plus README setup steps.
Automated tests: the service file contains the expected ExecStart and Restart keys (simple text check).
Manual: reboot the Pi, the game starts with no keyboard attached, and it recovers if the process is killed.

### Step 12: Polish and toddler playtest
Build: tune `config.py` (trip length, speeds, colours, volume), and finalize the sound and image assets.
Decide on the cockpit overlay (still an open question in CLAUDE.md).
Automated tests: the full suite passes, and a headless 3-loop soak test runs with no errors or growing memory.
Manual: a supervised playtest with the 3-year-old. Note confusion, fear or boredom, and adjust.

## Ideas for later
- Warp speed effect: stretch the stars into streaks.

## Sign-off log

| Step | Signed off by | Date | Notes |
|------|---------------|------|-------|
| 0 | Dave | 2026-11-22 | Blue window opens, Esc quits. 6/6 tests pass. |
| 1 | Dave | 2026-11-23 | Keyboard input and debug overlay checked by hand. 17/17 tests pass. |
| 2 | Dave | 2026-11-23 | Rocket speed, steering and distance checked by hand. Speed range kept at 6-12. 32/32 tests pass. |
| 3 | Dave | 2026-11-23 | Round white/soft yellow stars, no streaks; steering really turns the ship. Checked by hand. 52/52 tests pass. |
| 4 | Dave | 2026-11-23 | Full keyboard flight to arrival played by hand. 58/58 tests pass. |
| 5 | Dave | 2026-11-23 | Realistic moon, Earth-to-flag progress track, auto-return to the moon, star speed matched to moon growth. Checked by hand. 87/87 tests pass. |
