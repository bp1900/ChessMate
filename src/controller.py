

import chess
import chess.engine
import random
#import whisper
import os

class ChessEngine:
    def __init__(self, engine_path, ):
        self.engine_path = engine_path

    def compute_move(self, board, time=0.1):
        with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
            result = engine.play(board, chess.engine.Limit(time=time))
            return result.move

class ChessController:
    def __init__(self, gui, robot, mode, color, engine_path=r'C:\Users\blanca.llaurado\Desktop\ChessPlayer\third_party\stockfish\stockfish-windows-x86-64-avx2.exe'):
        self.board = chess.Board()
        self.gui = gui
        self.robot = robot
        self.engine = ChessEngine(engine_path=engine_path)

        self.game_mode = mode
        self.player_color = color

        self.robot_movement = False

    def handle_move(self, move):
        """Process and apply a move from any source."""

        if not self.robot_movement and self.is_pawn_promotion_candidate(move):
            self.gui.ask_promotion_piece()
            move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)

        if self.is_move_legal(move):
            # Check for captured
            captured_piece = self.board.piece_at(move.to_square) if self.board.is_capture(move) else None

            # Check for castling
            is_castling_move = self.board.is_castling(move)

            self.board.push(move)
            self.gui.update_display(self.board.fen(), last_move=move)

            if True or self.robot_movement:
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

    def start_engine_game(self):
        if self.game_mode == "human-engine" and self.player_color == chess.BLACK:
            self.check_and_make_engine_move()
        elif self.game_mode == "engine-engine":
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

    def send_move_robot(self, move):
        """Send the move to the robotic arm."""

        print(f'[ROBOT - PIECE MOVEMENT]: {move}')
        self.robot.move_piece(move)

        # Notify the robotic arm to move turn has finished
        self.robot_movement = False

    def send_capture_robot(self, move, captured_piece):
        """Send the capture move to the robotic arm."""
        square_name = chess.square_name(move.to_square)
        verbose_piece = self.piece_to_verbose(captured_piece)
        print(f'[ROBOT - CAPTURED PIECE {verbose_piece} AT]: {square_name}')
        self.robot.capture_piece(move)