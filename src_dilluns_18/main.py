import chess
import tkinter as tk
from gui import ChessGUI
from robot.src.robot import Robot
from controller import ChessController

def launch_game_mode(mode_selection_window, mode, color=None):
    # Close the mode selection window
    mode_selection_window.destroy()

    # Create the main GUI
    gui = ChessGUI()

    # Create the Robot controller
    robot = Robot()

    # Create the controller with the GUI
    controller = ChessController(gui, robot, mode, color)

    # Set the controller in the GUI
    gui.set_controller(controller)

    # Start the engine game if it's an engine-related mode
    gui.root.after(100, controller.start_game_loop)

    # Start the main GUI
    gui.run()

def main():
    # Create a new window for mode selection
    mode_selection_window = tk.Tk()
    mode_selection_window.title("Select Game Mode")

    large_font = ('Verdana', 20)

    # Add buttons for game mode selection
    mode_frame = tk.Frame(mode_selection_window)
    mode_frame.pack(pady=10)

    human_vs_human_button = tk.Button(mode_frame, text="Human vs Human", command=lambda: launch_game_mode(mode_selection_window, "human-human"), height=2, width=20)
    human_vs_human_button.config(font=large_font)
    human_vs_human_button.pack(side=tk.LEFT, padx=10)

    human_vs_engine_white_button = tk.Button(mode_frame, text="Human (White) vs Engine", command=lambda: launch_game_mode(mode_selection_window, "human-engine", chess.WHITE), height=2, width=20)
    human_vs_engine_white_button.config(font=large_font)
    human_vs_engine_white_button.pack(side=tk.LEFT, padx=10)

    human_vs_engine_black_button = tk.Button(mode_frame, text="Human (Black) vs Engine", command=lambda: launch_game_mode(mode_selection_window, "human-engine", chess.BLACK), height=2, width=20)
    human_vs_engine_black_button.config(font=large_font)
    human_vs_engine_black_button.pack(side=tk.LEFT, padx=10)

    engine_vs_engine_button = tk.Button(mode_frame, text="Engine vs Engine", command=lambda: launch_game_mode(mode_selection_window, "engine-engine"), height=2, width=20)
    engine_vs_engine_button.config(font=large_font)
    engine_vs_engine_button.pack(side=tk.LEFT, padx=10)

    # Start the mode selection window
    mode_selection_window.mainloop()

if __name__ == "__main__":
    main()