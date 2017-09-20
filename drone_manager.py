# Author: William Healey http://billhealey.com

from time import sleep

import cv2

from copter_marker_vision import CopterMarkerVision
from display import Display
from drone_pids import DronePIDs
from joystick_input import JoystickInput
from orbslam import OrbSlam


class DroneManager:
    def __init__(self):
        self.pids = DronePIDs()
        self.orbslam = OrbSlam()
        self.display = Display()
        self.marker_vision = CopterMarkerVision()
        self.joystick = JoystickInput()

    def process_loop(self):
        # marker_telemetry = self.marker_vision.process()
        slam_telemetry = self.orbslam.process()
        self.handle_keyboard_input()
        self.display.rerender()
        self.joystick.update()
        self.pids.update(slam_telemetry)
        sleep(.05)

    def cleanup(self):
        self.pids.failsafe()
        self.marker_vision.cleanup()
        self.orbslam.cleanup()
        self.display.cleanup()

    @staticmethod
    def handle_keyboard_input():
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            raise Exception('Shutdown')


if __name__ == '__main__':
    drone_manager = None
    try:
        drone_manager = DroneManager()
        while True:
            drone_manager.process_loop()
    except Exception as e:
        if e.message == 'Shutdown':
            pass
        else:
            print e
            raise
    finally:
        if drone_manager:
            drone_manager.cleanup()
