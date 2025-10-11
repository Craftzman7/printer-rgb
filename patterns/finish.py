from patterns.breathe import Breathe


class Finish(Breathe):
    def __init__(self, period=2.0, gamma=2.2):
        # Use full green as base color
        super().__init__(base_color=(0, 255, 0), period=period, gamma=gamma)
