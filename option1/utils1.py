from ultralytics import YOLO

from matplotlib.pyplot import figure
import matplotlib.image as image
from matplotlib import pyplot as plt

import pandas as pd
import numpy as np
from numpy import asarray
from PIL import Image

import cv2

from shapely.geometry import Polygon

"""
    Detect chessboard corners
"""
def detect_corners(image):
    # YOLO model trained to detect corners on a chessboard
    model_trained = YOLO("best_corners.pt")
    results = model_trained.predict(source=image, line_thickness=1, conf=0.25, save_txt=True, save=True)

    print(f'Results: {results}')
    # get the corners coordinates from the model
    boxes = results[0].boxes
    print(f'Boxes: {boxes}')
    arr = boxes.xywh.numpy()
    print(f'Array of boxes: {arr}')
    points = arr[:, 0:2]
    print(f'Points: {points}')

    corners = order_points(points)
    print(f'Corners: {corners}')

    return corners

""" 
    Rearrange the corners in a fixed order.
    This function applies simple logic to this problem.
    The top-left point will have the smallest sum between x and y, whereas the bottom-right point will have the largest sum. 
    The top-right point will have the smallest difference, whereas the bottom-left will have the largest difference. 
"""
def order_points(pts):
    # order a list of 4 coordinates:
    # 0: top-left,
    # 1: top-right
    # 2: bottom-right,
    # 3: bottom-left

    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

"""
    Compute the perspective transform matrix using OpenCV2
"""
# perspective transforms an image with four given corners

def four_point_transform(image, pts):
    img = Image.open(image)
    image = asarray(img)
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # compute the width of the new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # compute the height of the new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # construct set of destination points to obtain a "birds eye view"
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    img = Image.fromarray(warped, "RGB")
    img.show()
    # return the warped image
    return img

"""
    Calculate the coordinates of all the squares on the board by dividing the upper edge of the image by 8, and then the 
    same for the left edge, and then connecting all the points into lines
"""
# calculates chessboard grid
def interpolate(xy0, xy1):
    x0, y0 = xy0
    x1, y1 = xy1
    dx = (x1 - x0) / 8
    dy = (y1 - y0) / 8
    pts = [(x0 + i * dx, y0 + i * dy) for i in range(9)]
    return pts

def plot_grid_on_transformed_image(image):
    corners = np.array([[0, 0],
                        [image.size[0], 0],
                        [0, image.size[1]],
                        [image.size[0], image.size[1]]])

    corners = order_points(corners)

    figure(figsize=(10, 10), dpi=80)

    # im = plt.imread(image)
    implot = plt.imshow(image)

    TL = corners[0]
    BL = corners[3]
    TR = corners[1]
    BR = corners[2]

    ptsT = interpolate(TL, TR)
    ptsL = interpolate(TL, BL)
    ptsR = interpolate(TR, BR)
    ptsB = interpolate(BL, BR)

    for a, b in zip(ptsL, ptsR):
        plt.plot([a[0], b[0]], [a[1], b[1]], 'ro', linestyle="--")
    for a, b in zip(ptsT, ptsB):
        plt.plot([a[0], b[0]], [a[1], b[1]], 'ro', linestyle="--")

    plt.axis('off')

    plt.savefig('chessboard_transformed_with_grid.jpg')
    return ptsT, ptsL

"""
    Solving the chess piece recognition problem
"""
#
# # detects chess pieces
# def chess_pieces_detector(image):
#     model_trained = YOLO("best_transformed_detection.pt")
#     results = model_trained.predict(source=image, line_thickness=1, conf=0.5, augment=False, save_txt=True, save=True)
#
#     boxes = results[0].boxes
#     detections = boxes.xyxy.numpy()
#
#     return detections, boxes
#
# # calculates iou between two polygons
# def calculate_iou(box_1, box_2):
#     poly_1 = Polygon(box_1)
#     poly_2 = Polygon(box_2)
#     iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
#     return iou
#
# # connects detected piece to the right square
# def connect_square_to_detection(detections, square):
#     di = {0: 'b', 1: 'k', 2: 'n',
#           3: 'p', 4: 'q', 5: 'r',
#           6: 'B', 7: 'K', 8: 'N',
#           9: 'P', 10: 'Q', 11: 'R'}
#
#     list_of_iou = []
#
#     for i in detections:
#
#         box_x1 = i[0]
#         box_y1 = i[1]
#
#         box_x2 = i[2]
#         box_y2 = i[1]
#
#         box_x3 = i[2]
#         box_y3 = i[3]
#
#         box_x4 = i[0]
#         box_y4 = i[3]
#
#         # cut high pieces
#         if box_y4 - box_y1 > 60:
#             box_complete = np.array([[box_x1, box_y1 + 40], [box_x2, box_y2 + 40], [box_x3, box_y3], [box_x4, box_y4]])
#         else:
#             box_complete = np.array([[box_x1, box_y1], [box_x2, box_y2], [box_x3, box_y3], [box_x4, box_y4]])
#
#         # until here
#
#         list_of_iou.append(calculate_iou(box_complete, square))
#
#     num = list_of_iou.index(max(list_of_iou))
#
#     piece = boxes.cls[num].tolist()
#
#     if max(list_of_iou) > 0.15:
#         piece = boxes.cls[num].tolist()
#         return di[piece]
#
#     else:
#         piece = "empty"
#         return piece
