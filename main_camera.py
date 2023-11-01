# Import libraries
import glob
import os
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.pyplot import figure
import datetime
import cv2

from lc2fen.predict_board import detect_input_board
from utils import create_dir

from chessboard_recognition import chessboard_recognition
from chess_piece_recognition import chess_pieces_detector, chess_pieces_detector2

import pyrealsense2 as rs       # https://www.youtube.com/watch?v=CmDO-w56qso&ab_channel=NickDiFilippo


def main():

    # Connect camera
    pipe = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    pipe.start(cfg)

    # Save path of images and predictions
    images_path = f'images{os.sep}camera{os.sep}'
    save_path = f'predictions{os.sep}camera{os.sep}'
    create_dir(images_path)
    create_dir(save_path)

    # Process images
    while True:

        # Frame
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

        # Save image
        image_path = os.path.join(images_path, "color_image.png")

        # Chessboard recognition
        image = chessboard_recognition(image_path, save_path)
        print("Chessboard recognition DONE!")

        # Chess piece recognition
        detections, boxes = chess_pieces_detector(image)
        # chess_pieces_detector2(image_path)
        print("Chess pieces detected DONE!")

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