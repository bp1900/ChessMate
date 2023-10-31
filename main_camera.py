# Import libraries
import glob
import os
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.pyplot import figure
import datetime
import cv2

from lc2fen.predict_board import detect_input_board

import pyrealsense2 as rs       # https://www.youtube.com/watch?v=CmDO-w56qso&ab_channel=NickDiFilippo


def interpolate(xy0, xy1):
    x0, y0 = xy0
    x1, y1 = xy1
    dx = (x1 - x0) / 8
    dy = (y1 - y0) / 8
    pts = [(x0 + i * dx, y0 + i * dy) for i in range(9)]
    return pts


def detect_chess_pieces():
    model_trained = YOLO("best_transformed_detection.pt")
    results = model_trained.predict(source=image, line_thickness=1, conf=0.5, augment=False, save_txt=True, save=True)

    boxes = results[0].boxes
    detections = boxes.xyxy.numpy()

def main():
    pipe = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    pipe.start(cfg)

    while True:
        frame = pipe.wait_for_frames()
        depth_frame = frame.get_depth_frame()
        color_frame = frame.get_color_frame()

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        cv2.imshow('rgb', color_image)
        cv2.imshow('depth', depth_image)

        key = cv2.waitKey(1)

        if key == 13:  # Check for ENTER key
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            cv2.imwrite(f'color_image_{timestamp}.png', color_image)
            cv2.imwrite(f'depth_image_{timestamp}.png', depth_image)

        elif key == ord('q'):
            break

    detect_chess_pieces()

    pipe.stop()
    cv2.destroyAllWindows()

    # folder_path = f'data{os.sep}boards{os.sep}input{os.sep}'
    # board_path = glob.glob(f"{folder_path}chessboard*.jpg")
    #
    # # folder_path = f'predictions{os.sep}TestImages{os.sep}BoardDetection{os.sep}'
    # # board_path = glob.glob(f"{folder_path}cc*.jpg")
    #
    # for image in board_path[:1]:
    #     corners = detect_input_board(image)
    #
    #     figure(figsize=(10, 10), dpi=80)
    #
    #     im = plt.imread(image)
    #     implot = plt.imshow(im)
    #
    #     TL = corners[0]
    #     BL = corners[3]
    #     TR = corners[1]
    #     BR = corners[2]
    #
    #     ptsT = interpolate(TL, TR)
    #     ptsL = interpolate(TL, BL)
    #     ptsR = interpolate(TR, BR)
    #     ptsB = interpolate(BL, BR)
    #
    #     for a, b in zip(ptsL, ptsR):
    #         plt.plot([a[0], b[0]], [a[1], b[1]], 'ro', linestyle="--")
    #     for a, b in zip(ptsT, ptsB):
    #         plt.plot([a[0], b[0]], [a[1], b[1]], 'ro', linestyle="--")
    #
    #     plt.axis('off')
    #
    #     plt.savefig('chessboard_transformed_with_grid.jpg')



if __name__ == "__main__":
    main()