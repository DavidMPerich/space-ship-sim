"""Rocket state: speed, turning, heading and distance to the moon. Pure logic, no drawing."""

import math

import config


def _clamp(value, low, high):
    return max(low, min(high, value))


def _ease_fraction(rate, dt):
    """Share of the remaining gap to close in dt seconds (same feel at any frame rate)."""
    return 1.0 - math.exp(-rate * dt)


class Rocket:
    """Holding faster/slower moves the target speed, which stays put when the button is released."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Back to the start of a trip."""
        self.speed = config.START_SPEED
        self.target_speed = config.START_SPEED
        self.steer_offset = 0.0  # smoothed steering: -1 = full left, +1 = full right
        self.heading = 0.0       # radians turned from straight ahead, in -pi..pi; right is positive
        self.distance = config.TRIP_DISTANCE
        self.arrived = False

    @property
    def progress(self):
        """0 at launch, 1 at the moon."""
        return 1.0 - self.distance / config.TRIP_DISTANCE

    @property
    def turn_rate(self):
        """Radians per second, right is positive."""
        return self.steer_offset * config.TURN_RATE

    def update(self, controls, dt):
        """Advance by dt seconds using an InputState."""
        dt = _clamp(dt, 0.0, config.MAX_FRAME_TIME)
        self._update_steering(controls, dt)
        old_speed = self.speed
        self._update_speed(controls, dt)
        # The average of old and new speed keeps trips the same length at any frame rate.
        self._update_distance((old_speed + self.speed) / 2, dt)

    def _update_steering(self, controls, dt):
        target = _clamp(controls.steer, -1.0, 1.0)
        self.steer_offset += (target - self.steer_offset) * _ease_fraction(config.STEER_EASE_RATE, dt)
        self.heading = math.remainder(self.heading + self.turn_rate * dt, math.tau)  # never grows forever

    def _update_speed(self, controls, dt):
        throttle = int(controls.faster) - int(controls.slower)  # both held cancels out
        self.target_speed = _clamp(
            self.target_speed + throttle * config.THROTTLE_RATE * dt, config.MIN_SPEED, config.MAX_SPEED)
        change = (self.target_speed - self.speed) * _ease_fraction(config.SPEED_EASE_RATE, dt)
        limit = config.MAX_SPEED_CHANGE * dt
        self.speed = _clamp(self.speed + _clamp(change, -limit, limit), config.MIN_SPEED, config.MAX_SPEED)

    def _update_distance(self, speed, dt):
        self.distance = max(0.0, self.distance - speed * dt)
        if self.distance <= 0.0:
            self.arrived = True
