import chess
import chess.svg
import tkinter as tk
from tkinter import PhotoImage
import tkinter.messagebox as messagebox
import cairosvg
import queue
import time

class ChessGUI:
    BOARD_SIZE = 600

    def __init__(self):
        self.board = chess.Board()
        self.possible_moves_displayed = False
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

        # Create a frame for the buttons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)

        # Add a wrong move button
        self.in_correction_mode = False
        self.wrong_move_button = tk.Button(self.button_frame, text="Wrong Move", command=self.handle_wrong_move, font=("Verdana", 20), height=2, width=20)
        self.wrong_move_button.grid(row=0, column=0, columnspan=2, pady=10)  # Span two columns

        # Add a reset button
        self.reset_button = tk.Button(self.button_frame, text="Reset", command=self.reset_game, font=("Verdana", 20), height=2, width=20)
        self.reset_button.grid(row=1, column=1, pady=10)  # Place in the right column of the second row


    def set_controller(self, controller):
        self.controller = controller

        # If game mode human-human disable the wrong move button
        if self.controller.game_mode == "engine-engine":
            self.wrong_move_button.config(state="disabled")


    def handle_wrong_move(self):
        self.controller.camera.pause_camera()
        self.controller.handle_wrong_move()
        self.in_correction_mode = True

        messagebox.showinfo("Confirm Action", "Please put the piece the engine move did to its previous position and then correct your LAST movement on the Interface.")
        self.wrong_move_button.config(state="disabled")  # Disable the button

    def display_possible_moves(self, moves):
        self.possible_moves_displayed = True
        colors = ["blue", "green", "red", "yellow", "purple", "orange"]  # Add more colors if needed
        self.move_color_dict = {}

        possible_arrows = []
        for i, move in enumerate(moves):
            color = colors[i % len(colors)]  # Select a color from the list
            possible_arrows.append(chess.svg.Arrow(move.from_square, move.to_square, color=color))
            self.move_color_dict[color] = move  # Save the color-move combo

        self.display_board(arrows=possible_arrows)  # Redraw the board with arrows
        self.show_disambiguation_dialog()

    def handle_forfeit(self):
        # Forfeit the game
        self.forfeit = True
        self.update_game_status()

    def game_status_text(self):
        status = ""
        if self.board.is_checkmate():
            status = "Checkmate! " + ("Black wins!" if self.board.turn == chess.WHITE else "White wins!")
        elif self.board.is_stalemate():
            status = "Stalemate! Draw!"
        elif self.board.is_insufficient_material():
            status = "Draw due to insufficient material!"
        elif self.board.can_claim_draw():
            status = "Draw can be claimed!"
        elif self.board.is_game_over():
            status = "Game over!"
        elif hasattr(self, 'forfeit') and self.forfeit:
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            status = f"Game forfeited! {winner} wins!"

        if status:
            show_custom_dialog('Game Over', status)

        return status

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

    def display_board(self, highlight_square=None, arrows=[]):
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
        svg = chess.svg.board(board=self.board, size=self.BOARD_SIZE, fill=fill_squares, arrows=arrows)
        photo = self.svg_to_photo(svg)
        if hasattr(self, 'board_image'):
            # Update the existing image
            self.canvas.itemconfig(self.board_image, image=photo)
        else:
            # Create the image for the first time
            self.board_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo
        self.turn_label.config(text=self.current_turn_text())


    def show_disambiguation_dialog(self):
        num_buttons = len(self.move_color_dict)

        # Create a top-level window for the dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Move")

        # Calculate the height of the window based on the number of buttons
        height = 70 + 50 * num_buttons
        dialog.geometry(f"300x{height}")  # Adjust the width as needed

        # Add a label with instructions
        label = tk.Label(dialog, text="Select the correct move:", font=("Verdana", 15))
        label.pack(pady=10)

        # Function to handle move selection
        def on_move_select(move):
            self.controller.handle_move(move)
            dialog.destroy()
            self.possible_moves_displayed = False

        # Sort the moves by color
        sorted_moves = sorted(self.move_color_dict.items(), key=lambda item: item[0])

        # Create a button for each possible move
        for i, (color, move) in enumerate(sorted_moves, start=1):
            move_button = tk.Button(dialog, text=f"{i}. {move}", bg=color, command=lambda m=move: on_move_select(m), height=2, width=20)
            move_button.pack(pady=5)

        # Make the window modal
        dialog.grab_set()
        dialog.focus_set()
        dialog.wait_window()
        self.possible_moves_displayed = False


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

    def update_display(self, fen, last_move=None):
        # Update the board with the new FEN
        self.board.set_fen(fen)

        # Update last move and game status if provided
        self.last_move = last_move
        self.display_board()

        game_status = self.game_status_text()
        # Redraw the board and update the turn label

        if game_status:
            self.turn_label.config(text=game_status)
        else:
            self.turn_label.config(text=self.current_turn_text())

        time.sleep(0.05)

    def on_release(self, event):
        self.canvas.delete("dragged_piece")
        dest_square = self.get_square_from_coords(event.x, event.y)
        dest_index = chess.SQUARE_NAMES.index(dest_square)

        # Create the move object
        move = chess.Move(self.source_square, dest_index)
        
        self.selected_piece = None
        self.highlight_square = None

        self.controller.handle_move(move)

        if self.in_correction_mode:
            self.in_correction_mode = False
            self.controller.exit_correction_mode()
            self.wrong_move_button.config(state="normal")
            self.controller.camera.resume_camera()


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
        self.wrong_move_button.config(state="disabled")  # Disable the 'Wrong Move' button on reset

        self.controller.start_game_loop()

    def run(self, command_queue):
        # Schedule the first check of the command queue
        self.root.after(100, self.check_command_queue, command_queue)
        self.root.mainloop()

    def check_command_queue(self, command_queue):
        try:
            while True:
                # Non-blocking check of the command queue
                command = command_queue.get_nowait()
                # Process the command (a move)
                self.process_command(command)
        except queue.Empty:
            # No more commands in the queue
            pass
        finally:
            # Schedule the next check of the command queue
            self.root.after(100, self.check_command_queue, command_queue)

    def process_command(self, command):
        # Process the command here (handle a move)
        if isinstance(command, chess.Move):
            self.controller.handle_move(command)

    def handle_pawn_promotion(self, move):
        # Popup dialog for pawn promotion
        promotion_piece = self.ask_promotion_piece()
        promoted_move = chess.Move(move.from_square, move.to_square, promotion_piece)
        return promoted_move
        #self.display_board()

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
        self.geometry("560x125")  # Set the size of the dialog

        # Create a button for each piece
        for piece_type, img in images.items():
            # Resize the image
            img = img.zoom(3)  # Increase the size by a factor of 2
            btn = tk.Button(self, image=img, command=lambda p=piece_type: self.select_piece(p))
            btn.image = img  # Keep a reference
            btn.pack(side=tk.LEFT)

        self.transient(parent)  # Dialog is associated with the parent
        self.grab_set()  # Modal dialog
        self.wait_window()  # Wait for the dialog to be closed

    def select_piece(self, piece_type):
        self.piece = piece_type
        self.destroy()

def show_custom_dialog(title, message):
    # Create a top-level window
    popup = tk.Toplevel()
    popup.title(title)
    popup.geometry("400x200")  # Width x Height

    # Add a message
    message_label = tk.Label(popup, text=message, wraplength=350, font=("Verdana", 40))
    message_label.pack(pady=10)

    # Add a dismiss button
    dismiss_button = tk.Button(popup, text="Dismiss", command=popup.destroy)
    dismiss_button.pack()

    # Make the window modal
    popup.grab_set()
    popup.focus_set()
    popup.wait_window()