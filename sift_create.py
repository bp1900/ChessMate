import cv2
import numpy as np
import os
import pickle

def keypoint_to_tuple(keypoint):
    return (keypoint.pt, keypoint.size, keypoint.angle, keypoint.response, keypoint.octave, keypoint.class_id)

def create_sift_keypoints(root_dir):
    sift = cv2.SIFT_create()
    keypoints_database = {}

    for folder in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder, 'cropped')
        if os.path.isdir(folder_path):
            keypoints_database[folder] = []

            for filename in os.listdir(folder_path):
                if filename.endswith(".jpg"):
                    image_path = os.path.join(folder_path, filename)
                    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

                    # Detect SIFT features
                    keypoints, descriptors = sift.detectAndCompute(image, None)

                    # Convert keypoints to a pickle-able format
                    keypoints = [keypoint_to_tuple(kp) for kp in keypoints]

                    # Store keypoints and descriptors
                    keypoints_database[folder].append((keypoints, descriptors))

            print(f"Processed {folder}")

    # Save keypoints database to a file
    with open('keypoints_database.pkl', 'wb') as f:
        pickle.dump(keypoints_database, f)

    print("Keypoint detection completed and saved.")

def main():
    root_dir = "images"
    create_sift_keypoints(root_dir)

if __name__ == "__main__":
    main()
