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
        (self.width, self.height) = (1280, 1024)
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
        if len(point_data) < 1:
            raise ValueError('point_data must include at least one line')

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

    def rerender(self, state):

        self.screen.fill((0, 0, 0))

        if state['slam_telemetry']['telemetry_lost']:
            font = pygame.font.Font(None, 36)
            text_surface = font.render('***TELEMETRY LOST***', 1, (240, 100, 100))
            text_pos = text_surface.get_rect()
            text_pos.centerx = self.width / 2
            text_pos.top = 36
            self.screen.blit(text_surface, text_pos)

        if len(self.graphs) > 0:

            graph_height = self.height / len(self.graphs)

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

    def get_keyboard_events(self):
        retval = []
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                self.cleanup()
            if event.type==pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise Exception('Shutdown')
                if event.key == pygame.K_SPACE:
                    retval.append('tune_yaw')
                if event.key == pygame.K_s:
                    retval.append('hold_current_position')
                if event.key == pygame.K_UP:
                    retval.append('translate_forward')
                if event.key == pygame.K_DOWN:
                    retval.append('translate_backward')
                if event.key == pygame.K_LEFT:
                    retval.append('yaw_left')
                if event.key == pygame.K_RIGHT:
                    retval.append('yaw_right')
                if event.key == pygame.K_KP8:
                    retval.append('translate_up')
                if event.key == pygame.K_KP5:
                    retval.append('translate_down')
                if event.key == pygame.K_KP4:
                    retval.append('translate_left')
                if event.key == pygame.K_KP6:
                    retval.append('translate_right')

        return retval

    def cleanup(self):
        pygame.quit()
        self.graphs = None
