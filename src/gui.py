import chess
import chess.svg
import tkinter as tk
from PIL import Image, ImageTk
import tkinter.simpledialog
from tkinter import PhotoImage
import cairosvg

class ChessGUI:
    BOARD_SIZE = 2000

    def __init__(self):
        self.board = chess.Board()
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=self.BOARD_SIZE, height=self.BOARD_SIZE)
        self.canvas.pack()
        self.turn_label = tk.Label(self.root, text=self.current_turn_text(), font=("Verdana", 16))
        self.turn_label.pack()
        self.last_move = None
        self.display_board()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.selected_piece = None
        self.source_square = None
        self.highlight_square = None

        self.game_mode = "human-human"  # Default game mode
        self.player_color = chess.WHITE  # Default player color when playing against engine

        # Add a forfeit button
        self.forfeit_button = tk.Button(self.root, text="Forfeit", command=self.handle_forfeit, font=("Verdana", 14))
        self.forfeit_button.pack(pady=10)

        # Add a reset button
        self.reset_button = tk.Button(self.root, text="Reset", command=self.reset_game, font=("Verdana", 14))
        self.reset_button.pack(pady=10)

    def set_controller(self, controller):
        self.controller = controller

    def set_game_mode(self, mode, player_color=chess.WHITE):
        self.controller.game_mode = mode
        self.controller.player_color = player_color

    def handle_forfeit(self):
        # Forfeit the game
        self.forfeit = True
        self.update_game_status()

    def game_status_text(self):
        if self.board.is_checkmate():
            return "Checkmate! " + ("Black wins!" if self.board.turn == chess.WHITE else "White wins!")
        elif self.board.is_stalemate():
            return "Stalemate! Draw!"
        elif self.board.is_insufficient_material():
            return "Draw due to insufficient material!"
        elif self.board.can_claim_draw():
            return "Draw can be claimed!"
        elif self.board.is_game_over():
            return "Game over!"
        elif hasattr(self, 'forfeit') and self.forfeit:
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            return f"Game forfeited! {winner} wins!"
        else:
            return ""

    def current_turn_text(self):
        check_status = ""
        if self.board.is_check():
            check_status = " - Check!"
        return "Turn: " + ("White" if self.board.turn == chess.WHITE else "Black") + check_status

    def svg_to_photo(self, svg_string):
        png_image = cairosvg.svg2png(bytestring=svg_string)
        return PhotoImage(data=png_image)

    def get_square_from_coords(self, x, y):
        files = 'abcdefgh'
        ranks = '87654321'
        file_index = min(max(int(x / (self.BOARD_SIZE / 8)), 0), 7)
        rank_index = min(max(int(y / (self.BOARD_SIZE / 8)), 0), 7)
        return files[file_index] + ranks[rank_index]

    def display_board(self, highlight_square=None):
        self.canvas.delete("all")
        fill_squares = {}

        # Highlight the last move
        if self.last_move:
            fill_squares[self.last_move.from_square] = "#FFFF0033"  # Yellow with some transparency
            fill_squares[self.last_move.to_square] = "#FFFF0033"  # Yellow with some transparency

        # Highlight possible moves with one color
        if highlight_square:
            for move in self.board.legal_moves:
                if move.from_square == chess.parse_square(highlight_square):
                    fill_squares[move.to_square] = "#ADD8E660"  # Light blue with some transparency

        # Highlight the king's square in check with another color
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            fill_squares[king_square] = "#FF634760"  # Tomato color with some transparency

        # Generate the SVG with filled squares
        svg = chess.svg.board(board=self.board, size=self.BOARD_SIZE, fill=fill_squares)
        photo = self.svg_to_photo(svg)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo
        self.turn_label.config(text=self.current_turn_text())

    def on_click(self, event):
        square = self.get_square_from_coords(event.x, event.y)
        self.source_square = chess.SQUARE_NAMES.index(square)
        piece = self.board.piece_at(self.source_square)
        if piece:
            self.highlight_square = square  # Set the square to be highlighted
            piece_svg = chess.svg.piece(piece, size=self.BOARD_SIZE // 8)
            self.selected_piece = self.svg_to_photo(piece_svg)
            self.canvas.create_image(event.x, event.y, image=self.selected_piece, tags="dragged_piece")
            self.display_board(highlight_square=square)  # Pass the square to highlight

    def on_drag(self, event):
        if self.selected_piece:
            self.canvas.delete("dragged_piece")
            # Create a dragged piece image at the cursor position.
            self.canvas.create_image(event.x, event.y, image=self.selected_piece, tags="dragged_piece")
            # Keep a reference to the image.
            self.canvas.dragged_piece_image = self.selected_piece


    def update_display(self, fen, last_move=None, game_status=None):
        # Update the board with the new FEN
        self.board.set_fen(fen)

        # Update last move and game status if provided
        self.last_move = last_move
        game_status = game_status if game_status else self.game_status_text()

        # Redraw the board and update the turn label
        self.display_board()
        self.turn_label.config(text=game_status)

    
    def on_release(self, event):
        self.canvas.delete("dragged_piece")
        dest_square = self.get_square_from_coords(event.x, event.y)
        dest_index = chess.SQUARE_NAMES.index(dest_square)

        # Create the move object
        move = chess.Move(self.source_square, dest_index)

        self.controller.handle_move(move)
        
        self.selected_piece = None
        self.highlight_square = None

    def update_game_status(self):
        game_status = self.game_status_text()
        if game_status:
            self.turn_label.config(text=game_status)
        else:
            self.turn_label.config(text=self.current_turn_text())

    def reset_game(self):
        # Reset the game
        self.controller.reset_board()
        self.last_move = None
        self.forfeit = False
        self.display_board()
        self.turn_label.config(text=self.current_turn_text())

    def run(self):
        self.root.mainloop()

    def handle_pawn_promotion(self, move):
        # Popup dialog for pawn promotion
        promotion_piece = self.ask_promotion_piece()
        promoted_move = chess.Move(move.from_square, move.to_square, promotion_piece)
        self.board.push(promoted_move)
        self.display_board()

    def ask_promotion_piece(self):
        # Load SVG images for each piece and convert to PhotoImage
        images = {
            chess.QUEEN: self.svg_to_photo(chess.svg.piece(chess.Piece(chess.QUEEN, self.board.turn))),
            chess.ROOK: self.svg_to_photo(chess.svg.piece(chess.Piece(chess.ROOK, self.board.turn))),
            chess.BISHOP: self.svg_to_photo(chess.svg.piece(chess.Piece(chess.BISHOP, self.board.turn))),
            chess.KNIGHT: self.svg_to_photo(chess.svg.piece(chess.Piece(chess.KNIGHT, self.board.turn)))
        }

        # Open the promotion dialog
        dialog = PromotionDialog(self.root, images)
        return dialog.piece if dialog.piece else chess.QUEEN  # Default to Queen

class PromotionDialog(tk.Toplevel):
    def __init__(self, parent, images):
        super().__init__(parent)
        self.piece = None  # To store the selected piece
        self.title("Pawn Promotion")
        self.geometry("200x100")  # Set the size of the dialog

        # Create a button for each piece
        for piece_type, img in images.items():
            btn = tk.Button(self, image=img, command=lambda p=piece_type: self.select_piece(p))
            btn.image = img  # Keep a reference
            btn.pack(side=tk.LEFT)

        self.transient(parent)  # Dialog is associated with the parent
        self.grab_set()  # Modal dialog
        self.wait_window()  # Wait for the dialog to be closed

    def select_piece(self, piece_type):
        self.piece = piece_type
        self.destroy()