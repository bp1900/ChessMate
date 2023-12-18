

import chess
import chess.engine
import random
#import whisper
import os
import time
from camera import Camera

class ChessEngine:
    def __init__(self, engine_path, ):
        self.engine_path = engine_path

    def compute_move(self, board, time=0.5):
        with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
            result = engine.play(board, chess.engine.Limit(time=time))
            return result.move

class ChessController:
    def __init__(self, gui, robot, mode, color, engine_path=r'C:\Users\sonia.rabanaque\Desktop\ChessPlayer\third_party\stockfish\stockfish-windows-x86-64-avx2.exe'):
        self.board = chess.Board()
        self.gui = gui
        self.robot = robot
        self.engine = ChessEngine(engine_path=engine_path)
        self.camera = Camera()
        self.check_camera_interval = 1000

        self.turn = chess.WHITE

        self.game_mode = mode
        self.player_color = color

        self.robot_movement = False

    def check_for_camera_move(self):
        """Check for a move made via the camera."""
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

    def handle_move(self, move):
        """Process and apply a move from any source."""

        current_piece = self.board.piece_at(move.from_square)

        if not self.robot_movement and self.is_pawn_promotion_candidate(move):
            self.gui.ask_promotion_piece()
            move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)

        if self.is_move_legal(move):
        #if True:
            # Check for captured
            captured_piece = self.board.piece_at(move.to_square) if self.board.is_capture(move) else None

            # Check for castling
            is_castling_move = self.board.is_castling(move)

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
                        self.gui.root.after(100, self.check_and_make_engine_move)

            elif self.game_mode == "human-engine": # not so sure about this
                print('Robot Turn:')
                self.check_and_make_engine_move()
                print()
                print('Human Turn:')

            is_checkmate = self.board.is_check() #  self.board.is_checkmate()
            if is_checkmate:

                color_current_piece = current_piece.color
                if color_current_piece == chess.WHITE:
                    king_square_index = self.board.king(chess.BLACK)
                else:
                    king_square_index = self.board.king(chess.WHITE)

                king_square_name = chess.square_name(king_square_index)

                move_kill = chess.Move(move.to_square, chess.parse_square(king_square_name))

                self.send_move_robot(move_kill, is_checkmate=True)

            
            self.turn = not self.turn
            self.camera.sample_board('previous_turn')

        else:
            print("Illegal move!")

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

    def is_move_legal(self, move):
        """Check if a move is legal."""
        return move in self.board.legal_moves

    def is_pawn_promotion_candidate(self, move):
        piece = self.board.piece_at(move.from_square)
        return piece is not None and (piece.piece_type == chess.PAWN) and \
            ((piece.color == chess.WHITE and move.from_square in chess.SquareSet(chess.BB_RANK_7) and move.to_square in chess.SquareSet(chess.BB_RANK_8)) or \
            (piece.color == chess.BLACK and move.from_square in chess.SquareSet(chess.BB_RANK_2) and move.to_square in chess.SquareSet(chess.BB_RANK_1)))
    
    def check_and_make_engine_move(self):
        """Make the engine's move in human-engine mode."""
        if self.game_mode == "human-engine" and self.player_color != self.board.turn:
            self.robot_movement = True
            engine_move = self.engine.compute_move(self.board)
            self.handle_move(engine_move)
        elif self.game_mode == "engine-engine":
            self.robot_movement = True
            engine_move = self.engine.compute_move(self.board)
            self.handle_move(engine_move)

    def reset_board(self):
        self.board.reset()
        self.gui.update_display(self.board.fen())
        
    def modify_game_mode(self, mode, player_color=chess.WHITE):
        """Modify the game mode."""
        self.game_mode = mode
        self.player_color = player_color

    def start_game_loop(self):
        self.check_for_camera_move()
        if self.game_mode == "human-engine" and self.player_color == chess.BLACK:
            self.check_and_make_engine_move()
        elif self.game_mode == "engine-engine":
            self.check_and_make_engine_move()

    def handle_wrong_move(self):
        # Reverts the last move
        self.board.pop()
        self.gui.update_display(self.board.fen())
        
        if self.game_mode == "human-engine" or self.game_mode == "human-human":
            self.check_and_make_engine_move()

    def piece_to_verbose(self, piece):
        """Convert a chess.Piece to a verbose string."""
        if not piece:
            return "None"
        
        color = "white" if piece.color == chess.WHITE else "black"
        piece_type = piece.piece_type
        piece_name = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king"
        }.get(piece_type, "unknown")

        return f"{color} {piece_name}"
    
    #############################
    # Robotic arm communication #
    #############################

    def send_move_robot(self, move, is_checkmate=False):
        """Send the move to the robotic arm."""

        print(f'[ROBOT - PIECE MOVEMENT]: {move}')
        self.robot.move_piece(move, checkmate=is_checkmate)

        # Notify the robotic arm to move turn has finished
        self.robot_movement = False

    def send_capture_robot(self, move, captured_piece, is_checkmate=False):
        """Send the capture move to the robotic arm."""
        square_name = chess.square_name(move.to_square)
        verbose_piece = self.piece_to_verbose(captured_piece)
        print(f'[ROBOT - CAPTURED PIECE {verbose_piece} AT]: {square_name}')
        self.robot.capture_piece(move, is_checkmate)