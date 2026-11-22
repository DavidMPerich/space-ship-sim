"""Run every test headless: no real window or sound device needed."""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

# Make the project root importable (config, main, game/...).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
