import tkinter as tk
from gui import ChessGUI
from controller import ChessController
from robot.src.robot import Robot
import chess

def main():
    # Create the GUI
    gui = ChessGUI()

    # Create the Robot controller
    robot = Robot()

    # Create the controller with the GUI
    controller = ChessController(gui, robot)

    # Set the controller in the GUI
    gui.set_controller(controller)

    large_font = ('Verdana', 20)  # Adjust the size as needed

    # Create a frame to hold the buttons
    button_frame = tk.Frame(gui.root)
    button_frame.pack(pady=10)

    # Add a button to trigger the engine move manually
    engine_move_button = tk.Button(button_frame, text="Engine Move", command=controller.check_and_make_engine_move, height=2, width=20)
    engine_move_button.config(font=large_font)
    engine_move_button.pack(side=tk.LEFT, padx=10)  # Pack the button on the left side of the frame

    # Add a button to trigger the audio transcription and move processing
    transcribe_button = tk.Button(button_frame, text="Transcribe Audio", command=lambda: process_audio(controller), height=2, width=20)
    transcribe_button.config(font=large_font)
    transcribe_button.pack(side=tk.LEFT, padx=10)  # Pack the button on the left side of the frame, to the right of the first button

    # Add buttons for game mode selection
    mode_frame = tk.Frame(gui.root)
    mode_frame.pack(pady=10)

    human_vs_human_button = tk.Button(mode_frame, text="Human vs Human", command=lambda: gui.set_game_mode("human-human"), height=2, width=20)
    human_vs_human_button.config(font=large_font)
    human_vs_human_button.pack(side=tk.LEFT, padx=10)

    human_vs_engine_white_button = tk.Button(mode_frame, text="Human (White) vs Engine", command=lambda: gui.set_game_mode("human-engine", chess.WHITE), height=2, width=20)
    human_vs_engine_white_button.config(font=large_font)
    human_vs_engine_white_button.pack(side=tk.LEFT, padx=10)

    human_vs_engine_black_button = tk.Button(mode_frame, text="Human (Black) vs Engine", command=lambda: gui.set_game_mode("human-engine", chess.BLACK), height=2, width=20)
    human_vs_engine_black_button.config(font=large_font)
    human_vs_engine_black_button.pack(side=tk.LEFT, padx=10)

    # Start the GUI
    gui.run()

def process_audio(controller):
    # You would replace 'path_to_audio_file.mp3' with the path to your actual audio file
    transcription = controller.transcribe_audio("match.mp3")
    controller.process_transcription_moves(transcription)

if __name__ == "__main__":
    main()
