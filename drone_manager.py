# Author: William Healey http://billhealey.com

import traceback
from time import sleep

import cv2

from copter_marker_vision import CopterMarkerVision
from display import Display
from drone_pids import DronePIDs
from drone_rc_controller import DroneRCController
from joystick_input import JoystickInput
from orbslam import OrbSlam


class DroneManager:
    def __init__(self):
        self.pids = DronePIDs()
        self.orbslam = OrbSlam()
        self.display = Display()
        self.marker_vision = CopterMarkerVision()
        self.drone_rc_controller = DroneRCController()
        self.shared_state = {}
        #self.joystick = JoystickInput()

    def process_loop(self):
        # Get Telemetry
        # self.shared_state['marker_telemetry'] = self.marker_vision.process()
        self.shared_state['slam_telemetry'] = self.orbslam.process(self.shared_state)

        # Scan keyboard
        self.shared_state['cv_keyboard'] = self.handle_opencv_keyboard_input()
        self.shared_state['pygame_keyboard'] = self.display.get_keyboard_events()

        # Tune yaw on spacebar
        if 'space' in self.shared_state.get('pygame_keyboard'):
            self.pids.pids['yaw'].begin_tuning()

        # Lock in setpoints on 'S' key
        if 's' in self.shared_state.get('pygame_keyboard') and 'last_known_pose' in self.shared_state['slam_telemetry']:
            self.pids.hold_current_position(self.shared_state['slam_telemetry']['last_known_pose'])

        # Only update PIDs if new telemetry pose data is available
        if self.shared_state['slam_telemetry'].get('pose_update'):
            self.shared_state['pid_output'] = self.pids.update(self.shared_state['slam_telemetry']['pose_update'])
            self.drone_rc_controller.update_channels(
                self.shared_state['pid_output']['aileron'],
                self.shared_state['pid_output']['pitch'],
                self.shared_state['pid_output']['throttle'],
                self.shared_state['pid_output']['yaw'],
            )

        # Kill throttle if telemetry is lost
        if self.shared_state['slam_telemetry'].get('telemetry_lost'):
            self.drone_rc_controller.pause_stream()
        self.display.rerender(self.shared_state)
        sleep(.05)

    def cleanup(self):
        self.drone_rc_controller.kill_throttle()
        self.drone_rc_controller.pause_stream()
        self.marker_vision.cleanup()
        self.orbslam.cleanup()
        self.display.cleanup()

    @staticmethod
    def handle_opencv_keyboard_input():
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
            traceback.print_exc()
            raise
    finally:
        if drone_manager:
            drone_manager.cleanup()
