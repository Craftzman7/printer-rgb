from patterns.pattern import Pattern


class Paused(Pattern):
    def __init__(self, unreached_color=(255, 255, 255), reached_color=(255, 165, 0)):
        super().__init__()
        self.num_leds = 64  # Default value; will be set by caller if needed
        self.unreached_color = unreached_color
        self.reached_color = reached_color

    def at(self, pos):
        if pos < (self.progress * self.num_leds):
            return self.reached_color
        else:
            return self.unreached_color
