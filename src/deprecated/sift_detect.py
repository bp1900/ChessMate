import pyrealsense2 as rs
import numpy as np
import cv2
import os
import pickle

def tuple_to_keypoint(tup):
    # Ensure the tuple elements are correctly mapped to the KeyPoint parameters
    # Assuming the tuple has 6 elements: (x, y, size, angle, response, octave)
    return cv2.KeyPoint(x=tup[0][0], y=tup[0][1], size=tup[1], angle=tup[2], response=tup[3], octave=tup[4], class_id=tup[5])


def load_keypoints_database(file_path):
    with open(file_path, 'rb') as f:
        keypoints_database = pickle.load(f)
    # Convert tuples back to KeyPoint objects
    for piece_type, keypoints_list in keypoints_database.items():
        for i in range(len(keypoints_list)):
            keypoints, descriptors = keypoints_list[i]
            keypoints_list[i] = ([tuple_to_keypoint(kp) for kp in keypoints], descriptors)
    return keypoints_database

def initialize_camera():
    pipe = rs.pipeline()
    cfg = rs.config()
    cfg.disable_all_streams()
    cfg.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)
    pipe.start(cfg)
    return pipe

def detect_piece(image, keypoints_database, sift):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    keypoints, descriptors = sift.detectAndCompute(gray, None)

    if descriptors is not None:
        best_match = None
        highest_match_count = 0
        bf = cv2.BFMatcher()

        for piece_type, keypoints_list in keypoints_database.items():
            for kp, desc in keypoints_list:
                matches = bf.knnMatch(desc, descriptors, k=2)
                
                # Filter good matches
                good_matches = []
                for match_pair in matches:
                    if len(match_pair) == 2:
                        m, n = match_pair
                        if m.distance < 0.75 * n.distance:
                            good_matches.append(m)

                if len(good_matches) > highest_match_count:
                    highest_match_count = len(good_matches)
                    best_match = piece_type

        return best_match, highest_match_count
    return None, 0


def main():
    # Load keypoints database
    keypoints_database = load_keypoints_database('keypoints_database.pkl')

    # Initialize SIFT
    sift = cv2.SIFT_create()

    # Initialize camera
    pipe = initialize_camera()

    # Capture the first frame and select ROI
    frames = pipe.wait_for_frames()
    color_frame = frames.get_color_frame()
    initial_image = np.asanyarray(color_frame.get_data())
    roi = cv2.selectROI("Select ROI", initial_image, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Select ROI")
    x, y, w, h = roi

    while True:
        frames = pipe.wait_for_frames()
        color_frame = frames.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())

        # Crop to the selected ROI
        cropped_image = color_image[y:y+h, x:x+w]

        # Detect piece in the cropped image
        piece, match_count = detect_piece(cropped_image, keypoints_database, sift)

        if piece is not None:
            cv2.putText(cropped_image, f'Detected: {piece} (Matches: {match_count})', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow('Camera Feed', cropped_image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pipe.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
