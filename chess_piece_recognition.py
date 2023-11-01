# Libraries
import os
import cv2

from shapely.geometry import Polygon
from ultralytics import YOLO

from lc2fen.predict_board import obtain_individual_pieces, load_image
from lc2fen.infer_pieces import infer_chess_pieces

from keras.models import load_model
from keras.applications.imagenet_utils import preprocess_input as prein_squeezenet

def calculate_iou(box_1, box_2):
    poly_1 = Polygon(box_1)
    poly_2 = Polygon(box_2)
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
    return iou


def chess_pieces_detector(image):

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Predict using YOLO
    model_path = os.path.join('models', "best_transformed_detection.pt")
    model_trained = YOLO(model_path)
    results = model_trained.predict(source=image, line_thickness=1, conf=0.2, augment=False, save_txt=True, save=True, imgsz=(512,512),
                                    save_conf=True)

    boxes = results[0].boxes
    detections = boxes.xyxy.numpy()

    return detections, boxes


def obtain_piece_probs_for_all_64_squares(pieces: list[str], img_size: int = 227) -> list[list[float]]:

    # Model
    model_path = os.path.join('models', 'SqueezeNet1p1.h5')
    model = load_model(model_path)

    predictions = []
    for piece in pieces:
        piece_img = load_image(piece, img_size, prein_squeezenet)
        predictions.append(model.predict(piece_img)[0])

    return predictions


def chess_pieces_detector2(image_path, a1_pos="TL", previous_fen=None):

    pieces = obtain_individual_pieces(image_path)
    probs_with_no_indices = obtain_piece_probs_for_all_64_squares(pieces)

    print(probs_with_no_indices)

    # predictions = infer_chess_pieces(probs_with_no_indices, a1_pos, previous_fen)
