from time import sleep
import numpy as np
import cv2
from markers import Markers
from display import Display

class CopterMarkerVision():
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
        self.markers_cache = None

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
        #ret,thresh1 = cv2.threshold(frame,200,255,cv2.THRESH_BINARY)

        eroded = cv2.erode(gray, np.ones((5,5), np.uint8))

        markers = self.markers.detect(eroded)
        self.frames_to_display['gray'] = eroded

        # manage markers cache
        if markers:
            self.markers_cache = markers
        elif self.markers_cache:
            markers = self.markers_cache
            self.markers_cache = None
        else:
            return

        telemetry = {}

        for marker in markers:
            src, marker_rotation, marker_name = marker

            skew = (src[0][1] - src[3][1] ) / ( src[1][1] - src[2][1]) - 1.0

            # Shoelace algorithm to find size (polygon area).
            relative_marker_camera_distance = np.sqrt(Markers.polygon_area(src))

            #Frame Center
            frame_height, frame_width = tuple(np.divide(gray.shape, 2).astype(int))
            frame_center = (frame_width, frame_height)

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

            #Control copter
            telemetry = {
                'vertical_dist': float(target_midpoint[1]) / float(frame_center[1]) - 1.0,
                'side_dist': float(target_midpoint[0])  / float(frame_center[0]) - 1.0,
                'forward_dist': float(target_camera_closeness) / float(relative_marker_camera_distance) - 1.0,
                'yaw_dist': skew
            }
            #print '{:.02f} {:.02f} {:.02f} {:.02f}'.format(vertical_dist, side_dist, forward_dist, yaw_dist)
            break

        self.frames_to_display['color'] = frame

        return telemetry


    def display_frames(self, frame_dict):
        for key, value in frame_dict.iteritems():
            if value is not None:
                cv2.imshow(key, value)
        self.frames_to_display = {}

    def capture_frame(self):
        ret, frame = self.cap.read()
        return frame

    def load_frame_from_file(self, filename):
        frame = cv2.imread(filename, 0)
        if frame is None:
            print("Failed to load", filename)
            self.cleanup()
        return frame

    def process(self):
        frame = self.capture_frame()
        self.process_frame(frame)
        self.display_frames(self.frames_to_display)

    def cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()

