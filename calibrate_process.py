#!/usr/bin/env python

# Python 2/3 compatibility
from __future__ import print_function
from time import sleep

import numpy as np
import cv2
import glob
import os

if __name__ == '__main__':

    img_names = glob.glob('calibration_images/*.png')

    pattern_size = (6, 7)
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
    print("distortion coefficients: ", dist.ravel())

    cv2.destroyAllWindows()
