import cv2
import time


cap = cv2.VideoCapture(0)


while(1):

    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

     # Find the chess board corners
    found_chessboard, corners = cv2.findChessboardCorners(gray, (7,6), None)

    # If found, add object points, image points (after refining them)
    if found_chessboard == True:
        filename = 'calibrate_{}.png'.format(int(time.time()))
        cv2.imwrite(filename, frame)
        print 'Captured {}\n'.format(filename)

    cv2.imshow('frame', frame)

    # Handle Keyboard input

    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break


cv2.destroyAllWindows()
cap.release()
