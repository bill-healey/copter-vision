import pygame

class JoystickInput:
    aileron = 0.0
    pitch = 0.0
    throttle = 0.0
    rudder = 0.0
    tside = 0.0
    hat_state = (0, 0)

    def __init__(self):
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        pygame.event.set_allowed([pygame.JOYHATMOTION, pygame.KEYDOWN])

    def update(self):

        self.aileron = self.joystick.get_axis(0)
        self.pitch = self.joystick.get_axis(1)
        self.throttle = -self.joystick.get_axis(2)
        self.rudder = self.joystick.get_axis(3)
        self.tside = self.joystick.get_axis(4)
        self.hat_state = self.joystick.get_hat(0)
        self.button_state = [self.joystick.get_button(b) for b in xrange(self.joystick.get_numbuttons())]

        if not pygame.event.peek():
            return

        pygame.event.pump()

        for event in pygame.event.get():
            if event.type == pygame.JOYHATMOTION:
                print event.value
                self.hat_state = event.value
            elif event.type == pygame.QUIT:
                raise Exception('Shutdown')
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise Exception('Shutdown')
            else:
                #print 'Unexpected event {} {}'.format(event.type, event)
                pass
