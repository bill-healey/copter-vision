# Author: William Healey http://billhealey.com

import json
import subprocess

import numpy as np
import zmq


class OrbSlam:
    def __init__(self):
        self.connection_string = 'tcp://localhost:5555'
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

    def process(self):
        try:
            string = self.socket.recv(flags=zmq.NOBLOCK)
            topic, messagedata = string.split('|')
            # print("recv {} {}".format(topic, messagedata))
            jsonified_pose = messagedata.replace('[', '[[').replace(']', ']]').replace(';\n', '],[')
            pose_obj = json.loads(jsonified_pose)
            if len(pose_obj) != 4:
                return
            if self.original_pose is None:
                self.original_pose = np.array(pose_obj)
            cur_pose = np.matrix(pose_obj)

            # Compute Pose Translation Vector
            mTcw = cur_pose
            mRcw = mTcw.copy()[:3, :3]
            mRwc = np.transpose(mRcw.copy())
            mtcw = mTcw.copy()[:3, 3:]
            mOw = -np.transpose(mRcw.copy()) * mtcw

            print 'camera position: {:0.03f} {:0.03f} {:0.03f}'.format(
                mOw.item(0),
                mOw.item(1),
                mOw.item(2)
            )

        except zmq.Again:
            # print "No SLAM pose received"
            pass

    def cleanup(self):
        self.zmq_context.term()
