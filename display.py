import pygame

class Display:

    def __init__(self):
        (self.width, self.height) = (800, 600)
        pygame.init()
        pygame.display.set_caption('PID Controllers')
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.screen.fill((0, 0, 0))

    def clamp(self, n, min_bound, max_bound):
        return min(max(n, min_bound), max_bound)

    def graph_data(self, points, min_bound, max_bound, text):

        if len(points) <= 1:
            return

        # Display the text
        font = pygame.font.Font(None, 14)
        text_element = font.render(text, 1, (230, 230, 230))
        text_pos = text_element.get_rect()
        text_pos.centerx = self.width / 2


        # Display the most recent points
        scaled_points = points
        if len(scaled_points) > self.width:
            scaled_points = scaled_points[-self.width:]

        scaled_line_1 = [ (i, self.height - (self.clamp(p[1], min_bound, max_bound) - min_bound) * self.height / (max_bound - min_bound)) for i, p in enumerate(scaled_points)]
        scaled_line_2 = [ (i, self.height - (self.clamp(p[2], min_bound, max_bound) - min_bound) * self.height / (max_bound - min_bound)) for i, p in enumerate(scaled_points)]

        self.screen.fill((0, 0, 0))

        self.screen.blit(text_element, text_pos)

        pygame.draw.lines(self.screen,
                          (0, 255, 0),
                          False,
                          scaled_line_1,
                          1)

        pygame.draw.lines(self.screen,
                          (0, 100, 255),
                          False,
                          scaled_line_2,
                          1)

        pygame.display.update()
