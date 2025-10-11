import sys
from patterns.finish import Finish
from patterns.paused import Paused
from patterns.prepare import Prepare
import time
try:
    import pygame # pyright: ignore[reportMissingImports]
except Exception as e:
    print("PyGame is required to run the simulator. Install with: pip install pygame")
    raise

from patterns.idle import Idle
from patterns.error import Error
from patterns.progress import Progress


class Simulator:
    def __init__(self, num_leds=64, led_size=12, spacing=4):
        pygame.init()
        self.num_leds = num_leds
        self.led_size = led_size
        self.spacing = spacing
        width = num_leds * (led_size + spacing) + spacing
        # Increase height to leave space for UI text below the strip
        height = led_size + 2 * spacing + 80
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption('Printer RGB Simulator')
        # Pre-create a font for consistent rendering and to avoid re-creating every frame
        try:
            self.font = pygame.font.SysFont('Arial', 16)
        except Exception:
            self.font = None

        # Patterns to cycle through
        self.patterns = [Idle(), Error(), Progress(), Finish(), Paused(), Prepare()]
        self.pattern_names = ['Idle', 'Error', 'Progress', 'Finish', 'Paused', 'Prepare']
        self.current = 0

        self.running = True
        self.paused = False
        self.time_scale = 1.0
        self.print_time = 60.0  # default print time in seconds
        self.brightness = 1.0
        self.start_time = time.time()
        try:
            self.clock = pygame.time.Clock()
        except Exception:
            self.clock = None

    def run(self):
        while self.running:
            self.handle_events()
            if not self.paused:
                now = (time.time() - self.start_time) * self.time_scale
            else:
                now = (self.pause_time - self.start_time) * self.time_scale

            progress = now / self.print_time
            # Throttle progress printing to avoid flooding the terminal.
            if self.clock is None or (self.clock.get_time() and self.clock.get_fps()):
                # If clock available, we'll cap FPS below. Still print a lightweight status once per second.
                pass

            pattern = self.patterns[self.current]
            pattern.update(now, progress)

            # Draw background
            self.screen.fill((10, 10, 10))

            for i in range(self.num_leds):
                color = pattern.at(i)
                color = (color[0] * self.brightness, color[1] * self.brightness, color[2] * self.brightness)
                x = self.spacing + i * (self.led_size + self.spacing)
                y = self.spacing
                pygame.draw.rect(self.screen, color, (x, y, self.led_size, self.led_size), border_radius=self.led_size//4)

            # Draw UI overlay below the strip
            ui_x = 8
            ui_y = self.led_size + 2 * self.spacing + 8
            self.draw_text(f'Pattern: {self.pattern_names[self.current]}', ui_x, ui_y)
            self.draw_text(f'Speed: {self.time_scale:.2f}x', ui_x, ui_y + 20)
            self.draw_text('Space: pause | Left/Right: speed | Up/Down: change pattern', ui_x, ui_y + 40)

            pygame.display.flip()
            # Cap the frame rate to 10 FPS to keep CPU usage low during simulation.
            if self.clock:
                self.clock.tick(10)

    def draw_text(self, text, x, y, size=14, color=(200, 200, 200)):
        if self.font is not None and self.font.get_height() == size:
            font = self.font
        else:
            try:
                font = pygame.font.SysFont('Arial', size)
            except Exception:
                font = None

        if font is not None:
            surf = font.render(text, True, color)
            self.screen.blit(surf, (x, y))
        else:
            # fallback: no font available
            pass

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    if not self.paused:
                        self.paused = True
                        self.pause_time = time.time()
                    else:
                        # resume; adjust start_time so animation continues from same point
                        paused_duration = time.time() - self.pause_time
                        self.start_time += paused_duration
                        self.paused = False
                elif event.key == pygame.K_LEFT:
                    self.time_scale = max(0.1, self.time_scale - 0.1)
                elif event.key == pygame.K_RIGHT:
                    self.time_scale = min(5.0, self.time_scale + 0.1)
                elif event.key == pygame.K_UP:
                    self.current = (self.current + 1) % len(self.patterns)
                elif event.key == pygame.K_DOWN:
                    self.current = (self.current - 1) % len(self.patterns)


def main():
    sim = Simulator(num_leds=64)
    sim.run()
    pygame.quit()


if __name__ == '__main__':
    main()
