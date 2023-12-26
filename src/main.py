import chess
import tkinter as tk
from tkinter import ttk
from gui import ChessGUI
from robot.src.robot import Robot
from controller import ChessController, DetectionController, DetectionControllerAudio
from chessEngine import ChessEngine
from camera import Camera
import queue

# SETUP
CAMERA = False
SELECT_CORNERS = True # Select the corners of the chessboard

MICROPHONE = False # THIS HASNT BEEN TESTED ON THE LAB

GRIPPER_TEST_MODE = True
HOST = '10.10.73.239'
PORT = 30002

LARGE_THRS = 5
SMALL_THRS = 6

# Global Variables for Engine Paths and Times
ENGINE_PATHS = {
    "Stockfish": r'third_party\stockfish\stockfish-windows-x86-64-avx2.exe',
    "Leela Zero": r'third_party\lc0\lc0.exe'
}
ENGINE_TIMES = {"Stockfish": 2, "Leela Zero": 0.01}

def launch_game_mode(mode_selection_window, mode, color=None, engine1="Stockfish", engine2="Leela Zero", time_engine1=2, time_engine2=0.01):
    # Close the mode selection window
    mode_selection_window.destroy()

    # Extract the paths from the global ENGINE_PATHS dictionary
    engine_path = ENGINE_PATHS[engine1]
    engine2_path = ENGINE_PATHS[engine2]

    # Convert time values to floats
    time_engine = float(time_engine1)
    time_engine2 = float(time_engine2)

    # Create the main GUI
    gui = ChessGUI()

    # Create the Robot controller
    robot = Robot(host=HOST, port=PORT, gripper_test_mode=GRIPPER_TEST_MODE)

    engine = ChessEngine(engine_path=engine_path, time_limit=time_engine)
    engine2 = ChessEngine(engine_path=engine2_path, time_limit=time_engine2)

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
    if MICROPHONE:
        # THIS HASNT BEEN TESTED ON THE LAB
        detection_controller = DetectionControllerAudio(controller, camera=camera, command_queue=command_queue, mode=mode)
    else:
        detection_controller = DetectionController(controller, camera=camera, command_queue=command_queue, mode=mode)
    detection_controller.start_detection_loop()

    # Start the main GUI with the command queue
    gui.run(command_queue)

def launch_intermediate_window(mode_selection_window, mode, advanced_var, color=None):

    if not advanced_var.get():
        # Launch the game mode with default engine parameters
        launch_game_mode(mode_selection_window, mode, color)
        return
    else:
        # Close the initial mode selection window
        mode_selection_window.destroy()

    # Create a new window for engine selection
    engine_selection_window = tk.Tk()
    engine_selection_window.title("Select Engine Configuration")

    # Font configuration
    large_font = ('Verdana', 20)

    # Frame for engine configuration
    engine_config_frame = tk.Frame(engine_selection_window)
    engine_config_frame.pack(pady=20)

    # Engine for White (or the only engine in human vs. engine)
    text = "Choose Engine for White:" if mode == 'engine-engine' else "Choose Engine:"
    tk.Label(engine_config_frame, text=text, font=large_font).pack()
    engine1_var = tk.StringVar(value="Stockfish")  # default value
    engine1_dropdown = ttk.Combobox(engine_config_frame, textvariable=engine1_var, values=list(ENGINE_PATHS.keys()), state="readonly", font=large_font)
    engine1_dropdown.pack(fill=tk.X, padx=10)

    tk.Label(engine_config_frame, text="Max seconds per turn for White:", font=large_font).pack()
    time_engine1_scale = tk.Scale(engine_config_frame, from_=0.01, to=10.0, resolution=0.01, orient=tk.HORIZONTAL)
    time_engine1_scale.set(2.0)  # default value
    time_engine1_scale.pack(fill=tk.X, padx=10)

    # Conditional GUI elements for engine-engine mode
    if mode == "engine-engine":
        # Separator or title for Black Engine settings
        ttk.Separator(engine_config_frame).pack(fill='x', padx=10, pady=5)
        # Settings for Black Engine
        tk.Label(engine_config_frame, text="Choose Engine for Black:", font=large_font).pack()
        engine2_var = tk.StringVar(value="Leela Zero")  # default value
        engine2_dropdown = ttk.Combobox(engine_config_frame, textvariable=engine2_var, values=list(ENGINE_PATHS.keys()), state="readonly", font=large_font)
        engine2_dropdown.pack(fill=tk.X, padx=10)

        tk.Label(engine_config_frame, text="Max seconds per turn for Black:", font=large_font).pack()
        time_engine2_scale = tk.Scale(engine_config_frame, from_=0.01, to=10.0, resolution=0.01, orient=tk.HORIZONTAL)
        time_engine2_scale.set(0.01)  # default value
        time_engine2_scale.pack(fill=tk.X, padx=10)

    # Button to confirm selection and launch the game mode
    confirm_button_text = "Play Against Engine" if color else "Play Engine vs. Engine"

    ttk.Separator(engine_config_frame).pack(fill='x', padx=10, pady=5)

    confirm_button = tk.Button(engine_config_frame, text=confirm_button_text, height=2, width=20, font=large_font,
                               command=lambda: launch_game_mode(engine_selection_window, mode, color, 
                                                                engine1=engine1_var.get(), engine2=engine2_var.get() if mode == "engine-engine" else "Leela Zero", 
                                                                time_engine1=time_engine1_scale.get(), time_engine2=time_engine2_scale.get() if mode == "engine-engine" else "0.01"))
    confirm_button.pack(pady=10)

    engine_selection_window.mainloop()

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

    # Advanced settings toggle
    advanced_var = tk.BooleanVar(value=False)  # default value as false
    advanced_check = tk.Checkbutton(mode_frame, text="Advanced Engine Params", var=advanced_var, font=large_font)
    advanced_check.pack(side=tk.TOP, pady=(0, 10))

    # Add buttons for game mode selection
    create_button(mode_frame, "👤 vs. 👤", lambda: launch_game_mode(mode_selection_window, "human-human"), large_font, tk.TOP, 10, 5)
    create_button(mode_frame, "👤 (⚪) vs. 🖥️", lambda: launch_intermediate_window(mode_selection_window, "human-engine", advanced_var, chess.WHITE), large_font, tk.TOP, 10, 5)
    create_button(mode_frame, "👤 (⚫) vs. 🖥️", lambda: launch_intermediate_window(mode_selection_window, "human-engine", advanced_var, chess.BLACK), large_font, tk.TOP, 10, 5)
    create_button(mode_frame, "🖥️ vs. 🖥️", lambda: launch_intermediate_window(mode_selection_window, "engine-engine", advanced_var), large_font, tk.TOP, 10, 5)

    # Start the mode selection window
    mode_selection_window.mainloop()

if __name__ == "__main__":
    main()