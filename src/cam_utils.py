import os
import numpy as np
import cv2
import matplotlib.pyplot as plt


def chess_square_to_camera_perspective(square_idx):
    # Assuming square_idx is from 0 to 63, where 0 is a1 and 63 is h8.
    # Flip the row (0 becomes 7, 1 becomes 6, etc.)
    row, col = divmod(square_idx, 8)
    flipped_row = 7 - row
    return flipped_row * 8 + col


def resize_image(image, max_width=1280, max_height=720):
    height, width = image.shape[:2]
    if width > max_width or height > max_height:
        scaling_factor = min(max_width / width, max_height / height)
        return cv2.resize(image, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
    return image


def select_points(image, num_points=6):
    points = []
    #resized_image = resize_image(image)
    #cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)
    #cv2.resizeWindow("Camera Feed", 1280, 720) 

    def click_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < num_points:
            points.append((x, y))
            cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
            cv2.imshow("Image", image)

    cv2.imshow("Image", image)
    cv2.setMouseCallback("Image", click_event)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return points

def apply_perspective_transform(image, corners, chessboard_size=(7, 7), square_size_cm=4, pixels_per_cm=20):
    if len(corners) != 6:
        return None

    # Main chessboard transform
    main_chessboard_width_px = (chessboard_size[0] - 1) * square_size_cm * pixels_per_cm
    chessboard_height_px = chessboard_size[1] * square_size_cm * pixels_per_cm
    pts_src_main = np.array([corners[0], corners[1], corners[2], corners[3]], dtype="float32")
    pts_dst_main = np.array([
        [0, 0],
        [main_chessboard_width_px - 1, 0],
        [0, chessboard_height_px - 1],
        [main_chessboard_width_px - 1, chessboard_height_px - 1],
    ], dtype="float32")
    M_main = cv2.getPerspectiveTransform(pts_src_main, pts_dst_main)
    main_chessboard = cv2.warpPerspective(image, M_main, (main_chessboard_width_px, chessboard_height_px))

    # Last column transform
    last_col_width_px = 7 * pixels_per_cm
    pts_src_last_col = np.array([corners[4], corners[0], corners[5], corners[2]], dtype="float32")
    pts_dst_last_col = np.array([
        [0, 0],
        [last_col_width_px - 1, 0],
        [0, chessboard_height_px - 1],
        [last_col_width_px - 1, chessboard_height_px - 1],
    ], dtype="float32")
    M_last_col = cv2.getPerspectiveTransform(pts_src_last_col, pts_dst_last_col)
    last_column = cv2.warpPerspective(image, M_last_col, (last_col_width_px, chessboard_height_px))

    # Combine the two parts
    combined_chessboard = np.hstack((last_column, main_chessboard)) # before rotation

    # Rotate the image around the y-axis (horizontal flip)
    #rotated_image = cv2.flip(combined_chessboard, 1)

    cv2.imshow('Chessboard', combined_chessboard)
    return combined_chessboard

def divide_into_squares_left(warped_image, chessboard_size=(8, 8), extended_last_col_width_cm=7, pixels_per_cm=20):
    squares = []
    square_size = int(warped_image.shape[0] / chessboard_size[0])
    extended_last_col_width_px = extended_last_col_width_cm * pixels_per_cm

    for row in range(chessboard_size[0]):
        for col in range(chessboard_size[1]):
            if col == chessboard_size[1] - 1:  # Last column
                # For the last column, use the extended width
                square = warped_image[row*square_size:(row+1)*square_size, 
                                      col*square_size:col*square_size + extended_last_col_width_px]
            else:
                # For other columns, use the standard square size
                square = warped_image[row*square_size:(row+1)*square_size, 
                                      col*square_size:(col+1)*square_size]
            squares.append(square)

    return squares

def divide_into_squares(warped_image, chessboard_size=(8, 8), extended_first_col_width_cm=7, pixels_per_cm=20):
    squares = []
    square_size = int(warped_image.shape[0] / chessboard_size[0])
    extended_first_col_width_px = extended_first_col_width_cm * pixels_per_cm

    for row in range(chessboard_size[0]):
        for col in range(chessboard_size[1]):
            if col == 0:  # First column
                # For the first column, use the extended width
                square = warped_image[row*square_size:(row+1)*square_size,
                                      col*square_size:col*square_size + extended_first_col_width_px]
            else:
                # Adjust the start of the next square to account for the extended first column
                start_col = col*square_size + (extended_first_col_width_px - square_size)
                square = warped_image[row*square_size:(row+1)*square_size,
                                      start_col:(start_col+square_size)]
            squares.append(square)

    return squares

# Function to find corners of markers
def detect_markers(image):
    # Let user manually select points on the markers
    selected_points = [(1000, 641), (1008, 983), (608, 638), (544, 983), (996, 581), (622, 579)] 
    #selected_points = select_points(image.copy())

    # Convert image to float and apply SLIC
    #image_float = img_as_float(image)
    #segments_slic = slic(image_float, n_segments=300, compactness=10, sigma=1, start_label=1)

    marker_corners = selected_points
    #marker_corners = []

    # Iterate over each selected point to find corresponding superpixel
    #for point in selected_points:
    #    # Get the segment label of the selected point
    #    segment_label = segments_slic[point[1], point[0]]

    #    # Create a mask for the selected superpixel
    #    mask = segments_slic == segment_label

    #    # Find contours in the masked image
    #    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    #    # Assuming the largest contour in the mask is the marker
    #    if contours:
    #        c = max(contours, key=cv2.contourArea)
    #        # Get the corner of the contour (modify this part based on how you want to get the corner)
    #        epsilon = 0.1 * cv2.arcLength(c, True)
    #        approx = cv2.approxPolyDP(c, epsilon, True)
    #        marker_corners.append(approx[0][0])  # Modify this to select the correct corner

    ## Visualize the detected corners
    #for corner in marker_corners:
    #    cv2.circle(image, tuple(corner), 5, (255, 0, 0), -1)

    #cv2.imshow('Image with Detected Corners', image)

    print(marker_corners)
    return marker_corners

def detect_chessboard(cropped_image):
    # Convert to HSV and create a mask to filter out green hues
    hsv = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([60, 60, 40])  # Adjust these values
    upper_green = np.array([120, 255, 255])  # Adjust these values
    mask = cv2.inRange(hsv, lower_green, upper_green)
    filtered_image = cv2.bitwise_and(cropped_image, cropped_image, mask=~mask)

    # Convert to grayscale
    gray = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur and thresholding
    blur = cv2.GaussianBlur(gray, (3, 3), 2)
    ret, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_OTSU)

    # Optionally, apply Canny edge detection
    # edges = cv2.Canny(blur, 50, 150)

    # Define a kernel for the closing operation
    kernel = np.ones((10, 10), np.uint8)

    # Apply morphological closing
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Find the chessboard corners
    ret, corners = cv2.findChessboardCorners(closing, (7, 7), cv2.CALIB_CB_ADAPTIVE_THRESH)

    if ret:
        # Draw corners on the cropped image
        cv2.drawChessboardCorners(cropped_image, (7, 7), corners, ret)

    cv2.imshow('Processed Image', closing)
    return ret, corners if ret else None

def index_to_algebraic(square_index, board_size=8):
    file_letters = 'abcdefgh'
    rank = board_size - (square_index // board_size)
    file = file_letters[square_index % board_size]
    return f'{file}{rank}'

def algebraic_to_index(square_name, board_size=8):
    file_letters = 'abcdefgh'
    file = square_name[0]
    rank = int(square_name[1])
    return (board_size - rank) * board_size + file_letters.index(file)

def plot_heatmap(data):
    fig, ax = plt.subplots()
    heatmap = ax.imshow(data, cmap='hot', interpolation='nearest')
    plt.colorbar(heatmap)
    plt.show()

def split_into_sections(square):
    h, w = square.shape[:2]
    center = square[h//4:3*h//4, w//4:3*w//4]
    left = square[:, :w//2]
    right = square[:, w//2:]
    top = square[:h//2, :]
    bottom = square[h//2:, :]
    return {'center': center, 'left': left, 'right': right, 'top': top, 'bottom': bottom}