from __future__ import print_function
from time import sleep
import glob

import numpy as np
import cv2

if __name__ == '__main__':

    img_names = glob.glob('superx/*.png')

    pattern_size = (5, 4)
    pattern_points = np.zeros((np.prod(pattern_size), 3), np.float32)
    pattern_points[:, :2] = np.indices(pattern_size).T.reshape(-1, 2)

    obj_points = []
    img_points = []
    h, w = 0, 0
    img_names_undistort = []
    for fn in img_names:
        print('processing %s... ' % fn, end='')
        img = cv2.imread(fn, 0)
        if img is None:
            print("Failed to load", fn)
            continue

        h, w = img.shape[:2]
        found, corners = cv2.findChessboardCorners(img, pattern_size)
        if found:
            term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.1)
            cv2.cornerSubPix(img, corners, (6, 7), (-1, -1), term)
            print('found1 ')

        vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.drawChessboardCorners(vis, pattern_size, corners, found)
        cv2.imshow('vis', vis)
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break
        sleep(.2)

        if not found:
            print('chessboard not found')
            continue

        img_points.append(corners.reshape(-1, 2))
        obj_points.append(pattern_points)

        print('ok')

    # calculate camera distortion
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, (w, h), None, None)
    np.savez("webcam_calibration_ouput.npz", ret=ret, mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs)

    print("\nRMS:", ret)
    print("camera matrix:\n", mtx)
    print("distortion coefficients: ", dist.ravel(), '\n')

    print('Camera.fx: {:.09}'.format(mtx[0][0]))
    print('Camera.fy: {:.09}'.format(mtx[1][1]))
    print('Camera.cx: {:.09}'.format(mtx[0][2]))
    print('Camera.cy: {:.09}'.format(mtx[1][2]))

    print('Camera.k1: {:.09}'.format(dist.ravel()[0]))
    print('Camera.k2: {:.09}'.format(dist.ravel()[1]))
    print('Camera.p1: {:.09}'.format(dist.ravel()[2]))
    print('Camera.p2: {:.09}'.format(dist.ravel()[3]))
    print('Camera.k3: {:.09}'.format(dist.ravel()[4]))

    cv2.destroyAllWindows()
