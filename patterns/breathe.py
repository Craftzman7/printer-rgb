"""Shared breathing pattern utilities and base class.

This module provides a Breathe pattern that other patterns can subclass to
gain a time-based sinusoidal breathing envelope with optional gamma
correction.
"""

from patterns.pattern import Pattern
import math


def compute_brightness_from_time(t, period=2.0, gamma=1.0):
    """Compute brightness in [0,1] for time t (seconds) using period and gamma.

    - period: seconds per full breathe cycle
    - gamma: gamma correction exponent (1.0 disables correction)
    """
    try:
        phase = (2.0 * math.pi * float(t)) / float(period)
    except Exception:
        phase = 0.0

    raw = (math.sin(phase) + 1.0) / 2.0
    if gamma != 1.0 and gamma > 0:
        return math.pow(raw, 1.0 / float(gamma))
    return raw


class Breathe(Pattern):
    """Generic breathe pattern.

    Subclasses or instances can set `base_color`, `period`, and `gamma`.
    """
    def __init__(self, base_color=(255, 255, 255), period=2.0, gamma=1.0):
        super().__init__()
        self.base_color = tuple(int(c) for c in base_color)
        self.period = float(period) if period > 0 else 2.0
        self.gamma = float(gamma) if gamma > 0 else 1.0

    def brightness(self):
        """Return current brightness in [0,1] using stored last_frame."""
        t = getattr(self, 'last_frame', 0.0)
        return compute_brightness_from_time(t, period=self.period, gamma=self.gamma)

    def at(self, pos):
        """Return an RGB tuple for position `pos` using base_color scaled by brightness."""
        b = self.brightness()
        r = int(max(0, min(255, round(self.base_color[0] * b))))
        g = int(max(0, min(255, round(self.base_color[1] * b))))
        bl = int(max(0, min(255, round(self.base_color[2] * b))))

        return (r, g, bl)
