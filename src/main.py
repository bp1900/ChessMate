import chess
import tkinter as tk
from gui import ChessGUI
from robot.src.robot import Robot
from controller import ChessController

# SETUP
GRIPPER_TEST_MODE = False
ENGINE_PATH = r'third_party\stockfish\stockfish-windows-x86-64-avx2.exe'
TIME_ENGINE = 2
ENGINE2_PATH = r'third_party\lc0\lc0.exe'
TIME_ENGINE2 = 0.01
CAMERA = False

def launch_game_mode(mode_selection_window, mode, color=None):
    # Close the mode selection window
    mode_selection_window.destroy()

    # Create the main GUI
    gui = ChessGUI()

    # Create the Robot controller
    robot = Robot(gripper_test_mode=GRIPPER_TEST_MODE)

    # Create the controller with the GUI
    controller = ChessController(gui, robot, mode, color, engine_path=ENGINE_PATH, engine2_path=ENGINE2_PATH, time_engine=TIME_ENGINE, time_engine2=TIME_ENGINE2, camera=CAMERA, gripper_test_mode=GRIPPER_TEST_MODE)

    # Set the controller in the GUI
    gui.set_controller(controller)

    # Start the engine game if it's an engine-related mode
    gui.root.after(100, controller.start_game_loop)

    # Start the main GUI
    gui.run()

def create_button(parent, text, command, font, side, padx, pady):
    button = tk.Button(parent, text=text, command=command, height=2, width=20)
    button.config(font=font)
    button.pack(side=side, padx=padx, pady=pady)
    return button

def main():
    # Create a new window for mode selection
    mode_selection_window = tk.Tk()
    mode_selection_window.title("Select Game Mode")

    # Font configuration
    large_font = ('Verdana', 20)

    # Frame for buttons
    mode_frame = tk.Frame(mode_selection_window)
    mode_frame.pack(pady=20)

    # Add buttons for game mode selection
    create_button(mode_frame, "Human vs Human", lambda: launch_game_mode(mode_selection_window, "human-human"), large_font, tk.TOP, 10, 5)
    create_button(mode_frame, "Human (White) vs Engine", lambda: launch_game_mode(mode_selection_window, "human-engine", chess.WHITE), large_font, tk.TOP, 10, 5)
    create_button(mode_frame, "Human (Black) vs Engine", lambda: launch_game_mode(mode_selection_window, "human-engine", chess.BLACK), large_font, tk.TOP, 10, 5)
    create_button(mode_frame, "Engine vs Engine", lambda: launch_game_mode(mode_selection_window, "engine-engine"), large_font, tk.TOP, 10, 5)

    # Start the mode selection window
    mode_selection_window.mainloop()

if __name__ == "__main__":
    main()