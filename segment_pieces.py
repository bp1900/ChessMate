import cv2
import os

def crop_chess_piece(image_path, save_path):
    image = cv2.imread(image_path)
    
    # Select the ROI using cv2.selectROI
    r = cv2.selectROI("Crop Area", image, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Crop Area")

    # If no area is selected, return False
    if r == (0, 0, 0, 0):
        return False

    # Crop the image
    x, y, w, h = r
    cropped_image = image[y:y+h, x:x+w]
    cv2.imwrite(save_path, cropped_image)
    return True

def process_folder(folder_path):
    if not os.path.exists(os.path.join(folder_path, "cropped")):
        os.makedirs(os.path.join(folder_path, "cropped"))

    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg"):
            image_path = os.path.join(folder_path, filename)
            save_path = os.path.join(folder_path, "cropped", filename)

            success = crop_chess_piece(image_path, save_path)
            if not success:
                print(f"Failed to crop {image_path}")

def main():
    root_dir = "images"
    for folder in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder)
        if os.path.isdir(folder_path):
            process_folder(folder_path)
            print(f"Processed folder: {folder}")

if __name__ == "__main__":
    main()
