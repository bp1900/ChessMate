import chess
import chess.engine
import random

def get_user_move():
    """Retrieve and return a move from the user."""
    move = input("Enter your chess move (e.g., 'e2e4'): ")
    return move

def get_random_legal_move(board):
    """Retrieve a random legal move."""
    return random.choice([move.uci() for move in board.legal_moves])

def process_move(board, move):
    """Validate and apply the move to the board."""
    try:
        chess_move = chess.Move.from_uci(move)
        if chess_move in board.legal_moves:
            board.push(chess_move)
            return True
        else:
            print("Illegal move!")
            return False
    except ValueError:
        print("Invalid move format!")
        return False

def compute_engine_move(board):
    """Compute and return the best move using a chess engine."""
    with chess.engine.SimpleEngine.popen_uci("third_party/stockfish/stockfish-ubuntu-x86-64-avx2") as engine:
        result = engine.play(board, chess.engine.Limit(time=2.0))
        best_move = result.move
        return best_move

def get_board_evaluation(board):
    """Get the board evaluation in centipawns."""
    with chess.engine.SimpleEngine.popen_uci("third_party/stockfish/stockfish-ubuntu-x86-64-avx2") as engine:
        evaluation = engine.analyse(board, chess.engine.Limit(time=2.0))
        score = evaluation['score'].relative.score()
        return score

def main():
    board = chess.Board()
    while not board.is_game_over():
        print(board)
        
        #user_move = get_user_move()
        user_move = get_random_legal_move(board)
        if process_move(board, user_move):
            print("You played:", user_move)
            eval_score = get_board_evaluation(board)
            print("Evaluation after your move: {} (Positive for White, Negative for Black)".format(eval_score))
            
            engine_move = compute_engine_move(board)
            board.push(engine_move)
            print("Engine played:", engine_move.uci())
            eval_score = get_board_evaluation(board)
            print("Evaluation after engine's move: {} (Positive for White, Negative for Black)".format(eval_score))
        else:
            print("Please make a valid move.")

if __name__ == "__main__":
    main()
