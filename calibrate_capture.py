# Author: William Healey http://billhealey.com

import time

import cv2


# noinspection PyArgumentList
cap = cv2.VideoCapture(1)
cap.set(4, 704)  # Width
cap.set(5, 480)  # Height
cap.set(15, 0.1)  # Gain

while 1:
    try:
        ret, frame = cap.read()

        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        found_chessboard, corners = cv2.findChessboardCorners(gray, (5, 4), None)
        gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, (3, 3))

        # If found, add object points, image points (after refining them)
        if found_chessboard:
            filename = 'calibrate_{}.png'.format(int(time.time()))
            cv2.imwrite(filename, frame)
            print 'Captured {}\n'.format(filename)

        cv2.imshow('gray', gray)

        # Handle Keyboard input
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break
    except Exception as e:
        print e

cv2.destroyAllWindows()
cap.release()
