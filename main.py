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
from chess_piece_recognition import chess_pieces_detector2

import pyrealsense2 as rs       # https://www.youtube.com/watch?v=CmDO-w56qso&ab_channel=NickDiFilippo


def main():

    # Images path
    # folder_path = f'data{os.sep}boards{os.sep}input{os.sep}'
    folder_path = f'data{os.sep}boards_pieces{os.sep}'
    board_path = glob.glob(f"{folder_path}chessboard*.jpg")
    save_path = f'predictions{os.sep}boards_pieces{os.sep}BoardDetection{os.sep}'
    create_dir(save_path)

    # folder_path = f'predictions{os.sep}TestImages{os.sep}BoardDetection{os.sep}'
    # board_path = glob.glob(f"{folder_path}cc*.jpg")

    # Detect chessboard for each image
    for image_path in board_path:
        print(image_path)

        # Chessboard recognition
        image = chessboard_recognition(image_path, save_path)
        print("Chessboard recognition DONE!")

        # Chess piece recognition
        # detections, boxes = chess_pieces_detector(image)
        chess_pieces_detector2(image_path)
        print("Chess pieces detected DONE!")


if __name__ == "__main__":
    main()