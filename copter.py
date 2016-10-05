from time import sleep
import numpy as np
import cv2
import markers

class CopterVision():
    termination_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    pattern_size = (3, 3)
    pattern_points = np.zeros((np.prod(pattern_size), 3), np.float32)
    pattern_points[:, :2] = np.indices(pattern_size).T.reshape(-1, 2)
    axis = np.float32([[0,0,0], [0,3,0], [3,3,0], [3,0,0],
                       [0,0,-3],[0,3,-3],[3,3,-3],[3,0,-3] ])

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.frames_to_display = {}
        self.markers = markers.Markers()
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

        try:
            markers = self.markers.detect(frame)
        except Exception as ex:
            print(ex)

        # manage markers cache
        if markers:
            self.markers_cache = markers
        elif self.markers_cache:
            markers = self.markers_cache
            self.markers_cache = None
        else:
            return

        for marker in markers:
            src, skew, marker_rotation, marker_name = marker

            #Midpoint
            midpoint = np.mean(src, axis=0)
            print '{} {:0.02f}'.format(midpoint, skew)

            #Draw
            cv2.drawMarker(frame, tuple(midpoint), (0, 0, 255), cv2.MARKER_CROSS)
            for i in range(len(src)-1):
                cv2.line(frame, tuple(src[i]), tuple(src[i+1]), (255, 0, 0), 2)
            cv2.line(frame, tuple(src[3]), tuple(src[0]), (255, 0, 0), 2)

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

