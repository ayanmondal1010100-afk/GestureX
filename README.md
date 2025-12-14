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

System Architecture
1. Multi-Threading Design
The application uses a two-thread architecture to ensure smooth performance:
Main Thread (GUI)                 Worker Thread (Camera)
     |                                    |
     |---> Tkinter Event Loop             |---> Video Capture Loop
     |---> UI Updates (30ms)              |---> Pose Processing
     |---> Display Frames                 |---> Gesture Detection
     |                                    |
     |<-------- Frame Lock (Thread-Safe Communication) -------->|

Main Thread: Handles GUI rendering, user interactions, and display updates
Worker Thread: Continuously captures frames, processes pose data, and detects gestures
Thread-Safe Communication: Uses threading.Lock() to safely share frame data between threads

2. Data Flow Pipeline
Webcam → Frame Capture → RGB Conversion → MediaPipe Pose → Landmark Extraction
    ↓
Landmark Smoothing → Calibration → Gesture Detection → State Management
    ↓
Keyboard Simulation → GUI Update → User Feedback

How It Works: Technical Deep Dive
Phase 1: Initialization & Setup
When you start the application:

MediaPipe Pose Model is loaded with configuration:

model_complexity=1: Balanced accuracy and speed
smooth_landmarks=True: Reduces jitter in pose detection
min_detection_confidence=0.5: Minimum confidence to detect a person
min_tracking_confidence=0.5: Minimum confidence to track across frames


Camera Connection: Tries camera indices 0, 1, 2 sequentially until one opens
GUI Initialization: Creates Tkinter interface with video canvas and controls

Phase 2: Calibration (First 30 Frames)
The system needs to learn your neutral standing position to detect movements accurately.
What's Being Calibrated:

Neutral Center X-Position (neutral_center_x):

Calculates average shoulder center position
Used as reference for left/right tilt detection
Formula: (left_shoulder.x + right_shoulder.x) / 2


Shoulder-Hip Distance (neutral_shoulder_hip_distance):

Measures your body's vertical proportion
Used to detect body compression (sliding)
Formula: √[(shoulder_y - hip_y)² + (shoulder_z - hip_z)²]



Calibration Process:
python# Collects 30 frames of data
for frame in range(30):
    calibration_frames.append((body_center_x, shoulder_hip_dist))

# After 30 frames, calculates averages
neutral_center_x = mean(all_body_center_x_values)
neutral_shoulder_hip_distance = mean(all_shoulder_hip_distances)
Phase 3: Real-Time Pose Detection
MediaPipe Pose detects 33 body landmarks in each frame:
Key landmarks used:

LEFT_WRIST (15) & RIGHT_WRIST (16): For jump and slide detection
LEFT_SHOULDER (11) & RIGHT_SHOULDER (12): Body center reference
LEFT_HIP (23) & RIGHT_HIP (24): Lower body reference

Each landmark contains:

x: Horizontal position (0-1, normalized)
y: Vertical position (0-1, normalized)
z: Depth position (relative to hip center)
visibility: Confidence score (0-1)

Phase 4: Landmark Smoothing
Raw landmark data can be jittery. A moving average filter smooths the data:
python# Maintains buffer of last 7 frames
landmark_buffer = deque(maxlen=7)

# For each landmark coordinate
smoothed_x = mean([frame[landmark]['x'] for frame in last_7_frames])
smoothed_y = mean([frame[landmark]['y'] for frame in last_7_frames])
Why This Works:

Reduces high-frequency noise
Maintains responsiveness (7 frames ≈ 0.23 seconds at 30 FPS)
Prevents false gesture triggers

Phase 5: Gesture Detection Logic
JUMP Detection
python# Condition: Both wrists above shoulder center
left_wrist_up = left_wrist.y < shoulder_center_y - jump_threshold
right_wrist_up = right_wrist.y < shoulder_center_y - jump_threshold
both_visible = left_wrist.visibility > 0.4 AND right_wrist.visibility > 0.4

jump_detected = left_wrist_up AND right_wrist_up AND both_visible
Parameters:

jump_threshold: Default 0.15 (15% of frame height above shoulders)
Both hands must be visible (visibility > 0.4)

SLIDE Detection
Multiple conditions can trigger slide (OR logic):
Condition 1: Single Hand Down
pythonleft_hand_down = left_wrist.y > hip_center_y + slide_single_hand_threshold
right_hand_down = right_wrist.y > hip_center_y + slide_single_hand_threshold
Condition 2: Body Forward Bend
python# Calculates angle between vertical and body axis
vertical_distance = |hip_y - shoulder_y|
depth_distance = |hip_z - shoulder_z|
body_angle = arctan(depth_distance / vertical_distance) * (180/π)

body_bent = body_angle > slide_body_angle  # Default: 20°
Condition 3: Body Compression
python# Detects crouching/squatting
compression_ratio = current_shoulder_hip_distance / neutral_shoulder_hip_distance
body_compressed = compression_ratio < 0.85  # 15% compression
Final: slide_detected = hand_down OR body_bent OR body_compressed
LEFT/RIGHT Detection
python# Detects horizontal body shift from calibrated center
current_center_x = (left_shoulder.x + right_shoulder.x) / 2

left_detected = current_center_x < neutral_center_x - tilt_sensitivity
right_detected = current_center_x > neutral_center_x + tilt_sensitivity
Parameters:

tilt_sensitivity: Default 0.08 (8% of frame width shift)

Phase 6: State Management (Single-Press Logic)
Problem: Without state management, holding a gesture would spam key presses.
Solution: Each gesture has a boolean state flag:
pythongesture_states = {
    "JUMP": False,   # Is jump gesture currently held?
    "SLIDE": False,  # Is slide gesture currently held?
    "LEFT": False,   # Is left tilt held?
    "RIGHT": False   # Is right tilt held?
}
State Machine Logic:
python# When gesture is detected
if gesture_detected AND gesture_state == False:
    if time_since_last_gesture >= cooldown_time:
        gesture_state = True          # Mark as "in progress"
        trigger_keyboard_press()      # Execute ONCE
        last_gesture_time = current_time

# When gesture is released (user returns to neutral)
elif NOT gesture_detected:
    gesture_state = False             # Ready for next trigger
Cooldown Mechanism:

Default: 0.5 seconds between any gestures
Prevents accidental double-triggers
Adjustable via slider (0.3 - 1.0 seconds)

Phase 7: Keyboard Simulation
Uses pynput library to simulate keyboard inputs:
pythonfrom pynput.keyboard import Controller, Key

keyboard = Controller()

# Single key press-release cycle
keyboard.press(Key.up)      # Press down
keyboard.release(Key.up)    # Release immediately
Why Press-Release:

Games expect complete key press events
Prevents "stuck key" issues
Works with game input systems that detect key edges

Phase 8: GUI Update Cycle
Main thread updates UI every 30ms (≈33 FPS):
pythondef update_ui():
    # 1. Get latest frame from worker thread (thread-safe)
    with frame_lock:
        frame = current_frame.copy()
        gesture = current_gesture
    
    # 2. Update gesture display with color coding
    color_map = {"JUMP": green, "SLIDE": magenta, ...}
    
    # 3. Calculate and display FPS
    fps = 1.0 / mean(last_30_frame_times)
    
    # 4. Convert frame to Tkinter-compatible format
    frame_rgb = cv2.cvtColor(frame, BGR2RGB)
    photo = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
    
    # 5. Update canvas
    video_canvas.config(image=photo)
    
    # 6. Schedule next update
    master.after(30, update_ui)  # 30ms delay

Code Structure
Main Components
pythonclass TempleRunController:
    
    # 1. INITIALIZATION
    def __init__(self):
        # Setup MediaPipe, GUI, camera, threading
    
    # 2. CALIBRATION
    def calibrate_neutral_position():
        # Learn user's neutral stance
    
    # 3. SMOOTHING
    def smooth_landmarks():
        # Apply moving average filter
    
    # 4. GESTURE LOGIC
    def detect_gesture():
        # Analyze pose and return detected gesture
    
    # 5. CAMERA LOOP (Worker Thread)
    def capture_loop():
        # Continuous frame capture and processing
    
    # 6. GUI UPDATE (Main Thread)
    def update_ui():
        # Render frames and update interface
    
    # 7. CLEANUP
    def cleanup():
        # Release camera and close resources

Mathematical Concepts Used
1. Euclidean Distance (Shoulder-Hip Distance)
distance = √[(x₂ - x₁)² + (y₂ - y₁)²]
2. Angle Calculation (Body Bend)
angle = arctan(depth_distance / vertical_distance) × (180/π)
3. Moving Average (Smoothing)
smoothed_value = Σ(last_n_values) / n
4. Compression Ratio (Body Crouch)
ratio = current_distance / baseline_distance

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

bash   git clone https://github.com/ayanmondal1010100-afk/GestureX.git
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

bash   git clone https://github.com/ayanmondal1010100-afk/GestureX.git
   cd GestureX

Create a virtual environment

bash   python3 -m venv venv

Activate the virtual environment

bash   source venv/bin/activate

Install dependencies

bash   pip install opencv-python mediapipe numpy pynput pillow

Run the application

bash   python3 temple_run_controller.py
Running in VS Code or Other IDEs

Open the project folder in your IDE
Ensure the virtual environment is activated (select the correct Python interpreter)
Run temple_run_controller.py using the IDE's run button or terminal


Usage

Launch the application and click "▶ START CAMERA"
Position yourself so your full body is visible in the camera frame
Wait for calibration (approximately 1 second while "CALIBRATING..." is displayed)
Open your game (e.g., Temple Run) and ensure the game window has focus
Perform gestures to control the game:

Raise both hands to jump
Lower one hand or bend forward to slide
Lean left or right to move sideways


Adjust sensitivity using the sliders if gestures are too sensitive or not responsive enough
Toggle skeleton overlay to see pose detection landmarks on the video feed

Important Notes

Ensure adequate lighting for better pose detection
Stand at least 1.5-2 meters from the camera for full body visibility
The game window must be in focus to receive keyboard inputs
Each gesture executes once; return to neutral position to trigger again
Use "↻ RESET CALIBRATION" if you change position significantly


Project Structure
GestureX/
│
├── temple_run_controller.py    # Main application file
│   ├── TempleRunController     # Main class
│   │   ├── __init__()          # Initialization
│   │   ├── setup_ui()          # GUI creation
│   │   ├── calibrate_neutral_position()
│   │   ├── smooth_landmarks()
│   │   ├── detect_gesture()
│   │   ├── capture_loop()      # Worker thread
│   │   └── update_ui()         # Main thread
│   └── main()                  # Entry point
│
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies (optional)
└── venv/                        # Virtual environment (not tracked in git)

Performance Optimization
Threading Strategy

Separation of Concerns: Camera processing doesn't block GUI
Frame Dropping: If processing is slow, only latest frame is used
Lock Minimization: Thread lock held only during frame copy

Computational Efficiency

Model Complexity: Uses MediaPipe complexity level 1 (balanced)
Frame Rate: Targets 30 FPS for real-time response
Buffer Size: Limited to 7 frames for smoothing (0.23s memory)


Use Cases

Gaming: Control runner games, platformers, or any game requiring arrow key inputs
Fitness Gaming: Combine entertainment with physical activity
Accessibility: Alternative input method for users who prefer gesture-based control
Computer Vision Learning: Educational project demonstrating pose estimation and gesture recognition
Prototyping: Foundation for custom gesture-based control systems


Troubleshooting
Camera not detected: Try changing camera indices in the code or check camera permissions
Gestures not triggering: Adjust sensitivity sliders or reset calibration
Low FPS: Close other applications using the webcam; reduce camera resolution if needed
Keyboard inputs not working: Ensure the target game window has focus
False triggers: Increase cooldown time or adjust gesture thresholds
Jittery detection: System automatically smooths landmarks; ensure good lighting

Future Enhancements

Support for custom gesture mapping
Multi-gesture combinations
Voice command integration
Game profiles with pre-configured sensitivity settings
Recording and playback of gesture sequences
Machine learning for adaptive threshold tuning


Author
Ayan Mondal
Project Created: December 13, 2025

License
This project is open-source and available for educational and personal use.

Acknowledgments

Google MediaPipe team for the pose estimation model
OpenCV community for computer vision tools


References

MediaPipe Pose Documentation
OpenCV Python Tutorials
Pynput Documentation
