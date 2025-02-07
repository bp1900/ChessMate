
import chess
import time
import threading
from camera import Camera
import tkinter as tk
from transcriber import Transcriber, generate_text_from_transcription
import subprocess
import os

#################
# CHESS CONTROL #
#################

class ChessController(threading.Thread):
    def __init__(self, gui, robot, mode, color, engine, engine2, camera, gripper_test_mode):
        self.board = chess.Board()
        self.gui = gui
        self.robot = robot
        self.engine = engine
        self.engine2 = engine2

        self.GRIPPER_TEST_MODE = gripper_test_mode

        self.game_mode = mode
        self.player_color = color

        self.robot_movement = False
        self.in_correction_mode = False

        self.check_camera_interval = 1000
        self.camera = camera

    ##################
    # MOVE HANDLER   #
    ##################

    def handle_move(self, move):
        """Process and apply a move from any source."""

        # Obtain the current piece
        current_piece = self.board.piece_at(move.from_square)
        current_is_pawn = (current_piece is not None and current_piece.piece_type == chess.PAWN)

        # If the robot/engine is not moving, and its possible to promote a pawn, ask the user for the promotion piece
        if not self.robot_movement and self.is_pawn_promotion_candidate(move):
            promotion = self.gui.ask_promotion_piece()
            move = chess.Move(move.from_square, move.to_square, promotion=promotion)

        if self.is_move_legal(move):
            # Check for captured
            captured_piece = self.board.piece_at(move.to_square) if self.board.is_capture(move) else None

            # Check for castling
            is_castling_move = self.board.is_castling(move)

            # Make the move and update the GUI
            self.board.push(move)
            self.gui.update_display(self.board.fen(), last_move=move)
            
            if self.game_mode == "human-engine" and self.player_color != self.board.turn:
                self.gui.root.after(100, self.async_engine_move)

            if self.robot_movement:

                if captured_piece is not None and captured_piece.piece_type == chess.KING:
                    self.send_move_robot(move, is_checkmate=True, return_initial_position=False, is_pawn=current_is_pawn)

                else:
                    if captured_piece:
                        captured_is_pawn = (captured_piece.piece_type == chess.PAWN)
                        self.send_capture_robot(move, captured_piece, is_pawn=captured_is_pawn)
                    
                    if is_castling_move:
                        self.handle_castling_robot(move)
                    else:
                        self.send_move_robot(move, is_pawn=current_is_pawn)
                    
                    # After making the human move, check if it's the engine's turn
                    if self.game_mode == "engine-engine":
                        self.gui.root.after(100, self.async_engine_move)

            if self.board.is_checkmate():

                color_current_piece = current_piece.color
                if color_current_piece == chess.WHITE:
                    king_square_index = self.board.king(chess.BLACK)
                else:
                    king_square_index = self.board.king(chess.WHITE)

                king_square_name = chess.square_name(king_square_index)

                move_kill = chess.Move(move.to_square, chess.parse_square(king_square_name))

                self.send_move_robot(move_kill, is_checkmate=True, is_pawn=current_is_pawn)
            
            if self.camera and not self.in_correction_mode:
                if self.game_mode == "human-human":
                    self.camera.sample_board()
                    self.camera.print_stats()
 
                elif self.game_mode == "human-engine":
                    self.camera.sample_board()
                    self.camera.print_stats()

        else:
            print("Illegal move!")

    def get_engine_move(self):
        if self.board.is_game_over():
            return

        self.robot_movement = True
        if self.game_mode == "human-engine" and self.player_color != self.board.turn:
            engine_move = self.engine.compute_move(self.board)
        elif self.board.turn == chess.WHITE:
            engine_move = self.engine.compute_move(self.board)
        else:
            engine_move = self.engine2.compute_move(self.board)

        self.handle_move(engine_move)

    def async_engine_move(self):
        if self.board.is_game_over():
            return

        self.robot_movement = True
        def compute_and_handle_move():
            if self.game_mode == "human-engine" and self.player_color != self.board.turn:
                engine_move = self.engine.compute_move(self.board)
            elif self.board.turn == chess.WHITE:
                engine_move = self.engine.compute_move(self.board)
            else:
                engine_move = self.engine2.compute_move(self.board)

            self.gui.root.after(0, lambda: self.handle_move(engine_move))

        threading.Thread(target=compute_and_handle_move).start()

    def start_game_loop(self):
        """Start the game loop."""
        if self.game_mode == "engine-engine":
            self.async_engine_move()
        elif self.game_mode == "human-engine" and self.player_color == chess.BLACK:
            self.async_engine_move()
        
    ##########################
    # GAME UTILITY FUNCTIONS #
    ##########################

    def is_move_legal(self, move):
        return move in self.board.legal_moves
    
    def is_pawn_promotion_candidate(self, move):
        piece = self.board.piece_at(move.from_square)
        return piece is not None and (piece.piece_type == chess.PAWN) and \
            ((piece.color == chess.WHITE and move.from_square in chess.SquareSet(chess.BB_RANK_7) and move.to_square in chess.SquareSet(chess.BB_RANK_8)) or \
            (piece.color == chess.BLACK and move.from_square in chess.SquareSet(chess.BB_RANK_2) and move.to_square in chess.SquareSet(chess.BB_RANK_1)))
    
    ########################
    # RESETTING / MISTAKES #
    ########################
    
    def reset_board(self):
        self.board.reset()
        self.gui.update_display(self.board.fen())

        if self.game_mode == "human-engine" and self.player_color == chess.BLACK:
            self.robot_movement = True
            self.async_engine_move()
        else:
            self.robot_movement = False

        if self.camera:
            self.camera.sample_board()

    def handle_wrong_move(self):
        # If it's the robot's (engine's) turn, pop only the last move
        # If it's the human's turn again, pop two moves (human's and engine's)
        num_moves_to_pop = 1 if self.board.turn != self.player_color else 2

        for _ in range(num_moves_to_pop):
            self.board.pop()

        self.gui.update_display(self.board.fen())
        self.in_correction_mode = True

        if self.camera is not None:
            self.camera.archive_wrong_move(num_moves_to_pop)
            self.camera.sample_board()

    def exit_correction_mode(self):
        self.in_correction_mode = False

        if self.camera:
            # Sample the board for the previous turn, effectively resetting the detection state
            self.camera.sample_board()

        if self.game_mode == "human-engine" and not self.board.turn != self.player_color:
            # If it's the robot's turn after exiting correction mode, get the engine's move
            self.robot_movement = True
            self.async_engine_move()

    ############
    # CASTLING #
    ############
    
    def handle_castling_robot(self, move):
        king_to_square, rook_to_square = self.create_castling_squares(move)

        self.send_move_robot(king_to_square, return_initial_position=False)
        self.send_move_robot(rook_to_square)

    def create_castling_squares(self, move):
        king_from = move.from_square
        king_to = move.to_square
        rook_from = move.to_square + 1 if move.to_square > move.from_square else move.to_square - 2
        rook_to = move.to_square - 1 if move.to_square > move.from_square else move.to_square + 1

        king_move = chess.Move(king_from, king_to)
        rook_move = chess.Move(rook_from, rook_to)

        return king_move, rook_move
    
    #############################
    # Robotic arm communication #
    #############################

    def send_move_robot(self, move, return_initial_position=True, is_checkmate=False, is_pawn=False):
        """Send the move to the robotic arm."""

        print(f'[ROBOT - PIECE MOVEMENT]: {move}')
        if not self.GRIPPER_TEST_MODE:
            self.robot.move_piece(move, return_initial_position=return_initial_position, checkmate=is_checkmate, is_pawn=is_pawn)

        # Notify the robotic arm to move turn has finished
        self.robot_movement = False

    def send_capture_robot(self, move, captured_piece, is_checkmate=False, is_pawn=False):
        """Send the capture move to the robotic arm."""
        square_name = chess.square_name(move.to_square)
        print(f'[ROBOT - CAPTURED PIECE {captured_piece} AT]: {square_name}')

        if not self.GRIPPER_TEST_MODE:
            self.robot.capture_piece(move, is_checkmate, is_pawn=is_pawn)

class DetectionControllerAudio(threading.Thread):
    def __init__(self, chess_controller, camera, command_queue, mode):
        super().__init__()
        self.chess_controller = chess_controller
        self.command_queue = command_queue
        self.mode = mode

        # Camera related
        self.camera = camera
        self.camera_thread = threading.Thread(target=self.camera_loop, args=())

        # Transcriber related
        self.transcriber = Transcriber()
        self.transcriber_thread = threading.Thread(target=self.transcriber.transcribe, args=("move",))
        self.audio_thread = threading.Thread(target=self.audio_loop, args=())

    def run(self):
        # Start both threads
        self.camera_thread.start()
        self.transcriber_thread.start()
        self.audio_thread.start()

        # Wait for both threads to finish 
        self.camera_thread.join()
        self.transcriber_thread.join()
        self.audio_thread.join()

    def camera_loop(self):
        while True:
            if self.should_detect() and self.camera:
                move = self.camera.recognize_move(self.chess_controller.board)
                if move:
                    self.command_queue.put(move)
            time.sleep(1)  # Modify as needed

    def audio_loop(self):
        while True:
            if self.should_detect() and self.transcriber:
                self.check_transcription()
            time.sleep(1)  # Adjust as needed

    def check_transcription(self):
        if not self.transcriber.transfer_queue.empty():
            transcription = self.transcriber.transfer_queue.get()
            print(f"Transcription: {transcription}")  # Debugging
            possible_moves = generate_text_from_transcription(transcription, self.chess_controller.board.fen())
            # Check if possible moves are legal on the board
            if isinstance(possible_moves, list):
                if len(possible_moves) == 1:
                    if self.chess_controller.is_move_legal(possible_moves[0]):
                        self.chess_controller.robot_movement = True
                        self.command_queue.put(possible_moves[0])
                        return
                else:
                    subset_moves = []
                    for move in possible_moves:
                        if self.chess_controller.is_move_legal(move):
                            self.chess_controller.robot_movement = True # Make the robot arm move
                            subset_moves.append(move)

                    if len(subset_moves) == 1:
                        self.command_queue.put(subset_moves[0])
                        return
                    elif len(subset_moves) > 1:
                        self.chess_controller.gui.display_possible_moves(subset_moves)
                        return
                    
                    
    def start_detection_loop(self):
        # Start the detection loop in a separate thread
        detection_loop_thread = threading.Thread(target=self.run)
        detection_loop_thread.start()

    def should_detect(self):
        if self.chess_controller.board.is_game_over():
            return False

        if self.chess_controller.in_correction_mode:
            return False

        if self.mode == "human-human":
            return True
        elif self.mode == "human-engine":
            return self.chess_controller.board.turn == self.player_color
        return False
    
class DetectionController(threading.Thread):
    def __init__(self, chess_controller, camera, command_queue, mode):
        threading.Thread.__init__(self)
        self.chess_controller = chess_controller
        self.player_color = chess_controller.player_color
        self.command_queue = command_queue
        self.mode = mode
        self.camera = camera

    def run(self):
        time.sleep(0.5)
        if self.mode == "engine-engine":
            self.chess_controller.start_game_loop()
            return  # Do not run detection for engine-engine mode
        elif self.mode == "human-engine" and self.chess_controller.player_color == chess.BLACK:
            self.chess_controller.start_game_loop()
            return

        while True:
            # Check for camera move or other inputs
            if self.should_detect():
                if self.camera:
                    move = self.camera.recognize_move(self.chess_controller.board)
                    if move:
                        # Put the move in the queue instead of directly handling it
                        self.command_queue.put(move)
            time.sleep(1)

    def should_detect(self):
        if self.chess_controller.board.is_game_over():
            return False

        if self.chess_controller.in_correction_mode:
            return False

        if self.mode == "human-human":
            return True
        elif self.mode == "human-engine":
            return self.chess_controller.board.turn == self.player_color
        return False
    
    def start_detection_loop(self):
        # Start the detection loop in a separate thread
        detection_loop_thread = threading.Thread(target=self.run)
        detection_loop_thread.start()