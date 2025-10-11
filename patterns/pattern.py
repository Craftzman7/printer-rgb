class Pattern:
    def __init__(self):
        self.last_frame = 0.0
        self.progress = 0.0  # For patterns that use print progress
        # Optional number of LEDs in the strip. Patterns can use this when
        # rendering progress-based effects. Set by caller (e.g. main.py).
        self.num_leds = None

    def at(self, pos):
        pass

    def update(self, current_frame, progress=0.0):
        """Store the provided time/frame value for use by at().

        Patterns should call super().update(current_frame) to maintain
        consistent storage of the last_frame value.
        """
        try:
            self.last_frame = float(current_frame)
            self.progress = float(max(0.0, min(1.0, progress)))
        except Exception:
            # If conversion fails, just keep the previous value
            pass
