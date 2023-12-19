import pyrealsense2 as rs
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.components import containers
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
from cam_utils import *
import chess
import time
import cv2
import os

class Camera:
    def __init__(self, max_history=2):
        self._setup_camera()
        self._get_corners()
        self._init_hand_detector()

        self.large_threshold = 10
        self.small_threshold = 5

        self.sample_board("previous_turn")
        self._init_heatmap()
        #self._init_detailed_heatmap()

        self.frame_history = []
        self.max_history = max_history
        self.wrong_moves_folder = "wrong_moves"
        self.correct_moves = 0
        self.wrong_moves = 0

    ##################
    # CAMERA SETUP   #
    ##################

    def _setup_camera(self):
        # Connect camera
        self.pipe = rs.pipeline()
        cfg = rs.config()
        cfg.disable_all_streams()
        cfg.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)
        self.pipe.start(cfg)

        # Lose the first 5 frames, as they are often corrupted
        for _ in range(5):
            _ = self.pipe.wait_for_frames()

    def _get_corners(self):
        # Get the corners of the markers
        frame = self.pipe.wait_for_frames()
        color_frame = frame.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())

        self.corners = detect_markers(color_image)

    ##################
    # HEATMAP        #
    ##################

    def _init_heatmap(self):
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

    def _update_heatmap(self, square_diffs, avg_diff, show_heatmap=False):
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

    def _init_detailed_heatmap(self):
        self.fig, self.axs = plt.subplots(2, 3, figsize=(15, 10))  # Adjust the size as needed
        self.detailed_heatmaps = {}

        sections = ['center', 'left', 'right', 'top', 'bottom']
        for ax, section in zip(self.axs.flat, sections):
            self.detailed_heatmaps[section] = ax.imshow([[0]*8 for _ in range(8)], interpolation='nearest', vmin=0, vmax=50, cmap='jet')
            ax.set_title(section.capitalize())
            ax.set_xticks(range(8))
            ax.set_yticks(range(8))
            plt.colorbar(self.detailed_heatmaps[section], ax=ax)

        plt.tight_layout()
        plt.show(block=False)

    def _update_detailed_heatmap(self, detailed_square_diffs):
        # Initialize a data structure for heatmap values
        heatmap_values = {section: [[0]*8 for _ in range(8)] for section in ['center', 'left', 'right', 'top', 'bottom']}

        # Populate heatmap values
        for idx, _, section_diffs in detailed_square_diffs:
            row, col = divmod(idx, 8)
            for section, value in section_diffs.items():
                heatmap_values[section][row][col] = value

        # Update each heatmap
        for section, data in heatmap_values.items():
            self.detailed_heatmaps[section].set_data(data)
            self.axs.flat[section].draw_idle()

    ############################
    # MEDIAPIPE / DETECT HANDS #
    ############################

    def _init_hand_detector(self):
        base_options = mp_python.BaseOptions(model_asset_path=os.path.join('third_party', 'mediapipe', 'hand_landmarker.task'))
        options = mp_vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
        self.hand_detector = mp_vision.HandLandmarker.create_from_options(options)

    def detect_hands(self, color_frame):
        color_image = np.asanyarray(color_frame.get_data())
        cv2.imwrite(f'detect_hand.png', color_image)

        #mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=color_image)
        mp_image = mp.Image.create_from_file(f'detect_hand.png')
        
        # Detect hands
        detection_result = self.hand_detector.detect(mp_image)

        # Check if hands are detected
        if detection_result and detection_result.hand_landmarks:
            print('Hands Detected!')
            return len(detection_result.hand_landmarks) > 0
        return False
    
    ##################
    # BOARD SAMPLING #
    ##################

    def get_processed_frame(self):
        warped_image = None
        while warped_image is None:
            frames = self.pipe.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                continue

            if self.detect_hands(color_frame):
                time.sleep(3)
                continue

            color_image = np.asanyarray(color_frame.get_data())
            warped_image = apply_perspective_transform(color_image, self.corners)

        return warped_image
    
    def sample_board(self, folder_name, max_samples=5):
        # Create folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        sample_number = 0

        while sample_number < max_samples:
            frame = self.get_processed_frame()

            if frame is not None:
                # Save the entire frame
                frame_filename = os.path.join(folder_name, f'frame_sample_{sample_number}.jpg')
                cv2.imwrite(frame_filename, frame)
                sample_number += 1
                time.sleep(0.01)

    def load_saved_frames_as_squares(self, folder_name="previous_turn", num_samples=5):
        frames_as_squares = [[] for _ in range(64)]  # Assuming standard 8x8 chessboard

        self.previous_frames = []
        for i in range(num_samples):
            frame_path = os.path.join(folder_name, f'frame_sample_{i}.jpg')
            frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
            self.previous_frames.append(frame)
            if frame is not None:
                squares = divide_into_squares(frame)
                for j, square in enumerate(squares):
                    frames_as_squares[j].append(square)

        self.old_squares = frames_as_squares

    def get_relevant_squares(self, board, turn):
        """Get squares relevant to the current turn."""
        relevant_squares = set()
        for move in board.legal_moves:
            if board.color_at(move.from_square) == turn:
                relevant_squares.add(chess_square_to_camera_perspective(move.from_square))
                relevant_squares.add(chess_square_to_camera_perspective(move.to_square))

        return relevant_squares
    
    ##################
    # MOVE DETECTION #
    ##################

    def compare_squares(self, board, turn):
        self.load_saved_frames_as_squares()
        self.frame = self.get_processed_frame()
        ssim_squares = self.ssim_square(board, turn)
        detailed_squares = self.ssim_small(ssim_squares)
        return detailed_squares

    def ssim_square(self, board, turn):
        relevant_squares = self.get_relevant_squares(board, turn)
        new_squares = divide_into_squares(self.frame)

        square_diffs = []
        for idx in relevant_squares:
            new = new_squares[idx]
            if new is not None:
                new_gray = cv2.cvtColor(new, cv2.COLOR_BGR2GRAY)
                diffs = []
                for old_sample in self.old_squares[idx]:
                    if old_sample is not None:
                        old_gray = cv2.cvtColor(old_sample, cv2.COLOR_BGR2GRAY)
                        score, _ = ssim(old_gray, new_gray, full=True)
                        diff = (1 - score) * 100
                        diffs.append(diff)

                avg_diff = sum(diffs) / len(diffs) if diffs else 0
                square_diffs.append((idx, avg_diff))

        self._update_heatmap(square_diffs, avg_diff)

        # Sort and filter based on overall changes
        square_diffs.sort(key=lambda x: x[1], reverse=True)
        return [(idx, avg_diff) for idx, avg_diff in square_diffs if avg_diff > self.large_threshold]
    
    def ssim_small(self, squares, detailed_threshold=6):
        new_squares = divide_into_squares(self.frame)

        detailed_square_diffs = []
        for idx, avg_diff in squares[:detailed_threshold]:
            new = new_squares[idx]
            new_sections_gray = split_into_sections(cv2.cvtColor(new, cv2.COLOR_BGR2GRAY))
            # Visualize the sections
            diffs = {'center': 0, 'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
            for old_sample in self.old_squares[idx]:
                if old_sample is not None:
                    old_sample_gray = cv2.cvtColor(old_sample, cv2.COLOR_BGR2GRAY)
                    old_sections_gray = split_into_sections(old_sample_gray)
                    for section in new_sections_gray:
                        score, _ = ssim(old_sections_gray[section], new_sections_gray[section], full=True)
                        diff = (1 - score) * 100
                        diffs[section] += diff
            avg_diffs = {section: diffs[section] / len(self.old_squares[idx]) for section in diffs}
            # Only append if the average difference is larger than 7
            if max(avg_diffs.values()) > self.small_threshold:
                detailed_square_diffs.append((idx, avg_diff, avg_diffs))

        return detailed_square_diffs
    
    def recognize_move(self, board, turn):
        # Get the squares that have changed along with their details
        changed_squares_with_details = self.compare_squares(board, turn)

        if len(changed_squares_with_details) == 0:
            return None
        
        #self._update_detailed_heatmap(changed_squares_with_details)

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

        if len(refined_moves) == 0:
            return None
        elif len(refined_moves) == 1:
            self.correct_moves += 1
            self.add_to_history(self.frame, self.previous_frames, self.heatmap.get_array())
            return refined_moves[0][0]
        
        self.correct_moves += 1
        self.add_to_history(self.frame, self.previous_frames, self.heatmap.get_array())

        # If refined move difference between first and second is higher than 30, return the first move
        if len(refined_moves) > 1 and refined_moves[0][1] - refined_moves[1][1] > 30:
            return refined_moves[0][0]

        # Return the top 5 moves (if more than one) with the highest score
        return [move for move, _ in refined_moves[:5]]

    ##################
    # GETTER/SETTERS #
    ##################

    def get_large_threshold(self):
        return self.large_threshold
    
    def set_large_threshold(self, value):
        self.large_threshold = value

    def get_small_threshold(self):
        return self.small_threshold
    
    def set_small_threshold(self, value):
        self.small_threshold = value

    def print_stats(self):
        print(f"Correct moves: {self.correct_moves}")
        print(f"Wrong moves: {self.wrong_moves}")

    ##############
    # STATISTICS #
    ##############
    
    def add_to_history(self, frame, previous_turn_samples, heatmap_data):
        if len(self.frame_history) >= self.max_history:
            self.frame_history.pop(0)
        self.frame_history.append((frame, previous_turn_samples, heatmap_data))

    def archive_wrong_move(self, num_moves_to_pop):
        while num_moves_to_pop > 0 and self.frame_history:
            num_moves_to_pop -= 1

            # Pop the oldest record in the history
            current_frame, previous_turn_samples, heatmap_data = self.frame_history.pop(0)

            # Create a folder for this wrong move
            wrong_move_folder = os.path.join(self.wrong_moves_folder, f"wrong_move_{time.strftime('%Y%m%d-%H%M%S')}")
            os.makedirs(wrong_move_folder, exist_ok=True)

            # Save the current frame
            cv2.imwrite(os.path.join(wrong_move_folder, "current_frame.jpg"), current_frame)

            # Save the previous turn samples
            for i, prev_frame in enumerate(previous_turn_samples):
                cv2.imwrite(os.path.join(wrong_move_folder, f"prev_turn_sample_{i}.jpg"), prev_frame)

            # Save the heatmap data
            self.save_heatmap(os.path.join(wrong_move_folder, "heatmap.png"), heatmap_data)

        # We did one wrong move, which we counted as a correct move.
        self.wrong_moves += 1
        self.correct_moves -= 1

    def save_heatmap(self, filename, heatmap_data):
        fig, ax = plt.subplots()
        heatmap = ax.imshow(heatmap_data, interpolation='nearest', vmin=0, vmax=50, cmap='jet')
        plt.colorbar(heatmap)
        ax.set_xticks(range(8))
        ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
        ax.set_yticks(range(8))
        ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])
        plt.savefig(filename)
        plt.close()