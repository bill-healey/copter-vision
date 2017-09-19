from collections import OrderedDict

import pygame


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args)
        return cls._instances[cls]


class Display:
    __metaclass__ = Singleton

    def __init__(self):
        (self.width, self.height) = (800, 600)
        pygame.init()
        pygame.display.set_caption('PID Controllers')
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.screen.fill((0, 0, 0))
        self.graphs = OrderedDict()
        self.line_colors = [
            (0, 255, 0),
            (0, 100, 255),
            (255, 0, 0),
            (0, 0, 255),
            (255, 255, 255),
            (200, 200, 0),
            (200, 0, 200)
        ]

    def add_point(self, graph_name, text, point_data, min_bound, max_bound):
        if len(point_data) < 2:
            raise ValueError('point_data must include time as dimension 0 as well as at least one other line')

        if graph_name not in self.graphs:
            self.graphs[graph_name] = {
                'name': graph_name,
                'text': text,
                'points': [],
                'min_bound': min_bound,
                'max_bound': max_bound
            }

        self.graphs[graph_name]['points'].append(point_data)
        self.graphs[graph_name]['text'] = text

        if len(self.graphs[graph_name]['points']) > self.width:
            self.graphs[graph_name]['points'].pop(0)

    @staticmethod
    def clamp(n, min_bound, max_bound):
        return min(max(n, min_bound), max_bound)

    def rerender(self):

        if len(self.graphs) == 0:
            return

        graph_height = 600 / len(self.graphs)

        self.screen.fill((0, 0, 0))

        for graph_id, (graph_name, graph) in enumerate(self.graphs.iteritems()):
            graph_top = graph_id * graph_height

            # Verify sufficient points
            if len(graph['points']) < 2:
                continue

            # Render text onto a separate surface, then blit to screen
            font = pygame.font.Font(None, 14)
            text = '{} {}'.format(graph['name'], graph['text'])
            text_surface = font.render(text, 1, (230, 230, 230))
            text_pos = text_surface.get_rect()
            text_pos.centerx = self.width / 2
            text_pos.top = graph_top
            self.screen.blit(text_surface, text_pos)

            for line_id in range(len(graph['points'][0])):
                scaled_line_points = [(i,
                                       graph_top + graph_height - (
                                           self.clamp(p[line_id], graph['min_bound'], graph['max_bound']) - graph[
                                               'min_bound']) * graph_height / (graph['max_bound'] - graph['min_bound']))
                                      for
                                      i, p in enumerate(graph['points'])]

                pygame.draw.lines(self.screen,
                                  self.line_colors[line_id],
                                  False,
                                  scaled_line_points,
                                  1)

        pygame.display.update()

    def cleanup(self):
        pygame.quit()
        self.graphs = None
