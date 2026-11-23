"""Entry point: set up pygame, run the game loop, quit cleanly."""

import argparse
import math
import sys

import pygame

import config
from game.input import InputHandler
from game.rocket import Rocket
from game.starfield import Starfield


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Rocket to the Moon")
    parser.add_argument("--windowed", action="store_true", help="run in a window instead of fullscreen")
    parser.add_argument("--frames", type=int, default=0, help="quit after N frames (0 = run forever; for testing)")
    parser.add_argument("--debug", action="store_true", help="show live input and rocket values")
    return parser.parse_args(argv)


def debug_lines(state, fps):
    """Text shown by the --debug overlay."""
    return [
        f"FPS: {fps:.0f}",
        f"steer: {state.steer:+.1f}",
        f"faster: {'YES' if state.faster else 'no'}",
        f"slower: {'YES' if state.slower else 'no'}",
        f"start: {'PRESSED' if state.start_pressed else '-'}",
    ]


def rocket_lines(rocket):
    """Rocket values for the --debug overlay."""
    return [
        f"speed: {rocket.speed:.1f} (target {rocket.target_speed:.1f})",
        f"steer offset: {rocket.steer_offset:+.2f}",
        f"heading: {math.degrees(rocket.heading):+.0f} deg",
        f"distance: {rocket.distance:.1f} ({rocket.progress:.0%} there)",
        f"arrived: {'YES' if rocket.arrived else 'no'}",
    ]


def draw_debug(screen, font, lines):
    y = 10
    for line in lines:
        screen.blit(font.render(line, True, config.DEBUG_TEXT_COLOR), (10, y))
        y += font.get_linesize()


def create_screen(windowed):
    flags = 0 if windowed else pygame.FULLSCREEN
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
    pygame.display.set_caption(config.WINDOW_TITLE)
    return screen


def is_quit_event(event):
    """True for window close or Esc. Esc is a dev-only exit; kid mode replaces it in Step 9."""
    if event.type == pygame.QUIT:
        return True
    return event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE


def run(argv=None):
    """Run the game. Returns an exit code."""
    args = parse_args(argv)
    pygame.init()
    try:
        screen = create_screen(args.windowed)
        clock = pygame.time.Clock()
        controls = InputHandler()
        rocket = Rocket()
        stars = Starfield()
        font = pygame.font.Font(None, 36) if args.debug else None
        frame = 0
        running = True
        while running:
            dt = clock.tick(config.FPS) / 1000  # seconds
            controls.begin_frame()
            for event in pygame.event.get():
                if is_quit_event(event):
                    running = False
                controls.handle_event(event)
            state = controls.state()
            rocket.update(state, dt)
            stars.update(rocket.speed, dt, rocket.turn_rate)

            screen.fill(config.BACKGROUND_COLOR)
            stars.draw(screen)
            if font:
                draw_debug(screen, font, debug_lines(state, clock.get_fps()) + rocket_lines(rocket))
            pygame.display.flip()

            frame += 1
            if args.frames and frame >= args.frames:
                running = False
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(run())
