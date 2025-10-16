from patterns.pattern import Pattern

class Progress(Pattern):
    def __init__(self, unreached_color=(255, 255, 255), reached_color=(0, 255, 0)):
        super().__init__()
        self.num_leds = 64  # Default value; will be set by caller if needed
        self.unreached_color = unreached_color
        self.reached_color = reached_color
        self.progress = 0.0  # From 0.0 to 1.0
        self.progress_pos = 0.0
        self.all_same = False
        self.index = 0
        self.frac = 0

    def update(self, current_frame, progress=0.0):
        """Store the provided time/frame value for use by at().

        Patterns should call super().update(current_frame) to maintain
        consistent storage of the last_frame value.
        """
        try:
            self.last_frame = float(current_frame)
            self.progress = float(max(0.0, min(1.0, progress)))
            self.progress_pos = self.progress * self.num_leds
            self.index = int(self.progress_pos)
            self.frac = self.progress_pos - self.index
        except Exception:
            # If conversion fails, just keep the previous value
            pass

    def at(self, pos):
        if pos < self.index:
            # Fully reached
            return self.reached_color
        elif pos == self.index:
            # Partially faded in
            return tuple(
                int(self.unreached_color[i] + (self.reached_color[i] - self.unreached_color[i]) * self.frac)
                for i in range(3)
            )
        else:
            # Not reached yet
            return self.unreached_color

