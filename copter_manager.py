from time import sleep
import numpy as np
import cv2
from copter_marker_vision import CopterMarkerVision
from copter_controller import CopterController
from display import Display
from orbslam import OrbSlam
from joystick_input import JoystickInput

class CopterManager():

    def __init__(self):
        self.controller = CopterController()
        self.orbslam = OrbSlam()
        self.display = Display()
        self.marker_vision = CopterMarkerVision()
        self.joystick = JoystickInput()

    def process_loop(self):
        #marker_telemetry = self.marker_vision.process()
        slam_telemetry = self.orbslam.process()
        self.handle_keyboard_input()
        self.display.rerender()
        self.joystick.update()
        #self.controller.update(marker_telemetry)
        sleep(.5)

    def handle_keyboard_input(self):
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            raise Exception('Shutdown')

    def cleanup(self):
        self.controller.kill_throttle()
        self.marker_vision.cleanup()
        self.orbslam.cleanup()
        self.display.cleanup()

if __name__ == '__main__':
    copter_manager = None
    try:
        copter_manager = CopterManager()
        while(True):
            copter_manager.process_loop()
    except Exception as e:
        if e.message == 'Shutdown':
            pass
        else:
            print e
            raise
    finally:
        copter_manager.cleanup()

