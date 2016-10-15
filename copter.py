import subprocess
from time import sleep
import numpy as np
import cv2
import display
from markers import Markers
from joystick_input import JoystickInput
from copter_controller import CopterController
from display import Display

class CopterVision():
    termination_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    pattern_size = (3, 3)
    pattern_points = np.zeros((np.prod(pattern_size), 3), np.float32)
    pattern_points[:, :2] = np.indices(pattern_size).T.reshape(-1, 2)
    axis = np.float32([[0,0,0], [0,3,0], [3,3,0], [3,0,0],
                       [0,0,-3],[0,3,-3],[3,3,-3],[3,0,-3] ])

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(15, -7)
        self.frames_to_display = {}
        self.display = Display()
        self.markers = Markers()
        self.controller = CopterController()
        self.markers_cache = None

    def onSettingsChange(self, arg):
        pass

    def draw_axis(self, img, corners, imgpts):
         corner = tuple(corners[0].ravel())
         img = cv2.line(img, corner, tuple(imgpts[0].ravel()), (255,0,0), 5)
         img = cv2.line(img, corner, tuple(imgpts[1].ravel()), (0,255,0), 5)
         img = cv2.line(img, corner, tuple(imgpts[2].ravel()), (0,0,255), 5)
         return img

    def draw_cube(self, img, corners, pts):
        pts = np.int32(pts).reshape(-1,2)

        # draw ground floor in green
        #img = cv2.drawContours(img, [pts[:4]],-1,(0,255,0),-3)

        # draw pillars in blue color
        for i,j in zip(range(4),range(4,8)):
            img = cv2.line(img, tuple(pts[i]), tuple(pts[j]),(255),3)

        # draw top layer in red color
        #img = cv2.drawContours(img, [pts[4:]],-1,(0,0,255),3)

        return img

    def start_orbslam(self):
        self.proc = subprocess.Popen(['D:\\orbslam\\ORB_SLAM2\\Examples\\Live'], stdout=subprocess.PIPE)

    def read_orbslam_pose(self):
        if self.proc is None:
            return
        line = self.proc.stdout.readline()
        if line != '':
            print line.rstrip()

    def process_frame(self, frame):
        if frame is None:
            print 'Null frame'
            return
        if len(frame.shape) < 2:
            raise ValueError('Invalid frame, shape < 2')
        elif len(frame.shape) > 2:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        self.frames_to_display['gray'] = gray

        markers = []

        markers = self.markers.detect(frame)

        # manage markers cache
        if markers:
            self.markers_cache = markers
        elif self.markers_cache:
            markers = self.markers_cache
            self.markers_cache = None
        else:
            return

        for marker in markers:
            src, marker_rotation, marker_name = marker

            skew = (src[0][1] - src[3][1] ) / ( src[1][1] - src[2][1]) - 1.0

            # Shoelace algorithm to find size (polygon area).
            relative_marker_camera_distance = np.sqrt(Markers.polygon_area(src))

            #Frame Center
            frame_center = tuple(np.divide(gray.shape, 2).astype(int))

            #Target
            target_midpoint = tuple(np.mean(src, axis=0).astype(int))
            target_camera_closeness = 60.0 #decrease for further away

            #Draw box around pattern
            cv2.drawMarker(frame, target_midpoint, (0, 0, 255), cv2.MARKER_CROSS)
            for i in range(len(src)-1):
                cv2.line(frame, tuple(src[i]), tuple(src[i+1]), (255, 0, 0), 2)
            cv2.line(frame, tuple(src[3]), tuple(src[0]), (255, 0, 0), 2)

            #Draw offset arrows
            cv2.arrowedLine(frame, frame_center, target_midpoint, (0,255,255))
            cv2.arrowedLine(frame, frame_center, (int(frame_center[0] + skew * 100.0), frame_center[1]), (0,255,255))
            #cv2.arrowedLine(frame, frame_center, (midpoint[0] - aileron, midpoint[1]), (0,255,255))
            #cv2.arrowedLine(frame, (midpoint[0], midpoint[1]), (midpoint[0] + pitch, midpoint[1] - pitch), (0,255,255))

            #Control copter
            vertical_dist = target_midpoint[1] - frame_center[1]
            side_dist = frame_center[0] - target_midpoint[0]
            forward_dist = target_camera_closeness - relative_marker_camera_distance
            yaw_dist = skew
            print '{:.02f} {:.02f} {:.02f} {:.02f}'.format(vertical_dist, side_dist, forward_dist, yaw_dist)
            self.controller.update(vertical_dist, side_dist, forward_dist, yaw_dist, self.display)

        self.frames_to_display['color'] = frame

    def display_frames(self, frame_dict):
        for key, value in frame_dict.iteritems():
            if value is not None:
                cv2.imshow(key, value)
        self.frames_to_display = {}
    def handle_keyboard_input(self):
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            self.cleanup()

    def capture_frame(self):
        ret, frame = self.cap.read()
        return frame

    def load_frame_from_file(self, filename):
        frame = cv2.imread(filename, 0)
        if frame is None:
            print("Failed to load", filename)
            self.cleanup()
        return frame

    def process_loop(self):
        #frame = self.load_frame_from_file('calibration_images\calibrate_1475552618.png')
        frame = self.capture_frame()
        self.process_frame(frame)
        self.display_frames(self.frames_to_display)
        self.handle_keyboard_input()

    def cleanup(self):
        self.cap.release()
        raise Exception('Complete')

if __name__ == '__main__':
    try:
        copter_vision = CopterVision()
        while(True):
            copter_vision.process_loop()
    except Exception as e:
        if e.message == 'Complete':
            pass
        else:
            raise
    finally:
        cv2.destroyAllWindows()

