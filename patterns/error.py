from patterns.breathe import Breathe


class Error(Breathe):
    def __init__(self, period=2.0, gamma=2.2):
        # Use full red as base color
        super().__init__(base_color=(255, 0, 0), period=period, gamma=gamma)
