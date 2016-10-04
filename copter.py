import numpy as np
import cv2

class CopterVision():
    termination_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    color_grid = np.zeros((6*7, 3), np.float32)
    color_grid[:,:2] = np.mgrid[0:7, 0:6].T.reshape(-1,2)
    axis = np.float32([[0,0,0], [0,3,0], [3,3,0], [3,0,0],
                       [0,0,-3],[0,3,-3],[3,3,-3],[3,0,-3] ])

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        frames_to_display = {}

    def onSettingsChange(self, arg):
        pass

    def draw_cube(self, img, corners, pts):
        pts = np.int32(pts).reshape(-1,2)

        # draw ground floor in green
        img = cv2.drawContours(img, [pts[:4]],-1,(0,255,0),-3)

        # draw pillars in blue color
        for i,j in zip(range(4),range(4,8)):
            img = cv2.line(img, tuple(pts[i]), tuple(pts[j]),(255),3)

        # draw top layer in red color
        img = cv2.drawContours(img, [pts[4:]],-1,(0,0,255),3)

        return img

    def process_frame(self, frame):
        if len(frame.shape) < 2:
            raise ValueError('Invalid frame, shape < 2')
        elif len(frame.shape) > 2:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Find the chess board corners
        found_chessboard, corners = cv2.findChessboardCorners(gray, (7,6), None)

        # If found, add object points, image points (after refining them)
        if found_chessboard == True:
            obj_points = []
            img_points = []
            obj_points.append(self.color_grid)

            corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1), self.termination_criteria)
            img_points.append(corners2)

            # Draw and display the corners
            frame = cv2.drawChessboardCorners(frame, (7,6), corners2, found_chessboard)

            # Calibration
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray.shape[::-1],None,None)

            # Find the rotation and translation vectors.
            rvecs, tvecs, inliers = cv2.solvePnPRansac(obj_points, corners2, mtx, dist)

            # project 3D points to image plane
            imgpts, jac = cv2.projectPoints(self.axis, rvecs, tvecs, mtx, dist)

            gray = self.draw_cube(gray, corners2, imgpts)

    def display_frames(self, frame_dict):
        for key, value in frame_dict.iteritems():
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
        frame = self.load_frame_from_file('calibration_images\calibrate_1475552618.png')
        #frame = self.capture_frame()
        self.process_frame(frame)
        self.display_frames(self.frames_to_display)
        self.handle_keyboard_input()
        self.cleanup()

    def cleanup(self):
        self.cap.release()
        raise 'Complete'

if __name__ == '__main__':
    try:
        copter_vision = CopterVision()
        while(True):
            copter_vision.process_loop()
    finally:
        cv2.destroyAllWindows()


