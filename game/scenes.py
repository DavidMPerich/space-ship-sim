"""Game scenes. Step 4 has only the flight; the countdown, arrival and restart come in Step 6."""

import config
from game.moon import Moon, ProgressIndicator
from game.rocket import Rocket
from game.starfield import Starfield


class Flight:
    """Flying to the moon: controls drive the rocket, and the rocket drives the starfield."""

    def __init__(self):
        self.rocket = Rocket()
        self.stars = Starfield()
        self.moon = Moon()
        self.indicator = ProgressIndicator()
        self.announced = False

    def update(self, controls, dt):
        self.rocket.update(controls, dt)
        self.stars.update(self.rocket.speed, dt, self.rocket.turn_rate)
        if self.rocket.arrived and not self.announced:
            self.announced = True
            print("You made it to the Moon!", flush=True)  # placeholder until the Step 6 celebration

    def draw(self, screen):
        screen.fill(config.BACKGROUND_COLOR)
        self.stars.draw(screen)
        self.moon.draw(screen, self.rocket.progress, self.rocket.heading)
        self.indicator.draw(screen, self.rocket.progress)
