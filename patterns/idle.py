from patterns.pattern import Pattern
import math


class Idle(Pattern):
    def __init__(self, period=2.0, gamma=2.2):
        super().__init__()
        self.period = float(period) if period > 0 else 2.0
        self.gamma = float(gamma) if gamma > 0 else 1.0

    def at(self, pos):
        t = getattr(self, 'last_frame', 0)
        try:
            phase = (2.0 * math.pi * float(t)) / self.period
        except Exception:
            phase = 0.0

        raw = (math.sin(phase) + 1.0) / 2.0
        if self.gamma != 1.0:
            brightness = math.pow(raw, 1.0 / self.gamma)
        else:
            brightness = raw

        # Cache color for the current frame to avoid per-LED tuple allocations.
        if getattr(self, '_cached_frame', None) != self.last_frame:
            blue = int(max(0, min(255, round(255 * brightness))))
            self._cached_color = (0, 0, blue)
            self._cached_frame = self.last_frame
        return self._cached_color
