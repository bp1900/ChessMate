from skimage.segmentation import slic
from skimage.util import img_as_float
import pyrealsense2 as rs
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from skimage.metrics import structural_similarity as ssim
from mediapipe.tasks.python.components import containers
import matplotlib.pyplot as plt
import chess
import time
import cv2
import os

class Camera:
    def __init__(self):
        # Connect camera
        self.pipe = rs.pipeline()
        cfg = rs.config()
        cfg.disable_all_streams()
        cfg.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)

        self.pipe.start(cfg)

        # Lose the first 5 frames, as they are often corrupted
        for i in range(5):
            frames = self.pipe.wait_for_frames()

        # Get the corners of the markers
        frame = self.pipe.wait_for_frames()
        color_frame = frame.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())
        self.corners = detect_markers(color_image)

        # Hand detector setup
        base_options = mp_python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = mp_vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
        self.hand_detector = mp_vision.HandLandmarker.create_from_options(options)

        self.sample_board("previous_turn")
        self.init_heatmap()
        self.init_segmenter()

    def init_segmenter(self):
        base_options = mp_python.BaseOptions(model_asset_path='magic_touch.tflite')
        options = mp_vision.InteractiveSegmenterOptions(
            base_options=base_options,
            output_category_mask=True)
        self.segmenter = mp_vision.InteractiveSegmenter.create_from_options(options)

    def init_heatmap(self):
        self.fig, self.ax = plt.subplots()
        # Initialize with a fixed color scale range if known, e.g., vmin=0, vmax=1000
        self.heatmap = self.ax.imshow([[0]*8 for _ in range(8)], interpolation='nearest', vmin=0, vmax=50, cmap='jet')
        plt.colorbar(self.heatmap)

        # Set the x-tick labels
        self.ax.set_xticks(range(8))
        self.ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])

        # Set the y-tick labels
        self.ax.set_yticks(range(8))
        self.ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])

        plt.show(block=False)  # Show non-blocking plot

    def update_heatmap(self, square_diffs, avg_diff, show_heatmap=False):
        # Create a 2D array for the heatmap
        heatmap_data = [[0] * 8 for _ in range(8)]
        for idx, avg_diff in square_diffs:
            row, col = divmod(idx, 8)
            heatmap_data[row][col] = avg_diff

        # Update the heatmap data
        self.heatmap.set_data(heatmap_data)
        self.fig.canvas.draw_idle()

        # Bring the plot to the foreground only if required
        if show_heatmap:
            plt.pause(0.001)  # Update the plot and bring it to the foreground
        else:
            self.fig.canvas.start_event_loop(0.001)  # Update without bringing to foreground

    def detect_hands(self):
        # Convert to mediapipe image format
        frame = self.pipe.wait_for_frames()
        color_frame = frame.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=color_image)
        
        # Detect hands
        detection_result = self.hand_detector.detect(mp_image)

        # Check if hands are detected
        if detection_result and detection_result.hand_landmarks:
            print("Hands detected!")
            time.sleep(3)
            return len(detection_result.hand_landmarks) > 0
        return False

    def get_processed_frame(self):
        warped_image = None
        while warped_image is None:
            frames = self.pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            warped_image = apply_perspective_transform(color_image, self.corners)

        return warped_image
    
    def segment_square(self, combined_image, center):
        RegionOfInterest = mp_vision.InteractiveSegmenterRegionOfInterest
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=combined_image)
        x, y = center

        roi = RegionOfInterest(format=RegionOfInterest.Format.KEYPOINT,
                               keypoint=containers.keypoint.NormalizedKeypoint(x=x, y=y))
        segmentation_result = self.segmenter.segment(mp_image, roi)

        if segmentation_result:
            category_mask = segmentation_result.category_mask

            # For visualization
            image_data = mp_image.numpy_view()
            fg_image = np.zeros(image_data.shape, dtype=np.uint8)
            fg_image[:] = (255, 255, 255)
            bg_image = np.zeros(image_data.shape, dtype=np.uint8)
            bg_image[:] = (192, 192, 192)

            condition = np.stack((category_mask.numpy_view(),) * 3, axis=-1) > 0.1
            output_image = np.where(condition, fg_image, bg_image)
            return output_image
        return None

    def get_center_of_left_square(self, combined_image):
        height, width, _ = combined_image.shape
        center_x = width // 2  # Half of the half width (as we concatenated two squares)
        center_y = height // 2
        return center_x / width, center_y / height  # Normalized coordinates
    
    def sample_board(self, folder_name, max_samples=5):
        # If detect hands, skip sampling
        while self.detect_hands():
            pass

        sample_number = 0
        last_sample_time = None

        while sample_number < max_samples:
            frame = self.get_processed_frame()
            if frame is not None:
                current_squares = divide_into_squares(frame)
                save_squares(current_squares, folder_name, sample_number)
                sample_number += 1
                time.sleep(0.1)

    def get_relevant_squares(self, board, turn, debugging=False):
        """Get squares relevant to the current turn."""
        relevant_squares = set()

        if debugging:
            # Add all squares for debugging
            for i in range(64):
                relevant_squares.add(i)
        else:
            for move in board.legal_moves:
                if board.color_at(move.from_square) == turn:
                    relevant_squares.add(chess_square_to_camera_perspective(move.from_square))
                    relevant_squares.add(chess_square_to_camera_perspective(move.to_square))

        return relevant_squares

    def compare_squares(self, board, turn):
        ssim_squares = self.ssim_square(board, turn)
        detailed_squares = self.ssim_small(ssim_squares)
        return detailed_squares

    def ssim_square(self, board, turn, threshold=13):
        relevant_squares = self.get_relevant_squares(board, turn)
        old_squares = load_saved_squares("previous_turn")
        frame = self.get_processed_frame()
        new_squares = divide_into_squares(frame)

        square_diffs = []
        for idx in relevant_squares:
            new = new_squares[idx]
            if new is not None:
                new_gray = cv2.cvtColor(new, cv2.COLOR_BGR2GRAY)
                diffs = []
                for old_sample in old_squares[idx]:
                    if old_sample is not None:
                        old_gray = cv2.cvtColor(old_sample, cv2.COLOR_BGR2GRAY)
                        score, _ = ssim(old_gray, new_gray, full=True)
                        diff = (1 - score) * 100
                        diffs.append(diff)

                avg_diff = sum(diffs) / len(diffs) if diffs else 0
                square_diffs.append((idx, avg_diff))

        self.update_heatmap(square_diffs, avg_diff)

        # Sort and filter based on overall changes
        square_diffs.sort(key=lambda x: x[1], reverse=True)
        return [(idx, avg_diff) for idx, avg_diff in square_diffs if avg_diff > threshold]
    
    def ssim_small(self, squares, detailed_threshold=5, threshold=5):
        old_squares = load_saved_squares("previous_turn")
        frame = self.get_processed_frame()
        new_squares = divide_into_squares(frame)

        detailed_square_diffs = []
        for idx, avg_diff in squares[:detailed_threshold]:
            new = new_squares[idx]
            new_sections_gray = split_into_sections(cv2.cvtColor(new, cv2.COLOR_BGR2GRAY))
            # Visualize the sections
            diffs = {'center': 0, 'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
            for old_sample in old_squares[idx]:
                if old_sample is not None:
                    old_sample_gray = cv2.cvtColor(old_sample, cv2.COLOR_BGR2GRAY)
                    old_sections_gray = split_into_sections(old_sample_gray)
                    for section in new_sections_gray:
                        score, _ = ssim(old_sections_gray[section], new_sections_gray[section], full=True)
                        diff = (1 - score) * 100
                        diffs[section] += diff
            avg_diffs = {section: diffs[section] / len(old_squares[idx]) for section in diffs}
            # Only append if the average difference is larger than 7
            if max(avg_diffs.values()) > threshold:
                detailed_square_diffs.append((idx, avg_diff, avg_diffs))

        return detailed_square_diffs
    
    def recognize_move(self, board, turn):
        if self.detect_hands():
            return None

        # Get the squares that have changed along with their details
        changed_squares_with_details = self.compare_squares(board, turn)

        if len(changed_squares_with_details) == 0:
            return None
        
        # Calculate scores for each square based on detailed section differences
        square_scores = {}
        for idx, _, section_diffs in changed_squares_with_details:
            left_idx = idx - 1 if idx % 8 != 0 else None  # Get the left square index if it exists
            left_diffs = next((details for idy, _, details in changed_squares_with_details if idy == left_idx), None) if left_idx is not None else None

            score = section_diffs['center'] + section_diffs['right']
            if left_diffs:
                score += left_diffs['left']
            square_scores[idx] = score

        # Filter out only legal moves and calculate their scores
        legal_moves = []
        castling_moves = []
        for from_sq, from_score in square_scores.items():
            #from_sq = chess.SQUARES[from_sq]
            for to_sq, to_score in square_scores.items():
                #to_sq = chess.SQUARES[to_sq]
                if from_sq != to_sq:
                    move = chess.Move.from_uci(f"{index_to_algebraic(from_sq)}{index_to_algebraic(to_sq)}")
                    print(move)
                    promotion_move = chess.Move.from_uci(f"{index_to_algebraic(from_sq)}{index_to_algebraic(to_sq)}q")
                    if move in board.legal_moves:
                        legal_moves.append((move, from_score + to_score))
                        if board.is_castling(move):
                            castling_moves.append((move, from_score + to_score))
                    elif promotion_move in board.legal_moves:
                        legal_moves.append((promotion_move, from_score + to_score))

        # Check for castling
        if board.has_castling_rights(turn):
            square_scores = {idx: sum(section_diffs.values()) for idx, _, section_diffs in changed_squares_with_details}
            kingside_squares = [algebraic_to_index('e1'), algebraic_to_index('f1'), algebraic_to_index('g1'), algebraic_to_index('h1') ] if turn == chess.WHITE else [algebraic_to_index('e8'), algebraic_to_index('f8'), algebraic_to_index('g8'), algebraic_to_index('h8') ]
            queenside_squares = [algebraic_to_index('e1'), algebraic_to_index('d1'), algebraic_to_index('c1'), algebraic_to_index('a1')] if turn == chess.WHITE else [algebraic_to_index('e8'), algebraic_to_index('d8'), algebraic_to_index('c8'), algebraic_to_index('a8')]
            
            kingside_move = chess.Move.from_uci("e1g1" if turn == chess.WHITE else "e8g8")
            queenside_move = chess.Move.from_uci("e1c1" if turn == chess.WHITE else "e8c8")

            if all(square_scores.get(sq, 0) > 25 for sq in kingside_squares) and kingside_move in board.legal_moves:
                return kingside_move
            if all(square_scores.get(sq, 0) > 25 for sq in queenside_squares) and queenside_move in board.legal_moves:
                return queenside_move

        # Sort moves by their calculated score
        refined_moves = sorted(legal_moves, key=lambda x: x[1], reverse=True)
        for move, score in refined_moves:
            print(f"Refined Move: {move}, Score: {round(score)}")

        if len(refined_moves) == 0:
            return None
        elif len(refined_moves) == 1:
            return refined_moves[0][0]
        
        # If refined move difference between first and second is higher than 30, return the first move
        if len(refined_moves) > 1 and refined_moves[0][1] - refined_moves[1][1] > 30:
            return refined_moves[0][0]

        # Return the top 5 moves (if more than one) with the highest score
        return [move for move, _ in refined_moves[:5]]
    
def chess_square_to_camera_perspective(square_idx):
    # Assuming square_idx is from 0 to 63, where 0 is a1 and 63 is h8.
    # Flip the row (0 becomes 7, 1 becomes 6, etc.)
    row, col = divmod(square_idx, 8)
    flipped_row = 7 - row
    return flipped_row * 8 + col

def save_squares(squares, folder_name, sample_number):
    for square_id, square in enumerate(squares):
        square_filename = os.path.join(folder_name, f'square_{square_id}_sample_{sample_number}.jpg')
        cv2.imwrite(square_filename, square)

def load_saved_squares(folder_name, num_samples=5):
    squares = [[] for _ in range(64)]  # Assuming standard 8x8 chessboard
    for i in range(64):
        for j in range(num_samples):
            img_path = os.path.join(folder_name, f'square_{i}_sample_{j}.jpg')
            square_img = cv2.imread(img_path, cv2.IMREAD_COLOR)
            if square_img is not None:
                squares[i].append(square_img)
    return squares

def select_points(image, num_points=4):
    points = []

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
    rotated_image = cv2.flip(combined_chessboard, 1)

    cv2.imshow('Warped Image', rotated_image)
    return rotated_image

def divide_into_squares(warped_image, chessboard_size=(8, 8), extended_last_col_width_cm=7, pixels_per_cm=20):
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

# Function to find corners of markers
def detect_markers(image):
    # Let user manually select points on the markers
    selected_points = [(728, 404), (604, 1035), (1434, 408), (1559, 1059), (734, 294), (1430, 293)]
    #selected_points = select_points(image.copy())

    # Convert image to float and apply SLIC
    image_float = img_as_float(image)
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