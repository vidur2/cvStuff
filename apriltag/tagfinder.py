# MIT License
# Copyright (c) 2019-2022 JetsonHacks

# Using a CSI camera (such as the Raspberry Pi Version 2) connected to a
# NVIDIA Jetson Nano Developer Kit using OpenCV
# Drivers for the camera and OpenCV are included in the base image

import cv2
from pupil_apriltags import Detector

""" 
gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
Flip the image by setting the flip_method (most common values: 0 and 2)
display_width and display_height determine the size of each camera pane in the window on the screen
Default 1920x1080 displayd in a 1/4 size window
"""

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


def show_camera():
    window_title = "CSI Camera"
    at_detector = Detector(
        families="tag36h11",
        nthreads=3,
        quad_decimate=4.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
    )
    # To flip the image, modify the flip_method parameter (0 and 2 are the most common)
    print(gstreamer_pipeline(flip_method=0))
    video_capture = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    if video_capture.isOpened():
        try:
            counter = 0
            prev_cx = 0
            prev_cy = 0
            cx_current = 0
            cy_current = 0
            window_handle = cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
            while True:
                counter += 1
                ret_val, frame = video_capture.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                results = at_detector.detect(gray)
                for r in results:
	        # extract the bounding box (x, y)-coordinates for the AprilTag
                # and convert each of the (x, y)-coordinate pairs to integers
                    (ptA, ptB, ptC, ptD) = r.corners
                    ptB = (int(ptB[0]), int(ptB[1]))
                    ptC = (int(ptC[0]), int(ptC[1]))
                    ptD =  (int(ptD[0]), int(ptD[1]))
                    ptA = (int(ptA[0]), int(ptA[1]))
                    # draw the bounding box of the AprilTag detection
                    cv2.line(frame, ptA, ptB, (0, 255, 0), 2)
                    cv2.line(frame, ptB, ptC, (0, 255, 0), 2)
                    cv2.line(frame, ptC, ptD, (0, 255, 0), 2)
                    cv2.line(frame, ptD, ptA, (0, 255, 0), 2)
                    # draw the center (x, y)-coordinates of the AprilTag
                    (cX, cY) = (int(r.center[0]), int(r.center[1]))
                    cx_current = cX
                    cy_current = cY
                    cv2.line(frame, (prev_cx, prev_cy), (cx_current, cy_current), (255,0,0), 2)
                    print(counter)
                    if counter >= 15:
                        prev_cx = cx_current
                        prev_cy = cy_current
                        counter = 0
                    cv2.circle(frame, (cX, cY), 5, (0, 0, 255), -1)
                    # draw the tag family on the image
                    tagID = str(r.tag_id)
                    #print("X:",cX," Y:",cY)
                    cv2.putText(frame, tagID, (ptA[0], ptA[1] - 15),
	                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    #print("[INFO] tag family: {}".format(tagFamily))
                # Check to see if the user closed the window
                # Under GTK+ (Jetson Default), WND_PROP_VISIBLE does not work correctly. Under Qt it does
                # GTK - Substitute WND_PROP_AUTOSIZE to detect if window has been closed by user
                if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                    cv2.imshow(window_title, frame)
                else:
                    break 
                keyCode = cv2.waitKey(10) & 0xFF
                # Stop the program on the ESC key or 'q'
                if keyCode == 27 or keyCode == ord('q'):
                    break
        finally:
            video_capture.release()
            cv2.destroyAllWindows()
    else:
        print("Error: Unable to open camera")


if __name__ == "__main__":
    show_camera()
