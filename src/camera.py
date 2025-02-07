import pyrealsense2 as rs
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.components import containers
from skimage.metrics import structural_similarity as ssim
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from cam_utils import *
import chess
import time
import cv2
import os
import tkinter as tk
import copy

class Camera:
    def __init__(self, select_corners, large_threshold=20, small_threshold=10, max_history=2, parent=None):
        self._setup_camera()
        self._get_corners(select_corners)
        self._init_hand_detector()

        self.large_threshold = large_threshold
        self.small_threshold = small_threshold

        self.stability_threshold = 5
        self.stable_frame_count = 0
        self.last_stable_frame = None
        self.stability_ssim_threshold = 0.97

        self.sample_board()

        self.frame_history = []
        self.max_history = max_history
        self.wrong_moves_folder = "wrong_moves"
        self.correct_moves = 0
        self.wrong_moves = 0

        # Parent Tkinter widget
        self.parent = parent
        self._init_heatmaps()  # Initialize heatmaps

        self.is_active = True


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

        # Lose the first 10 frames, as they are often darker
        for _ in range(10):
            _ = self.pipe.wait_for_frames()

    def _get_corners(self, select_corners):
        # Get the corners of the markers
        frame = self.pipe.wait_for_frames()
        color_frame = frame.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())

        self.corners = detect_markers(color_image, select_corners)
        self.extended = len(self.corners) == 6

    ##################
    # HEATMAP        #
    ##################

    def _init_heatmaps(self):
        # Create a Toplevel window for the combined heatmaps
        self.heatmap_window = tk.Toplevel(self.parent)
        self.heatmap_window.title("Heatmaps")

        # Create a GridSpec with 4 columns and 2 rows (extra column for colorbar)
        gs = gridspec.GridSpec(2, 4, width_ratios=[1, 1, 1, 0.05])
        self.fig_heatmaps = plt.figure(figsize=(10, 6))

        # Initialize the main heatmap and other detailed heatmaps
        self.detailed_heatmaps = {}
        heatmap_positions = {
            'main': (0, 0), 'center': (0, 1), 'top': (0, 2),
            'left': (1, 0), 'right': (1, 1), 'bottom': (1, 2)
        }

        # Create each heatmap
        for section, pos in heatmap_positions.items():
            ax = plt.subplot(gs[pos])
            if section == 'main':
                self.heatmap = ax.imshow([[0]*8 for _ in range(8)], interpolation='nearest', vmin=0, vmax=100, cmap='jet')
                ax.set_title("Main Heatmap")
            else:
                # Initialize and store each detailed heatmap
                detailed_heatmap = ax.imshow([[0]*8 for _ in range(8)], interpolation='nearest', vmin=0, vmax=100, cmap='jet')
                self.detailed_heatmaps[section] = detailed_heatmap
                ax.set_title(section.capitalize())
            
            ax.set_xticks(range(8))
            ax.set_yticks(range(8))
            ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
            ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])

        # Create colorbar in the last column, spanning all rows
        cb_ax = plt.subplot(gs[:, -1])
        plt.colorbar(self.heatmap, cax=cb_ax)

        # Adjust layout
        plt.tight_layout()

        # Embed the Matplotlib figure in the Tkinter window
        self.canvas_heatmaps = FigureCanvasTkAgg(self.fig_heatmaps, master=self.heatmap_window)
        self.canvas_heatmaps_widget = self.canvas_heatmaps.get_tk_widget()
        self.canvas_heatmaps_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _update_heatmap(self, square_diffs, avg_diff, show_heatmap=False):
        # Create a 2D array for the heatmap
        heatmap_data = [[0] * 8 for _ in range(8)]
        for idx, avg_diff in square_diffs:
            row, col = divmod(idx, 8)
            heatmap_data[row][col] = avg_diff

        # Update the heatmap data
        self.heatmap.set_data(heatmap_data)
        #self.fig.canvas.draw_idle()

        # Bring the plot to the foreground only if required
        #if show_heatmap:
        #    plt.pause(0.001)  # Update the plot and bring it to the foreground
        #else:
        #    self.fig.canvas.start_event_loop(0.001)  # Update without bringing to foreground
        
    def _update_detailed_heatmap(self, detailed_square_diffs):
        # Update heatmap values
        heatmap_values = {section: [[0]*8 for _ in range(8)] for section in ['center', 'left', 'right', 'top', 'bottom']}
        for idx, _, section_diffs in detailed_square_diffs:
            row, col = divmod(idx, 8)
            for section, value in section_diffs.items():
                heatmap_values[section][row][col] = value

        self.canvas_heatmaps.draw_idle()

        self.detailed_heatmap_data = {}
        # Update each heatmap and redraw
        for section, data in heatmap_values.items():
            self.detailed_heatmaps[section].set_data(data)
            self.detailed_heatmap_data[section] = data

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

        #plt.show(block=False)  # Show non-blocking plot

    def _init_detailed_heatmap(self):
        # Create a Toplevel window for the detailed heatmap
        self.detailed_heatmap_window = tk.Toplevel(self.parent)
        self.detailed_heatmap_window.title("Detailed Heatmap")

        # Create a GridSpec with 5 columns and 1 row
        gs = gridspec.GridSpec(1, 6, width_ratios=[1, 1, 1, 1, 1, 0.05])
        self.fig_detailed = plt.figure(figsize=(15, 10))
        self.detailed_heatmaps = {}

        # Initialize heatmaps for each section
        sections = ['center', 'left', 'right', 'top', 'bottom']
        for i, section in enumerate(sections):
            ax = plt.subplot(gs[i])
            self.detailed_heatmaps[section] = ax.imshow([[0]*8 for _ in range(8)], interpolation='nearest', vmin=0, vmax=50, cmap='jet')
            ax.set_title(section.capitalize())
            ax.set_xticks(range(8))
            ax.set_yticks(range(8))

        # Create a single colorbar for all subplots
        cb_ax = plt.subplot(gs[-1])
        plt.colorbar(self.detailed_heatmaps[sections[0]], cax=cb_ax)

        plt.tight_layout()

        # Embed the Matplotlib figure in the Tkinter window
        self.canvas_detailed = FigureCanvasTkAgg(self.fig_detailed, master=self.detailed_heatmap_window)
        self.canvas_detailed_widget = self.canvas_detailed.get_tk_widget()
        self.canvas_detailed_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)



    ############################
    # MEDIAPIPE / DETECT HANDS #
    ############################

    def _init_hand_detector(self):
        base_options = mp_python.BaseOptions(model_asset_path=os.path.join('third_party', 'mediapipe', 'hand_landmarker.task'))
        options = mp_vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
        self.hand_detector = mp_vision.HandLandmarker.create_from_options(options)

    def detect_hands(self, color_image):
        cv2.imwrite(f'detect_hand.png', color_image)
        #cv2.imshow(f'detect_hand.png', color_image)
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=color_image)
        #mp_image = mp.Image.create_from_file(f'detect_hand.png')
        
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

    def get_processed_frame(self, use_larger_context=True, crop_left = 500, crop_right=600, crop_bottom=100, crop_top=400):
        while True:
            frames = self.pipe.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())

            height, width = color_image.shape[:2]

            cropped_image = color_image[crop_top:(height - crop_bottom), crop_left:(width - crop_right)]
            cropped_image = cropped_image.astype(np.uint8)

            warped_image = apply_perspective_transform(color_image, self.corners)

            if self.detect_hands(cropped_image):
                self.stable_frame_count = 0  # Reset stability count if hands detected
                time.sleep(1)  # Wait before next frame capture
                continue

            warped_image_gray = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)

            # Choose the image to use for stability check
            check_image =  cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY) if use_larger_context else warped_image_gray

            if self.last_stable_frame is not None:
                # Use SSIM to compare current frame with the last stable frame
                similarity = ssim(check_image, self.last_stable_frame)

                if similarity > self.stability_ssim_threshold:
                    self.stable_frame_count += 1
                    time.sleep(0.15)
                else:
                    print('Frame not stable')
                    self.stable_frame_count = 0  # Reset count if frames are not similar enough

            self.last_stable_frame = check_image

            cv2.imshow('Warped Image', warped_image_gray)

            if self.stable_frame_count >= self.stability_threshold:
                break  # Exit loop if stability threshold reached

        return warped_image_gray  # Return the grayscale warped image


    def sample_board(self, max_samples=5, baseline_samples=2):
        sample_number = 0
        self.previous_frames = []
        while sample_number < max_samples:
            frame = self.get_processed_frame()
            if frame is not None:
                sample_number += 1
                self.previous_frames.append(frame)
                time.sleep(0.01)

        baseline_number = 0
        self.baseline_frames = []
        while baseline_number < baseline_samples:
            frame = self.get_processed_frame()
            if frame is not None:
                baseline_number += 1
                self.baseline_frames.append(frame)
                time.sleep(0.01)

        frames_as_squares = [[] for _ in range(64)]
        for frame in self.previous_frames:
            squares = divide_into_squares(frame, extended=self.extended)
            for j, square in enumerate(squares):
                frames_as_squares[j].append(square)

        self.old_squares = frames_as_squares
        self.calculate_baseline_thresholds()



    def calculate_baseline_thresholds(self):
        print("Computing baseline")
        self.baseline_thresholds = {'overall': {}, 'sections': {'center': {}, 'left': {}, 'right': {}, 'top': {}, 'bottom': {}}}

        # Preprocess to divide frames into squares and sections only once
        baseline_squares_list = [divide_into_squares(frame, extended=self.extended) for frame in self.baseline_frames]
        sample_squares_list = [divide_into_squares(frame, extended=self.extended) for frame in self.previous_frames]

        fig, axs = plt.subplots(8, 8, figsize=(10, 10))
        for i, ax in enumerate(axs.flatten()):
            ax.imshow(baseline_squares_list[0][i], cmap='gray')
            ax.axis('off')
            print(i)
        plt.tight_layout()
        plt.savefig('grid_separated.png', dpi=300, bbox_inches='tight')

        num_squares = len(baseline_squares_list[0])

        for idx in range(num_squares):
            overall_diffs, section_diffs = [], {'center': [], 'left': [], 'right': [], 'top': [], 'bottom': []}

            for baseline_square in [squares[idx] for squares in baseline_squares_list]:
                baseline_sections = split_into_sections(baseline_square)

                for sample_square in [squares[idx] for squares in sample_squares_list]:
                    sample_sections = split_into_sections(sample_square)

                    # Calculate overall SSIM
                    overall_score, _ = ssim(baseline_square, sample_square, full=True)
                    overall_diffs.append( (1 - overall_score)*100)

                    # Calculate section SSIMs
                    for section in section_diffs.keys():
                        section_score, _ = ssim(baseline_sections[section], sample_sections[section], full=True)
                        section_diffs[section].append((1 - section_score)*100)

            # Calculate metrics for overall and section differences
            self.baseline_thresholds['overall'][idx] = calculate_threshold_metrics(overall_diffs)
            for section in section_diffs:
                self.baseline_thresholds['sections'][section][idx] = calculate_threshold_metrics(section_diffs[section])


    def get_relevant_squares(self, board):
        """Get squares relevant to the current turn."""
        relevant_squares = set()
        for move in board.legal_moves:
            if board.color_at(move.from_square) == board.turn:
                relevant_squares.add(chess_square_to_camera_perspective(move.from_square))
                relevant_squares.add(chess_square_to_camera_perspective(move.to_square))

        return relevant_squares
    
    ##################
    # MOVE DETECTION #
    ##################

    def compare_squares(self, board):
        self.frame = self.get_processed_frame()
        ssim_squares = self.ssim_square(board)
        detailed_squares = self.ssim_small(ssim_squares)
        return detailed_squares

    def ssim_square(self, board):
        relevant_squares = self.get_relevant_squares(board)
        new_squares = divide_into_squares(self.frame, extended=self.extended)

        square_diffs = []
        for idx in relevant_squares:
            new = new_squares[idx]
            if new is not None:
                diffs = []
                for old_sample in self.old_squares[idx]:
                    if old_sample is not None:
                        score, _ = ssim(old_sample, new, full=True)
                        diff = (1 - score) * 100
                        diffs.append(diff)

                avg_diff = sum(diffs) / len(diffs) if diffs else 0
                square_diffs.append((idx, avg_diff))

        self._update_heatmap(square_diffs, avg_diff)

        # Sort and filter based on overall changes
        square_diffs.sort(key=lambda x: x[1], reverse=True)
        #return [(idx, avg_diff) for idx, avg_diff in square_diffs if (avg_diff > self.large_threshold)]

        return [(idx, avg_diff) for idx, avg_diff in square_diffs if avg_diff > self.baseline_thresholds['overall'][idx]['estimated_max'] and avg_diff > self.large_threshold ]

    def ssim_small(self, squares, detailed_threshold=6):
        new_squares = divide_into_squares(self.frame, extended=self.extended)

        detailed_square_diffs = []
        added_indices = set()  # To keep track of added square indices

        for idx, avg_diff in squares[:detailed_threshold]:
            new = new_squares[idx]
            new_sections = split_into_sections(new)
            # Visualize the sections
            diffs = {'center': 0, 'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
            for old_sample in self.old_squares[idx]:
                if old_sample is not None:
                    old_sections = split_into_sections(old_sample)
                    for section in new_sections:
                        score, _ = ssim(old_sections[section], new_sections[section], full=True)
                        diff = (1 - score) * 100
                        diffs[section] += diff
            avg_diffs = {section: diffs[section] / len(self.old_squares[idx]) for section in diffs}
            # Only append if the max difference is larger than the small threshold
            #if max(avg_diffs.values()) > self.small_threshold:
            #    detailed_square_diffs.append((idx, avg_diff, avg_diffs))

            center_exceeds_threshold = avg_diffs['center'] > self.baseline_thresholds['sections']['center'][idx]['estimated_max']
            right_exceeds_threshold = avg_diffs['right'] > self.baseline_thresholds['sections']['right'][idx]['median']
            left_exceeds_threshold = avg_diffs['left'] > self.baseline_thresholds['sections']['left'][idx]['median']
            top_exceeds_threshold = avg_diffs['top'] > self.baseline_thresholds['sections']['top'][idx]['median']
            bottom_exceeds_threshold = avg_diffs['bottom'] > self.baseline_thresholds['sections']['bottom'][idx]['median']

            #########################################################################################
            # THIS SHOULD BE TESTED MORE, PROBABLY ADDING SOME ML THAT LEARNS IT WOULD BE BETTER
            #########################################################################################
                
            # Determine the condition to append the square or its right neighbor to detailed_square_diffs
            if center_exceeds_threshold:
                detailed_square_diffs.append((idx, avg_diff, avg_diffs))
                added_indices.add(idx)
            elif right_exceeds_threshold and not left_exceeds_threshold:
                # Append the right adjacent square index if available, considering board limits
                right_idx = self._get_right_adjacent_square_index(idx)
                if right_idx is not None and right_idx not in added_indices:
                    detailed_square_diffs.append((right_idx, avg_diff, avg_diffs))

        self._update_detailed_heatmap(detailed_square_diffs)

        return detailed_square_diffs
    

    def _get_right_adjacent_square_index(self, current_idx):
        # Calculate the right adjacent square index based on current index and board dimensions
        # Assuming standard 8x8 chess board and idx starting from 0 at the top left square
        # You might need to adjust this based on how your board is represented
        row_size = 8  # Typically, a chess board row has 8 squares
        if (current_idx + 1) % row_size != 0:  # Not on the right edge
            return current_idx + 1  # The right adjacent square
        else:
            return None  # Right edge, no adjacent square to the right
        
    def recognize_move(self, board):
        # Get the squares that have changed along with their details
        changed_squares_with_details = self.compare_squares(board)

        if len(changed_squares_with_details) == 0:
            return None
        
        #self._update_detailed_heatmap(changed_squares_with_details)

        # Calculate scores for each square based on detailed section differences
        #square_scores = {}
        #for idx, _, section_diffs in changed_squares_with_details:
        #    left_idx = idx - 1 if idx % 8 != 0 else None  # Get the left square index if it exists
        #    left_diffs = next((details for idy, _, details in changed_squares_with_details if idy == left_idx), None) if left_idx is not None else None
        #    score = section_diffs['center'] + section_diffs['right']
        #    if left_diffs:
        #        score += left_diffs['left']
        #    square_scores[idx] = score

        square_scores = {}
        for idx, _, section_diffs in changed_squares_with_details:
            right_idx = idx + 1 if idx % 8 != 7 else None  # Get the right square index if it exists
            right_diffs = next((details for idy, _, details in changed_squares_with_details if idy == right_idx), None) if right_idx is not None else None

            score = section_diffs['center'] + section_diffs['left']
            if right_diffs:
                score += right_diffs['right']
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
                    promotion_move = chess.Move.from_uci(f"{index_to_algebraic(from_sq)}{index_to_algebraic(to_sq)}q")
                    if move in board.legal_moves:
                        legal_moves.append((move, from_score + to_score))
                        if board.is_castling(move):
                            castling_moves.append((move, from_score + to_score))
                    elif promotion_move in board.legal_moves:
                        legal_moves.append((promotion_move, from_score + to_score))

        # Check for castling
        if board.has_castling_rights(board.turn):
            square_scores = {idx: sum(section_diffs.values()) for idx, _, section_diffs in changed_squares_with_details}
            kingside_squares = [algebraic_to_index('e1'), algebraic_to_index('f1'), algebraic_to_index('g1'), algebraic_to_index('h1') ] if board.turn == chess.WHITE else [algebraic_to_index('e8'), algebraic_to_index('f8'), algebraic_to_index('g8'), algebraic_to_index('h8') ]
            queenside_squares = [algebraic_to_index('e1'), algebraic_to_index('d1'), algebraic_to_index('c1'), algebraic_to_index('a1')] if board.turn == chess.WHITE else [algebraic_to_index('e8'), algebraic_to_index('d8'), algebraic_to_index('c8'), algebraic_to_index('a8')]
            
            kingside_move = chess.Move.from_uci("e1g1" if board.turn == chess.WHITE else "e8g8")
            queenside_move = chess.Move.from_uci("e1c1" if board.turn == chess.WHITE else "e8c8")

            if all(square_scores.get(sq, 0) > 25 for sq in kingside_squares) and kingside_move in board.legal_moves:
                self.correct_moves += 1
                self.add_to_history(self.frame, self.previous_frames, self.heatmap.get_array(), self.detailed_heatmap_data)
                return kingside_move
            if all(square_scores.get(sq, 0) > 25 for sq in queenside_squares) and queenside_move in board.legal_moves:
                self.correct_moves += 1
                self.add_to_history(self.frame, self.previous_frames, self.heatmap.get_array(), self.detailed_heatmap_data)
                return queenside_move

        # Sort moves by their calculated score
        refined_moves = sorted(legal_moves, key=lambda x: x[1], reverse=True)

        if len(refined_moves) == 0:
            return None
        
        if False:
            # Save the movement square and split just for visualization
            from_square_idx = refined_moves[0][0].from_square
            to_square_idx = refined_moves[0][0].to_square

            # Save the 'from' square image
            from_square_image = self.old_squares[from_square_idx][-1]
            cv2.imwrite('movement_from_square.png', from_square_image)

            # Save the 'to' square image
            to_square_image = self.old_squares[to_square_idx][-1]
            cv2.imwrite('movement_to_square.png', to_square_image)

            # Save the split sections of the 'from' square
            from_square_sections = split_into_sections(from_square_image)
            for section, img in from_square_sections.items():
                cv2.imwrite(f'movement_from_{section}.png', img)

            # Save the split sections of the 'to' square
            to_square_sections = split_into_sections(to_square_image)
            for section, img in to_square_sections.items():
                cv2.imwrite(f'movement_to_{section}.png', img)

        
        self.correct_moves += 1
        self.add_to_history(self.frame, self.previous_frames, self.heatmap.get_array(), self.detailed_heatmap_data)

        if len(refined_moves) == 1:
            return refined_moves[0][0]
        
        # If refined move difference between first and second is higher than 30, return the first move
        if len(refined_moves) > 1 and refined_moves[0][1] - refined_moves[1][1] > 50:
            return refined_moves[0][0]

        # Return the top 5 moves (if more than one) with the highest score
        return [move for move, _ in refined_moves[:5]]

    ##################
    # GETTER/SETTERS #
    ##################

    def pause_camera(self):
        self.is_active = False

    def resume_camera(self):
        self.is_active = True

    def get_large_threshold(self):
        return self.large_threshold
    
    def set_large_threshold(self, value):
        self.large_threshold = value

    def get_small_threshold(self):
        return self.small_threshold
    
    def set_small_threshold(self, value):
        self.small_threshold = value

    def print_stats(self):
        print("-"*20)
        print(f"Correct moves: {self.correct_moves}")
        print(f"Wrong moves: {self.wrong_moves}")
        print()

    ##############
    # STATISTICS #
    ##############
    
    def add_to_history(self, frame, previous_turn_samples, heatmap_data, detailed_heatmaps):
        if len(self.frame_history) >= self.max_history:
            self.frame_history.pop(0)
        self.frame_history.append((frame, previous_turn_samples, heatmap_data, detailed_heatmaps))

    def archive_wrong_move(self, num_moves_to_pop):
        while num_moves_to_pop > 0 and self.frame_history:
            num_moves_to_pop -= 1

            # Pop the oldest record in the history
            current_frame, previous_turn_samples, main_heatmap_data, detailed_heatmap_data = self.frame_history.pop(0)

            # Create a folder for this wrong move
            wrong_move_folder = os.path.join(self.wrong_moves_folder, f"wrong_move_{time.strftime('%Y%m%d-%H%M%S')}")
            os.makedirs(wrong_move_folder, exist_ok=True)

            # Save the current frame
            cv2.imwrite(os.path.join(wrong_move_folder, "current_frame.jpg"), current_frame)

            # Save the previous turn samples
            for i, prev_frame in enumerate(previous_turn_samples):
                cv2.imwrite(os.path.join(wrong_move_folder, f"prev_turn_sample_{i}.jpg"), prev_frame)

            # Save the combined heatmap
            self.save_combined_heatmap(os.path.join(wrong_move_folder, "combined_heatmap.png"), main_heatmap_data, detailed_heatmap_data)

            # Update wrong moves count
        self.wrong_moves += 1
        self.correct_moves -= 1
        self.print_stats()

    def save_combined_heatmap(self, filename, main_heatmap_data, detailed_heatmap_data):
        # Create a figure with GridSpec layout
        fig = plt.figure(figsize=(15, 10))
        gs = gridspec.GridSpec(2, 4, width_ratios=[1, 1, 1, 0.05])

        # Create main heatmap subplot
        ax_main = plt.subplot(gs[0, 0])
        ax_main.imshow(main_heatmap_data, interpolation='nearest', vmin=0, vmax=50, cmap='jet')
        ax_main.set_title("Main Heatmap")
        ax_main.set_xticks(range(8))
        ax_main.set_yticks(range(8))

        # Create detailed heatmaps based on positions used in _init_heatmaps
        detailed_heatmap_positions = {
            'center': (0, 1), 'top': (0, 2), 
            'left': (1, 0), 'right': (1, 1), 'bottom': (1, 2)
        }

        for section, pos in detailed_heatmap_positions.items():
            ax = plt.subplot(gs[pos])
            ax.imshow(detailed_heatmap_data[section], interpolation='nearest', vmin=0, vmax=50, cmap='jet')
            ax.set_title(section.capitalize())
            ax.set_xticks(range(8))
            ax.set_yticks(range(8))

            ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
            ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])

        # Add colorbar
        cb_ax = plt.subplot(gs[:, -1])
        plt.colorbar(ax_main.get_images()[0], cax=cb_ax)

        # Save the figure
        plt.tight_layout()
        plt.savefig(filename)
        plt.close(fig)