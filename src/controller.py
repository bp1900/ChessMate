
import chess
import chess.engine
import random
#import whisper

class ChessEngine:
    def __init__(self, engine_path, ):
        self.engine_path = engine_path

    def compute_move(self, board, time=0.1):
        with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
            result = engine.play(board, chess.engine.Limit(time=time))
            return result.move

class ChessController:
    def __init__(self, gui, robot, engine_path="third_party/stockfish/stockfish-ubuntu-x86-64-avx2"):
        self.board = chess.Board()
        self.gui = gui
        self.robot = robot
        self.engine = ChessEngine(engine_path=engine_path)

        self.game_mode = "human-human"
        self.player_color = chess.WHITE

        self.robot_movement = False

    def handle_move(self, move):
        """Process and apply a move from any source."""

        if not self.robot_movement and self.is_pawn_promotion_candidate(move):
            self.gui.ask_promotion_piece()
            move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)

        if self.is_move_legal(move):

            captured_piece = self.board.piece_at(move.to_square) if self.board.is_capture(move) else None

            self.board.push(move)
            self.gui.update_display(self.board.fen(), last_move=move, game_status=self.get_game_status_text())

            #self.robot.move_piece(move)

            if self.robot_movement:
                if captured_piece:
                    self.send_capture_robot(move, captured_piece)
                self.send_move_robot(move)
            elif self.game_mode == "human-engine": # not so sure about this
                print('Robot Turn:')
                self.check_and_make_engine_move()
                print()
                print('Human Turn:')
        else:
            print("Illegal move!")

    def is_move_legal(self, move):
        """Check if a move is legal."""
        return move in self.board.legal_moves

    def is_pawn_promotion_candidate(self, move):
        piece = self.board.piece_at(move.from_square)
        return piece is not None and piece.piece_type == chess.PAWN and \
               move.to_square in chess.SquareSet(chess.BB_RANK_1 | chess.BB_RANK_8)
    
    def check_and_make_engine_move(self):
        """Make the engine's move in human-engine mode."""
        if self.game_mode == "human-engine" and self.gui.player_color != self.gui.board.turn:
            self.robot_movement = True
            engine_move = self.engine.compute_move(self.board)
            self.handle_move(engine_move)

    def reset_board(self):
        self.board.reset()
        self.gui.update_display(self.board.fen(), game_status=self.get_game_status_text())

    def get_game_status_text(self):
        """Return the current game status."""
        if self.board.is_checkmate():
            return "Checkmate!"
        elif self.board.is_stalemate():
            return "Stalemate!"
        elif self.board.is_insufficient_material():
            return "Draw due to insufficient material!"
        elif self.board.can_claim_draw():
            return "Draw can be claimed!"
        elif self.board.is_game_over():
            return "Game over!"
        else:
            return ""
        
    def modify_game_mode(self, mode, player_color=chess.WHITE):
        """Modify the game mode."""
        self.game_mode = mode
        self.player_color = player_color

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


