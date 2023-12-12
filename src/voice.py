import whisper
import os
import chess
import re
# https://lichess.org/@/schlawg/blog/how-to-lichess-voice/nWrypoWI

def is_valid_chess_move(board, move_str):
    try:
        move = board.parse_san(move_str)
        if move in board.legal_moves:
            return move
    except ValueError:
        pass
    return None

def process_moves(moves):
    board = chess.Board()
    for move_str in moves:
        cleaned_move = clean_transcription(move_str)
        move = is_valid_chess_move(board, cleaned_move)
        if move:
            uci_move = move.uci()
            print(f"Valid move: {cleaned_move} -> UCI: {uci_move}")
            board.push(move)
        else:
            print(f"Invalid move, please clarify: {move_str}")

def sort_key(file):
    number = re.search(r'\d+', file)
    if number:
        return int(number.group())
    return file

def clean_transcription(move_str):
    move_str = move_str.strip().lower()
    
    # Replacements for common transcription errors
    replacements = {
        'nite': 'N', 'night': 'N', 'knight': 'N',
        'bishop': 'B', 'rook': 'R', 'ruke': 'R', 'ruk': 'R',
        'queen': 'Q', 'king': 'K', 'castles': 'O-O', 'castle': 'O-O',
        'detakes': 'dxe', 'takes': 'x', 'provide': '', 'and': '',
        'a.e.8': 'a8', 'a.b.5': 'a5', 'r.e.1': 're1', 'r.e.i': 're1',
        'b.e.7': 'be7', 'b.e.3': 'be3', 'c.e.6': 'ce6', 'd.e.4': 'de4', 'e.e.2': 'ee2',
        'h.e.1': 'he1', 'g.e.1': 'ge1', 'f.e.4': 'fe4', 'b.e.2': 'be2',
        'night-f-3': 'Nf3', 'night c6': 'Nc6', 'night f6': 'Nf6', 'night bd2': 'Nbd2',
        'night h5': 'Nh5', 'night c4': 'Nc4', 'night a3': 'Na3', 'night f3': 'Nf3',
        'night g6': 'Ng6', 'be for': 'Bf4', '9g5': 'Ng5', 'live night e7': 'Nxe7',
        '9g4': 'Ng4', 'white resigns': '', '27': '', 'see you': '',
        'd takes e4': 'dxe4', 'g takes f4': 'gxf4', 'queen takes f4': 'Qxf4',
        'queen takes e4': 'Qxe4', '8 takes b5': 'axb5', '8xb5': 'axb5',
        'ruke-e i': 'Re1', 'rook ae1': 'Re1', 'ruke-88': '', 'rok a.e.8': 'Rae8'
    }

    for wrong, right in replacements.items():
        move_str = move_str.replace(wrong, right)

    # Handling pawn moves and captures (e.g., 'e4', 'exd5')
    move_str = re.sub(r'(\d) takes (\w)(\d)', r'\2x\3', move_str) # e.g., '4 takes e5' to '4xe5'
    move_str = re.sub(r'(\d) takes (\w)', r'\2x', move_str) # e.g., '4 takes e' to '4xe'
    move_str = re.sub(r'^(\w)(\d)$', r'\1\2', move_str) # e.g., 'e 4' to 'e4'

    # Special case for castling (king's side and queen's side)
    move_str = move_str.replace("castles king's side", "O-O").replace("castle's king's side", "O-O")
    move_str = move_str.replace("castles queen's side", "O-O-O").replace("castle's queen's side", "O-O-O")

    print(move_str)
    return move_str


# Load Whisper model
model = whisper.load_model("base")

# Read and process audio files
audio_moves = []
for file in sorted(os.listdir("chess_audio_chunks"), key=sort_key):
    if file.endswith(".mp3"):
        audio_file = os.path.join("chess_audio_chunks", file)
        result = model.transcribe(audio_file)
        audio_moves.append(result["text"])

# Process moves
process_moves(audio_moves)
