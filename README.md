GestureX
AI-Powered Body Gesture Game Controller
GestureX is a computer vision application that enables hands-free game control using full-body gestures detected through your webcam. Built with MediaPipe Pose and OpenCV, it translates real-time body movements into keyboard inputs, allowing you to play games like Temple Run without touching your keyboard.

Overview
This project uses pose estimation to track body landmarks and detect specific gestures, which are then converted into single-press keyboard actions. The system features automatic calibration, gesture state management to prevent repeated triggers, and a modern GUI with live feedback and customizable sensitivity controls.

Key Features

Real-Time Pose Detection: Uses MediaPipe Pose for accurate body tracking via webcam
Single-Press Gesture Execution: Each gesture triggers once, requiring return to neutral position before retriggering
Automatic Calibration: Adapts to your body position and proportions during the first 30 frames
Interactive GUI: Live camera feed with skeleton overlay, gesture visualization, and performance metrics
Adjustable Sensitivity: Real-time sliders for jump threshold, slide detection, tilt sensitivity, and cooldown timing
Gesture Counter: Tracks the number of times each gesture is executed
Multi-Platform Support: Works on Windows, Linux, and macOS


Gesture Mapping
GestureActionKeyboard KeyBoth hands raised above shouldersJump↑ (Up Arrow)One hand below hip OR body bend forwardSlide↓ (Down Arrow)Lean body leftMove Left← (Left Arrow)Lean body rightMove Right→ (Right Arrow)

Technologies Used

Python 3.8+
OpenCV: Video capture and frame processing
MediaPipe: Pose estimation and landmark detection
NumPy: Numerical computations and smoothing algorithms
Pynput: Keyboard input simulation
Tkinter: GUI framework
Pillow (PIL): Image processing for GUI display


Installation & Setup
Prerequisites

Python 3.8 or higher
Webcam (built-in or external)
Windows, Linux, or macOS

Windows Setup

Clone the repository

bash   git clone [https://github.com/yourusername/GestureX.git](https://github.com/ayanmondal1010100-afk/GestureX.git)
   cd GestureX

Create a virtual environment

bash   python -m venv venv

Activate the virtual environment

bash   venv\Scripts\activate

Install dependencies

bash   pip install opencv-python mediapipe numpy pynput pillow

Run the application

bash   python temple_run_controller.py
Linux/macOS Setup

Clone the repository

bash   git clone https://github.com/yourusername/GestureX.git
   cd GestureX

Create a virtual environment

bash   python3 -m venv venv

Activate the virtual environment

bash   source venv/bin/activate

Install dependencies

bash   pip install opencv-python mediapipe numpy pynput pillow

Run the application

bash   python3 temple_run_controller.py
```

### Running in VS Code or Other IDEs

1. Open the project folder in your IDE
2. Ensure the virtual environment is activated (select the correct Python interpreter)
3. Run `temple_run_controller.py` using the IDE's run button or terminal

---

## Usage

1. **Launch the application** and click "▶ START CAMERA"
2. **Position yourself** so your full body is visible in the camera frame
3. **Wait for calibration** (approximately 1 second while "CALIBRATING..." is displayed)
4. **Open your game** (e.g., Temple Run) and ensure the game window has focus
5. **Perform gestures** to control the game:
   - Raise both hands to jump
   - Lower one hand or bend forward to slide
   - Lean left or right to move sideways
6. **Adjust sensitivity** using the sliders if gestures are too sensitive or not responsive enough
7. **Toggle skeleton overlay** to see pose detection landmarks on the video feed

### Important Notes

- Ensure adequate lighting for better pose detection
- Stand at least 1.5-2 meters from the camera for full body visibility
- The game window must be in focus to receive keyboard inputs
- Each gesture executes once; return to neutral position to trigger again
- Use "↻ RESET CALIBRATION" if you change position significantly

---

## Project Structure
```
GestureX/
│
├── temple_run_controller.py    # Main application file
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies (optional)
└── venv/                        # Virtual environment (not tracked in git)

Use Cases

Gaming: Control runner games, platformers, or any game requiring arrow key inputs
Fitness Gaming: Combine entertainment with physical activity
Accessibility: Alternative input method for users who prefer gesture-based control
Computer Vision Learning: Educational project demonstrating pose estimation and gesture recognition
Prototyping: Foundation for custom gesture-based control systems


How It Works

Capture: Webcam frames are captured and processed in a separate thread
Detection: MediaPipe Pose identifies 33 body landmarks in real-time
Calibration: The system learns your neutral body position over 30 frames
Gesture Recognition: Body positions are analyzed against calibrated baselines and threshold values
State Management: Gesture states prevent continuous triggering; each gesture fires once per execution
Smoothing: Temporal smoothing using a moving average reduces jitter
Output: Detected gestures trigger corresponding keyboard key presses via Pynput


Troubleshooting
Camera not detected: Try changing camera indices in the code or check camera permissions
Gestures not triggering: Adjust sensitivity sliders or reset calibration
Low FPS: Close other applications using the webcam; reduce camera resolution if needed
Keyboard inputs not working: Ensure the target game window has focus

Future Enhancements

Support for custom gesture mapping
Multi-gesture combinations
Voice command integration
Game profiles with pre-configured sensitivity settings
Recording and playback of gesture sequences


Author
Ayan Mondal
Project Created: December 13, 2025

License
This project is open-source and available for educational and personal use.

Acknowledgments

Google MediaPipe team for the pose estimation model
OpenCV community for computer vision tools
