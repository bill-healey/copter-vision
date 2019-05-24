# Author: William Healey http://billhealey.com

import json
import math
import subprocess

import numpy as np
import zmq


class OrbSlam:
    def __init__(self):
        self.connection_string = 'tcp://localhost:5556'
        self.orbslam_process = None
        self.original_pose = None
        self.zmq_context = zmq.Context()
        self.socket = self.zmq_context.socket(zmq.SUB)
        self.connect()

    def start_orbslam(self):
        self.orbslam_process = subprocess.Popen(['D:\\orbslam\\ORB_SLAM2\\Examples\\Live'], stdout=subprocess.PIPE)

    def read_orbslam_pose(self):
        if self.orbslam_process is None:
            return
        line = self.orbslam_process.stdout.readline()
        if line != '':
            print line.rstrip()

    def connect(self):
        print 'Attempting connection to ORBSLAM on {}'.format(self.connection_string)
        self.socket.connect(self.connection_string)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "pose".decode('ascii'))

    def process(self, previous_state):
        try:
            string = self.socket.recv(flags=zmq.NOBLOCK)
            topic, messagedata = string.split('|')
            # print("recv {} {}".format(topic, messagedata))
            jsonified_pose = messagedata.replace('[', '[[').replace(']', ']]').replace(';\n', '],[')
            pose_obj = json.loads(jsonified_pose)
            if len(pose_obj) != 4:
                return {'telemetry_lost': True}
            if self.original_pose is None:
                self.original_pose = np.array(pose_obj)
            pose = np.matrix(pose_obj)

            # Compute Pose Translation Vector
            rot = pose.copy()[:3, :3]  # Rotation matrix
            mtcw = pose.copy()[:3, 3:]
            translation = -np.transpose(rot.copy()) * mtcw

            roll = math.atan2(rot.item(1, 0), rot.item(0, 0))
            yaw = -math.atan2(-rot.item(2, 0), math.sqrt(rot.item(2, 1) ** 2 + rot.item(2, 2) ** 2))
            pitch = math.atan2(rot.item(2, 1), rot.item(2, 2))

            #print 'camera position: {:0.03f} {:0.03f} {:0.03f} rotation: {:0.03f} {:0.03f} {:0.03f}'.format(
            #    translation.item(0),
            #    translation.item(1),
            #    translation.item(2),
            #    yaw,
            #   pitch,
            #    roll
            #)

            return ({
                'telemetry_lost': False,
                'last_known_pose': {
                    'right_dist': translation.item(0)*1.0,
                    'forward_dist': translation.item(2)*1.0,
                    'vertical_dist': translation.item(1)*-1.0,
                    'yaw': yaw,
                    'pitch': pitch,
                    'roll': roll,
                },
                'pose_update': {
                    'right_dist': translation.item(0)*1.0,
                    'forward_dist': translation.item(2)*1.0,
                    'vertical_dist': translation.item(1)*-1.0,
                    'yaw': yaw,
                    'pitch': pitch,
                    'roll': roll,
                }
            })

        except zmq.Again:
            updated_state = previous_state.get('slam_telemetry', {'telemetry_lost': True})
            if 'pose_update' in updated_state:
                updated_state.pop('pose_update')
            return updated_state

    def cleanup(self):
        self.zmq_context.term()
