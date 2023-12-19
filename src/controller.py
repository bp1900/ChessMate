

import chess
import chess.engine
import random
#import whisper
import os
import time
from camera import Camera

################
# CHESS ENGINE #
################

class ChessEngine:
    def __init__(self, engine_path, time_limit=0.5):
        self.engine_path = engine_path
        self.time_limit = time_limit

    def compute_move(self, board):
        with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
            result = engine.play(board, chess.engine.Limit(time=self.time_limit))
            return result.move
        
    def set_time_limit(self, time_limit):
        self.time_limit = time_limit

#################
# CHESS CONTROL #
#################

class ChessController:
    def __init__(self, gui, robot, mode, color, engine_path, time_engine, engine2_path, time_engine2, camera, gripper_test_mode):
        self.board = chess.Board()
        self.gui = gui
        self.robot = robot
        self.engine = ChessEngine(engine_path=engine_path, time_limit=time_engine)
        self.engine2 = ChessEngine(engine_path=engine2_path, time_limit=time_engine2)

        self.GRIPPER_TEST_MODE = gripper_test_mode
        if camera:
            max_history = 1 if mode == "human-human" else 2
            self.camera = Camera(max_history=max_history)
        else:
            self.camera = None
        self.check_camera_interval = 1000

        self.turn = chess.WHITE

        self.game_mode = mode
        self.player_color = color

        self.robot_movement = False
        self.in_correction_mode = False

    ##################
    # MOVE HANDLER   #
    ##################

    def handle_move(self, move):
        """Process and apply a move from any source."""

        # Obtain the current piece
        current_piece = self.board.piece_at(move.from_square)

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

            if self.robot_movement:
                
                if captured_piece is not None and captured_piece.piece_type == chess.KING:
                    self.send_move_robot(move, is_checkmate=True)     

                else:
                
                    if captured_piece:
                        self.send_capture_robot(move, captured_piece)
                    
                    if is_castling_move:
                        self.handle_castling_robot(move)
                    else:
                        self.send_move_robot(move)
                    
                    if self.game_mode == "engine-engine":
                        self.gui.root.after(100, self.get_engine_move)

            elif self.game_mode == "human-engine": 
                self.get_engine_move()

            if self.board.is_checkmate():

                color_current_piece = current_piece.color
                if color_current_piece == chess.WHITE:
                    king_square_index = self.board.king(chess.BLACK)
                else:
                    king_square_index = self.board.king(chess.WHITE)

                king_square_name = chess.square_name(king_square_index)

                move_kill = chess.Move(move.to_square, chess.parse_square(king_square_name))

                self.send_move_robot(move_kill, is_checkmate=True)
            
            self.turn = not self.turn

            if self.camera and not self.in_correction_mode:
                if self.game_mode == "human-engine" or self.game_mode == "human-human":
                    self.camera.sample_board('previous_turn')

        else:
            print("Illegal move!")

    ##########################
    # GAME UTILITY FUNCTIONS #
    ##########################

    def is_move_legal(self, move):
        """Check if a move is legal."""
        return move in self.board.legal_moves
    
    def is_pawn_promotion_candidate(self, move):
        piece = self.board.piece_at(move.from_square)
        return piece is not None and (piece.piece_type == chess.PAWN) and \
            ((piece.color == chess.WHITE and move.from_square in chess.SquareSet(chess.BB_RANK_7) and move.to_square in chess.SquareSet(chess.BB_RANK_8)) or \
            (piece.color == chess.BLACK and move.from_square in chess.SquareSet(chess.BB_RANK_2) and move.to_square in chess.SquareSet(chess.BB_RANK_1)))
    
    ##################
    # GAME LOOP CTRL #
    ##################

    def start_game_loop(self):
        if self.camera:
            self.check_for_camera_move()

        if self.game_mode == "human-engine" and self.player_color == chess.BLACK:
            self.get_engine_move()
        elif self.game_mode == "engine-engine":
            self.get_engine_move()
    
    def get_engine_move(self):
        if self.game_mode == "human-engine" and self.player_color != self.board.turn:
            self.robot_movement = True
            engine_move = self.engine.compute_move(self.board)
            self.handle_move(engine_move)
        elif self.game_mode == "engine-engine":
            self.robot_movement = True
            if self.turn:
                engine_move = self.engine.compute_move(self.board)
            else:
                engine_move = self.engine2.compute_move(self.board)

            self.handle_move(engine_move)
    
    ##################
    # CAMERA CONTROL #
    ##################

    def check_for_camera_move(self):
        """Check for a move made via the camera."""
        if self.in_correction_mode:
            return
        print('Checking for camera move')
        camera_move = self.camera.recognize_move(self.board, self.turn)
        if camera_move:
            # Check if camera move returned one or multiple moves
            if isinstance(camera_move, list):
                # Display possible moves in GUI for user selection
                self.gui.display_possible_moves(camera_move)
            else:
                self.handle_move(camera_move)
        self.gui.root.after(self.check_camera_interval, self.check_for_camera_move)

    ########################
    # RESETTING / MISTAKES #
    ########################
    
    def reset_board(self):
        self.board.reset()
        self.gui.update_display(self.board.fen())
        self.turn = chess.WHITE

        if self.game_mode == "human-engine" and self.player_color == chess.BLACK:
            self.robot_movement = True
            self.get_engine_move()
        else:
            self.robot_movement = False

        if self.camera:
            self.camera.sample_board('previous_turn')

    def handle_wrong_move(self):
        # Determine whose turn it is currently
        current_turn = self.board.turn

        # If it's the robot's (engine's) turn, pop only the last move
        # If it's the human's turn again, pop two moves (human's and engine's)
        num_moves_to_pop = 2 if self.game_mode == "human-engine" else 1

        for _ in range(num_moves_to_pop):
            self.board.pop()

        self.gui.update_display(self.board.fen())
        self.in_correction_mode = True
        self.camera.archive_wrong_move(num_moves_to_pop)

    def exit_correction_mode(self):
        self.in_correction_mode = False
        self.turn = self.board.turn

        if self.camera:
            # Sample the board for the previous turn, effectively resetting the detection state
            self.camera.sample_board('previous_turn')
            # Continue checking for camera moves after a delay
            self.gui.root.after(self.check_camera_interval, self.check_for_camera_move)

        if self.game_mode == "human-engine" and not self.board.turn != self.player_color:
            # If it's the robot's turn after exiting correction mode, get the engine's move
            self.robot_movement = True
            self.get_engine_move()

    ############
    # CASTLING #
    ############
    
    def handle_castling_robot(self, move):
        king_to_square, rook_to_square = self.create_castling_squares(move)

        self.send_move_robot(king_to_square)
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

    def send_move_robot(self, move, is_checkmate=False):
        """Send the move to the robotic arm."""

        print(f'[ROBOT - PIECE MOVEMENT]: {move}')
        if not self.GRIPPER_TEST_MODE:
            self.robot.move_piece(move, checkmate=is_checkmate)

        # Notify the robotic arm to move turn has finished
        self.robot_movement = False

    def send_capture_robot(self, move, captured_piece, is_checkmate=False):
        """Send the capture move to the robotic arm."""
        square_name = chess.square_name(move.to_square)
        print(f'[ROBOT - CAPTURED PIECE {captured_piece} AT]: {square_name}')

        if not self.GRIPPER_TEST_MODE:
            self.robot.capture_piece(move, is_checkmate)