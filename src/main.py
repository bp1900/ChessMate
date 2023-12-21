import chess
import tkinter as tk
from gui import ChessGUI
from robot.src.robot import Robot
from controller import ChessController, DetectionController
from chessEngine import ChessEngine
from camera import Camera
import queue

# SETUP
CAMERA = True
SELECT_CORNERS = False

GRIPPER_TEST_MODE = True
HOST = '10.10.73.239'
PORT = 30002

LARGE_THRS = 12
SMALL_THRS = 10

ENGINE_PATH = r'third_party\stockfish\stockfish-windows-x86-64-avx2.exe'
TIME_ENGINE = 2
ENGINE2_PATH = r'third_party\lc0\lc0.exe'
TIME_ENGINE2 = 0.01

def launch_game_mode(mode_selection_window, mode, color=None):
    # Close the mode selection window
    mode_selection_window.destroy()

    # Create the main GUI
    gui = ChessGUI()

    # Create the Robot controller
    robot = Robot(host=HOST, port=PORT, gripper_test_mode=GRIPPER_TEST_MODE)

    engine = ChessEngine(engine_path=ENGINE_PATH, time_limit=TIME_ENGINE)
    engine2 = ChessEngine(engine_path=ENGINE2_PATH, time_limit=TIME_ENGINE2)

    if CAMERA and mode != "engine-engine":
        # Create a frame for the heatmap
        heatmap_frame = tk.Frame(gui.root)
        heatmap_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create the camera
        max_history = 1 if mode == "human-human" else 2
        camera = Camera(select_corners=SELECT_CORNERS, large_threshold=LARGE_THRS, small_threshold=SMALL_THRS, max_history=max_history, parent=heatmap_frame)
    else:
        camera = None

    # Create the controller with the GUI
    controller = ChessController(gui, robot, mode, color, engine, engine2, camera=camera, gripper_test_mode=GRIPPER_TEST_MODE)

    # Set the controller in the GUI
    gui.set_controller(controller)

    # Create a thread-safe queue for communication between threads
    command_queue = queue.Queue()

    # Initialize and start the DetectionController
    detection_controller = DetectionController(controller, camera=camera, command_queue=command_queue, mode=mode)
    detection_controller.start_detection_loop()

    # Start the main GUI with the command queue
    gui.run(command_queue)

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