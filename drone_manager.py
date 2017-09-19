from time import sleep
import cv2
from copter_marker_vision import CopterMarkerVision
from drone_pids import DronePIDs
from display import Display
from orbslam import OrbSlam
from joystick_input import JoystickInput

class DroneManager():

    def __init__(self):
        self.pids = DronePIDs()
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
        self.pids.failsafe()
        self.marker_vision.cleanup()
        self.orbslam.cleanup()
        self.display.cleanup()

if __name__ == '__main__':
    drone_manager = None
    try:
        drone_manager = DroneManager()
        while(True):
            drone_manager.process_loop()
    except Exception as e:
        if e.message == 'Shutdown':
            pass
        else:
            print e
            raise
    finally:
        drone_manager.cleanup()

