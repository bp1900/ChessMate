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

def interpolate(yx0, yx1):
    # x0, y0 = xy0
    # x1, y1 = xy1
    y0, x0 = yx0
    y1, x1 = yx1
    dx = (x1 - x0) / 8
    dy = (y1 - y0) / 8
    pts = [(x0 + i * dx, y0 + i * dy) for i in range(9)]
    return pts


def chessboard_recognition(image_path, save_path=None):

    # Image
    im = plt.imread(image_path)

    # Corners
    corners = detect_input_board(image_path)

    # Perspective transformation
    new_corners = np.float32([[0, 0], [512, 0], [512, 512], [0, 512]])
    # new_corners = np.float32([[512, 512], [0, 512], [0,0], [512, 0]])
    M = cv2.getPerspectiveTransform(np.float32(corners), new_corners)
    im = cv2.warpPerspective(im, M, (512, 512))
    image = np.copy(im)

    # Interpolate corners (obtain squares of chessboard)
    TL, TR, BR, BL = new_corners

    ptsT = interpolate(TL, TR)
    ptsL = interpolate(TL, BL)
    ptsR = interpolate(TR, BR)
    ptsB = interpolate(BL, BR)

    # Visualize prediction
    figure(figsize=(10, 10), dpi=80)
    implot = plt.imshow(image)

    for a, b in zip(ptsL, ptsR):
        plt.plot([a[0], b[0]], [a[1], b[1]], 'ro', linestyle="--")
        plt.xlim(0, 512)
        plt.ylim(0, 512)
    for a, b in zip(ptsT, ptsB):
        plt.plot([a[0], b[0]], [a[1], b[1]], 'ro', linestyle="--")
        plt.xlim(0, 512)
        plt.ylim(0, 512)

    plt.axis('off')

    if save_path is not None:
        save_file = os.path.join(save_path, image_path.split(os.sep)[-1])
        plt.savefig(save_file, bbox_inches='tight')

    return im