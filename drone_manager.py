# Author: William Healey http://billhealey.com

import traceback
import cv2

from time import sleep
from copter_marker_vision import CopterMarkerVision
from display import Display
from drone_pids import DronePIDs
from drone_rc_controller import DroneRCController
from orbslam import OrbSlam
import numpy as np
import pickle
from joystick_input import JoystickInput


class DroneManager:
    def __init__(self):
        self.pids = DronePIDs()
        self.orbslam = OrbSlam()
        self.display = Display()
        self.marker_vision = CopterMarkerVision()
        self.drone_rc_controller = DroneRCController()
        self.shared_state = {}
        #self.joystick = JoystickInput()

    def update_drone_position_from_user_input(self, shared_state):
        translate_step = 0.01
        yaw_step = 0.10
        translate_step_vector = np.array([[0],[0],[0]],dtype=np.float64)

        if 'tune_yaw' in shared_state.get('user_input'):
            self.pids.pids['yaw'].begin_tuning()

        # Handle Translation
        if 'translate_forward' in shared_state.get('user_input'):
            # Forward is in the +Z direction, relative to the drone
            translate_step_vector += np.array([[0],[0],[1]],dtype=np.float64) * translate_step
        if 'translate_backward' in shared_state.get('user_input'):
            # Backward is in the -Z direction, relative to the drone
            translate_step_vector += np.array([[0],[0],[-1]],dtype=np.float64) * translate_step
        if 'translate_down' in shared_state.get('user_input'):
            # Down is in the +Y direction, relative to the drone
            translate_step_vector += np.array([[0],[1],[0]],dtype=np.float64) * translate_step
        if 'translate_up' in shared_state.get('user_input'):
            # Up is in the -Y direction, relative to the drone
            translate_step_vector += np.array([[0],[-1],[0]],dtype=np.float64) * translate_step
        if 'translate_left' in shared_state.get('user_input'):
            # Left is in the -X direction, relative to the drone
            translate_step_vector += np.array([[-1],[0],[0]],dtype=np.float64) * translate_step
        if 'translate_right' in shared_state.get('user_input'):
            # Right is in the +X direction, relative to the drone
            translate_step_vector += np.array([[1],[0],[0]],dtype=np.float64) * translate_step

        # Rotate translate_step_vector into world coordinates, then apply
        world_step_vector = np.matmul(np.transpose(self.orbslam.world_to_drone_rotation_matrix), translate_step_vector)
        self.orbslam.desired_position_translation_matrix += world_step_vector

        if 'yaw_left' in shared_state.get('user_input'):
            self.orbslam.desired_yaw -= yaw_step
        if 'yaw_right' in shared_state.get('user_input'):
            self.orbslam.desired_yaw -= yaw_step


    def process_loop(self):
        # Scan keyboard
        self.shared_state['cv_keyboard'] = self.handle_opencv_keyboard_input() # Unreliable, should remove
        self.shared_state['user_input'] = self.display.get_keyboard_events()

        # Get Telemetry
        # self.shared_state['marker_telemetry'] = self.marker_vision.process()
        self.shared_state['slam_telemetry'] = self.orbslam.process(self.shared_state)

        self.update_drone_position_from_user_input(self.shared_state)

        # Only update PIDs if new telemetry pose data is available.
        # Telemetry via ORBSLAM is sent at consistent intervals.
        #  (if that is not the case, this needs to be changed so PIDs are still updated regularly)
        if self.shared_state['slam_telemetry'].get('pose_update'):
            self.shared_state['pid_output'] = self.pids.update(self.shared_state['slam_telemetry']['pose_update'])
            self.drone_rc_controller.update_channels(
                self.shared_state['pid_output']['aileron'],
                self.shared_state['pid_output']['pitch'],
                self.shared_state['pid_output']['throttle'],
                self.shared_state['pid_output']['yaw'],
            )

        # Interrupt output stream whenever telemetry is lost
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
