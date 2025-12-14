"""
Temple Run Body Controller - Single Press Mode
Gesture executes ONCE - no continuous holding
"""

import cv2
import mediapipe as mp
import numpy as np
from pynput.keyboard import Controller, Key
import time
from collections import deque
import tkinter as tk
from PIL import Image, ImageTk
import threading

class TempleRunController:
    def __init__(self, master):
        self.master = master
        self.master.title("Temple Run Body Controller - Single Press")
        self.master.configure(bg='#1a1a2e')
        self.master.geometry("1400x800")

        # MediaPipe setup
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            smooth_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Keyboard controller
        self.keyboard = Controller()

        # Camera setup
        self.cap = None
        self.camera_active = False
        self.processing_thread = None

        # Gesture detection parameters
        self.jump_threshold = 0.15
        self.slide_single_hand_threshold = 0.12
        self.slide_body_angle = 20
        self.tilt_sensitivity = 0.08
        self.cooldown_time = 0.5  # Increased cooldown for single press
        self.show_skeleton = True

        # State tracking with gesture completion
        self.last_gesture_time = 0
        self.current_gesture = "IDLE"
        self.previous_gesture = "IDLE"
        self.gesture_in_progress = False
        self.neutral_center_x = None
        self.neutral_shoulder_hip_distance = None
        self.calibration_frames = []
        self.landmark_buffer = deque(maxlen=7)

        # Gesture state tracking (to prevent continuous trigger)
        self.gesture_states = {
            "JUMP": False,
            "SLIDE": False,
            "LEFT": False,
            "RIGHT": False
        }

        # FPS tracking
        self.fps = 0
        self.frame_times = deque(maxlen=30)

        # Thread-safe frame storage
        self.current_frame = None
        self.frame_lock = threading.Lock()

        # Gesture counter
        self.gesture_count = {
            "JUMP": 0,
            "SLIDE": 0,
            "LEFT": 0,
            "RIGHT": 0
        }

        self.setup_ui()

    def setup_ui(self):
        """Create the modern GUI"""
        main_frame = tk.Frame(self.master, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left panel - Video feed
        left_panel = tk.Frame(main_frame, bg='#16213e', relief=tk.RAISED, bd=3)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        video_label = tk.Label(left_panel, text="🎮 BODY CONTROL - SINGLE PRESS MODE",
                              font=('Arial', 18, 'bold'),
                              bg='#16213e', fg='#00fff5')
        video_label.pack(pady=10)

        self.video_canvas = tk.Label(left_panel, bg='#0f3460', text="Camera Feed Will Appear Here")
        self.video_canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Info display
        info_frame = tk.Frame(left_panel, bg='#16213e')
        info_frame.pack(pady=10, fill=tk.X)

        self.fps_label = tk.Label(info_frame, text="FPS: 0",
                                 font=('Arial', 12, 'bold'),
                                 bg='#16213e', fg='#00fff5')
        self.fps_label.pack(side=tk.LEFT, padx=20)

        self.angle_label = tk.Label(info_frame, text="Body Angle: 0°",
                                   font=('Arial', 12),
                                   bg='#16213e', fg='#ffffff')
        self.angle_label.pack(side=tk.LEFT, padx=20)

        # Right panel - Controls
        right_panel = tk.Frame(main_frame, bg='#16213e', relief=tk.RAISED, bd=3, width=420)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_panel.pack_propagate(False)

        # Gesture display
        gesture_frame = tk.Frame(right_panel, bg='#0f3460', relief=tk.RAISED, bd=2)
        gesture_frame.pack(pady=20, padx=20, fill=tk.X)

        tk.Label(gesture_frame, text="CURRENT ACTION",
                font=('Arial', 13, 'bold'),
                bg='#0f3460', fg='#ffffff').pack(pady=5)

        self.gesture_label = tk.Label(gesture_frame, text="IDLE",
                                     font=('Arial', 36, 'bold'),
                                     bg='#0f3460', fg='#00fff5')
        self.gesture_label.pack(pady=15)

        # Gesture counter display
        counter_frame = tk.Frame(right_panel, bg='#1a1a2e', relief=tk.RAISED, bd=2)
        counter_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(counter_frame, text="GESTURE COUNT",
                font=('Arial', 11, 'bold'),
                bg='#1a1a2e', fg='#00fff5').pack(pady=5)

        self.counter_label = tk.Label(counter_frame,
                                     text="JUMP: 0 | SLIDE: 0\nLEFT: 0 | RIGHT: 0",
                                     font=('Arial', 10),
                                     bg='#1a1a2e', fg='#ffffff',
                                     justify=tk.CENTER)
        self.counter_label.pack(pady=5)

        # Gesture rules info
        rules_frame = tk.Frame(right_panel, bg='#1a1a2e', relief=tk.RAISED, bd=2)
        rules_frame.pack(pady=10, padx=20, fill=tk.X)

        rules_text = """SINGLE PRESS MODE:
🙌 Both Hands UP → JUMP (Once)
🖐️ One Hand DOWN / Bend → SLIDE (Once)
⬅️ Lean LEFT → Move LEFT (Once)
➡️ Lean RIGHT → Move RIGHT (Once)

Return to neutral to trigger again!"""

        tk.Label(rules_frame, text=rules_text,
                font=('Arial', 9),
                bg='#1a1a2e', fg='#00fff5',
                justify=tk.LEFT).pack(pady=10, padx=10)

        # Control buttons
        button_frame = tk.Frame(right_panel, bg='#16213e')
        button_frame.pack(pady=15, padx=20, fill=tk.X)

        self.start_btn = tk.Button(button_frame, text="▶ START CAMERA",
                                   command=self.start_camera,
                                   bg='#00fff5', fg='#1a1a2e',
                                   font=('Arial', 12, 'bold'),
                                   relief=tk.RAISED, bd=3,
                                   activebackground='#00d4c4',
                                   cursor='hand2')
        self.start_btn.pack(pady=5, fill=tk.X)

        self.stop_btn = tk.Button(button_frame, text="⏹ STOP CAMERA",
                                 command=self.stop_camera,
                                 bg='#ff6b6b', fg='#1a1a2e',
                                 font=('Arial', 12, 'bold'),
                                 relief=tk.RAISED, bd=3,
                                 activebackground='#ff5252',
                                 state=tk.DISABLED,
                                 cursor='hand2')
        self.stop_btn.pack(pady=5, fill=tk.X)

        reset_btn = tk.Button(button_frame, text="↻ RESET CALIBRATION",
                             command=self.reset_calibration,
                             bg='#ffa500', fg='#1a1a2e',
                             font=('Arial', 12, 'bold'),
                             relief=tk.RAISED, bd=3,
                             activebackground='#ff9500',
                             cursor='hand2')
        reset_btn.pack(pady=5, fill=tk.X)

        # Reset counter button
        reset_counter_btn = tk.Button(button_frame, text="🔄 RESET COUNTER",
                                     command=self.reset_counter,
                                     bg='#9b59b6', fg='#ffffff',
                                     font=('Arial', 10, 'bold'),
                                     relief=tk.RAISED, bd=2,
                                     activebackground='#8e44ad',
                                     cursor='hand2')
        reset_counter_btn.pack(pady=5, fill=tk.X)

        # Camera status
        status_frame = tk.Frame(right_panel, bg='#16213e')
        status_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(status_frame, text="Camera:",
                font=('Arial', 11, 'bold'),
                bg='#16213e', fg='#ffffff').pack(side=tk.LEFT)

        self.status_indicator = tk.Label(status_frame, text="● OFFLINE",
                                        font=('Arial', 11, 'bold'),
                                        bg='#16213e', fg='#ff6b6b')
        self.status_indicator.pack(side=tk.LEFT, padx=10)

        # Sliders
        slider_frame = tk.Frame(right_panel, bg='#16213e')
        slider_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        tk.Label(slider_frame, text="⚙️ SENSITIVITY CONTROLS",
                font=('Arial', 11, 'bold'),
                bg='#16213e', fg='#00fff5').pack(pady=8)

        self.create_slider(slider_frame, "Jump Threshold", 0.05, 0.30,
                          self.jump_threshold, self.update_jump_threshold)
        self.create_slider(slider_frame, "Single Hand Slide", 0.05, 0.25,
                          self.slide_single_hand_threshold, self.update_slide_threshold)
        self.create_slider(slider_frame, "Body Bend Angle (°)", 10, 45,
                          self.slide_body_angle, self.update_body_angle)
        self.create_slider(slider_frame, "Tilt Sensitivity", 0.03, 0.15,
                          self.tilt_sensitivity, self.update_tilt_sensitivity)
        self.create_slider(slider_frame, "Cooldown (sec)", 0.3, 1.0,
                          self.cooldown_time, self.update_cooldown)

        # Skeleton toggle
        skeleton_frame = tk.Frame(right_panel, bg='#16213e')
        skeleton_frame.pack(pady=10, padx=20)

        self.skeleton_var = tk.BooleanVar(value=True)
        skeleton_check = tk.Checkbutton(skeleton_frame, text="✓ Show Skeleton Overlay",
                                       variable=self.skeleton_var,
                                       command=self.toggle_skeleton,
                                       bg='#16213e', fg='#ffffff',
                                       selectcolor='#0f3460',
                                       font=('Arial', 10, 'bold'),
                                       activebackground='#16213e',
                                       activeforeground='#00fff5')
        skeleton_check.pack()

    def create_slider(self, parent, label, from_, to, initial, command):
        """Create a styled slider with label"""
        frame = tk.Frame(parent, bg='#16213e')
        frame.pack(pady=6, fill=tk.X)

        label_widget = tk.Label(frame, text=label,
                font=('Arial', 9, 'bold'),
                bg='#16213e', fg='#ffffff')
        label_widget.pack(anchor=tk.W)

        slider = tk.Scale(frame, from_=from_, to=to,
                         resolution=0.01 if to < 1 else 1,
                         orient=tk.HORIZONTAL, command=command,
                         bg='#0f3460', fg='#00fff5',
                         troughcolor='#1a1a2e',
                         highlightthickness=0,
                         length=300,
                         sliderlength=30)
        slider.set(initial)
        slider.pack(fill=tk.X)

    def update_jump_threshold(self, val):
        self.jump_threshold = float(val)

    def update_slide_threshold(self, val):
        self.slide_single_hand_threshold = float(val)

    def update_body_angle(self, val):
        self.slide_body_angle = float(val)

    def update_tilt_sensitivity(self, val):
        self.tilt_sensitivity = float(val)

    def update_cooldown(self, val):
        self.cooldown_time = float(val)

    def toggle_skeleton(self):
        self.show_skeleton = self.skeleton_var.get()

    def reset_counter(self):
        """Reset gesture counter"""
        self.gesture_count = {
            "JUMP": 0,
            "SLIDE": 0,
            "LEFT": 0,
            "RIGHT": 0
        }
        self.update_counter_display()

    def update_counter_display(self):
        """Update counter label"""
        self.counter_label.config(
            text=f"JUMP: {self.gesture_count['JUMP']} | SLIDE: {self.gesture_count['SLIDE']}\n"
                 f"LEFT: {self.gesture_count['LEFT']} | RIGHT: {self.gesture_count['RIGHT']}"
        )

    def start_camera(self):
        """Start the webcam and processing loop"""
        if not self.camera_active:
            for camera_index in [0, 1, 2]:
                self.cap = cv2.VideoCapture(camera_index)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)

                    self.camera_active = True
                    self.start_btn.config(state=tk.DISABLED)
                    self.stop_btn.config(state=tk.NORMAL)
                    self.status_indicator.config(text="● ONLINE", fg='#00ff00')

                    self.processing_thread = threading.Thread(target=self.capture_loop, daemon=True)
                    self.processing_thread.start()

                    self.update_ui()
                    return

            self.gesture_label.config(text="NO CAMERA")
            self.status_indicator.config(text="● ERROR", fg='#ff0000')

    def stop_camera(self):
        """Stop the webcam"""
        if self.camera_active:
            self.camera_active = False
            time.sleep(0.1)

            if self.cap:
                self.cap.release()

            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_indicator.config(text="● OFFLINE", fg='#ff6b6b')
            self.video_canvas.config(image='', text="Camera Stopped")
            self.gesture_label.config(text="IDLE")

    def reset_calibration(self):
        """Reset body center calibration"""
        self.neutral_center_x = None
        self.neutral_shoulder_hip_distance = None
        self.calibration_frames = []
        self.landmark_buffer.clear()
        self.gesture_label.config(text="CALIBRATING...")

    def smooth_landmarks(self, landmarks):
        """Apply temporal smoothing using moving average"""
        self.landmark_buffer.append(landmarks)

        if len(self.landmark_buffer) < 3:
            return landmarks

        smoothed = {}
        for key in landmarks.keys():
            smoothed[key] = {
                'x': np.mean([frame[key]['x'] for frame in self.landmark_buffer]),
                'y': np.mean([frame[key]['y'] for frame in self.landmark_buffer]),
                'z': np.mean([frame[key]['z'] for frame in self.landmark_buffer]) if 'z' in landmarks[key] else 0,
                'visibility': landmarks[key]['visibility']
            }
        return smoothed

    def calibrate_neutral_position(self, body_center_x, shoulder_hip_dist):
        """Calibrate the neutral body position"""
        if self.neutral_center_x is None or self.neutral_shoulder_hip_distance is None:
            self.calibration_frames.append((body_center_x, shoulder_hip_dist))
            if len(self.calibration_frames) >= 30:
                centers, dists = zip(*self.calibration_frames)
                self.neutral_center_x = np.mean(centers)
                self.neutral_shoulder_hip_distance = np.mean(dists)
                self.calibration_frames = []

    def calculate_body_angle(self, shoulder_y, hip_y, shoulder_z, hip_z):
        """Calculate body forward bend angle"""
        vertical_dist = abs(hip_y - shoulder_y)
        depth_dist = abs(hip_z - shoulder_z)

        if vertical_dist > 0.01:
            angle = np.degrees(np.arctan(depth_dist / vertical_dist))
            return angle
        return 0

    def detect_gesture(self, landmarks):
        """Enhanced gesture detection with single press logic"""
        try:
            # Extract key landmarks
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]

            if (left_shoulder.visibility < 0.3 or right_shoulder.visibility < 0.3 or
                left_hip.visibility < 0.3 or right_hip.visibility < 0.3):
                # Reset all gesture states when pose not detected
                for key in self.gesture_states:
                    self.gesture_states[key] = False
                return "IDLE", 0

            # Calculate key positions
            shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
            shoulder_center_z = (left_shoulder.z + right_shoulder.z) / 2
            hip_center_y = (left_hip.y + right_hip.y) / 2
            hip_center_z = (left_hip.z + right_hip.z) / 2
            hip_y = hip_center_y
            body_center_x = (left_shoulder.x + right_shoulder.x) / 2

            shoulder_hip_distance = np.sqrt(
                (shoulder_center_y - hip_center_y)**2 +
                (shoulder_center_z - hip_center_z)**2
            )

            body_angle = self.calculate_body_angle(shoulder_center_y, hip_center_y,
                                                   shoulder_center_z, hip_center_z)

            # Smooth landmarks
            landmark_dict = {
                'left_wrist': {'x': left_wrist.x, 'y': left_wrist.y, 'z': left_wrist.z, 'visibility': left_wrist.visibility},
                'right_wrist': {'x': right_wrist.x, 'y': right_wrist.y, 'z': right_wrist.z, 'visibility': right_wrist.visibility},
                'shoulder_center': {'x': body_center_x, 'y': shoulder_center_y, 'z': shoulder_center_z, 'visibility': 1.0},
                'hip': {'x': body_center_x, 'y': hip_y, 'z': hip_center_z, 'visibility': 1.0}
            }
            smoothed = self.smooth_landmarks(landmark_dict)

            self.calibrate_neutral_position(smoothed['shoulder_center']['x'], shoulder_hip_distance)

            if self.neutral_center_x is None or self.neutral_shoulder_hip_distance is None:
                return "CALIBRATING", body_angle

            current_time = time.time()

            # JUMP Detection
            jump_detected = (smoothed['left_wrist']['y'] < smoothed['shoulder_center']['y'] - self.jump_threshold and
                           smoothed['right_wrist']['y'] < smoothed['shoulder_center']['y'] - self.jump_threshold and
                           left_wrist.visibility > 0.4 and right_wrist.visibility > 0.4)

            if jump_detected and not self.gesture_states["JUMP"]:
                if current_time - self.last_gesture_time >= self.cooldown_time:
                    self.gesture_states["JUMP"] = True
                    self.last_gesture_time = current_time
                    self.gesture_count["JUMP"] += 1
                    try:
                        self.keyboard.press(Key.up)
                        self.keyboard.release(Key.up)
                    except:
                        pass
                    return "JUMP", body_angle
            elif not jump_detected:
                self.gesture_states["JUMP"] = False

            # SLIDE Detection
            left_hand_down = (left_wrist.visibility > 0.4 and
                             smoothed['left_wrist']['y'] > smoothed['hip']['y'] + self.slide_single_hand_threshold)
            right_hand_down = (right_wrist.visibility > 0.4 and
                              smoothed['right_wrist']['y'] > smoothed['hip']['y'] + self.slide_single_hand_threshold)
            body_bent = body_angle > self.slide_body_angle

            body_compressed = False
            if self.neutral_shoulder_hip_distance:
                compression_ratio = shoulder_hip_distance / self.neutral_shoulder_hip_distance
                body_compressed = compression_ratio < 0.85

            slide_detected = left_hand_down or right_hand_down or body_bent or body_compressed

            if slide_detected and not self.gesture_states["SLIDE"]:
                if current_time - self.last_gesture_time >= self.cooldown_time:
                    self.gesture_states["SLIDE"] = True
                    self.last_gesture_time = current_time
                    self.gesture_count["SLIDE"] += 1
                    try:
                        self.keyboard.press(Key.down)
                        self.keyboard.release(Key.down)
                    except:
                        pass
                    return "SLIDE", body_angle
            elif not slide_detected:
                self.gesture_states["SLIDE"] = False

            # LEFT Detection
            left_detected = smoothed['shoulder_center']['x'] < self.neutral_center_x - self.tilt_sensitivity

            if left_detected and not self.gesture_states["LEFT"]:
                if current_time - self.last_gesture_time >= self.cooldown_time:
                    self.gesture_states["LEFT"] = True
                    self.last_gesture_time = current_time
                    self.gesture_count["LEFT"] += 1
                    try:
                        self.keyboard.press(Key.left)
                        self.keyboard.release(Key.left)
                    except:
                        pass
                    return "LEFT", body_angle
            elif not left_detected:
                self.gesture_states["LEFT"] = False

            # RIGHT Detection
            right_detected = smoothed['shoulder_center']['x'] > self.neutral_center_x + self.tilt_sensitivity

            if right_detected and not self.gesture_states["RIGHT"]:
                if current_time - self.last_gesture_time >= self.cooldown_time:
                    self.gesture_states["RIGHT"] = True
                    self.last_gesture_time = current_time
                    self.gesture_count["RIGHT"] += 1
                    try:
                        self.keyboard.press(Key.right)
                        self.keyboard.release(Key.right)
                    except:
                        pass
                    return "RIGHT", body_angle
            elif not right_detected:
                self.gesture_states["RIGHT"] = False

            return "IDLE", body_angle

        except Exception as e:
            print(f"Gesture detection error: {e}")
            return "ERROR", 0

    def capture_loop(self):
        """Separate thread for camera capture and processing"""
        while self.camera_active:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    continue

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                results = self.pose.process(rgb_frame)

                gesture = "IDLE"
                body_angle = 0

                if results.pose_landmarks:
                    gesture, body_angle = self.detect_gesture(results.pose_landmarks.landmark)

                    if self.show_skeleton:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            results.pose_landmarks,
                            self.mp_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                        )

                cv2.putText(frame, gesture, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                           1.5, (0, 255, 245), 3, cv2.LINE_AA)
                cv2.putText(frame, f"Angle: {int(body_angle)}°", (10, 100),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

                with self.frame_lock:
                    self.current_frame = frame
                    self.current_gesture = gesture
                    self.current_body_angle = body_angle

            except Exception as e:
                print(f"Capture error: {e}")
                time.sleep(0.1)

    def update_ui(self):
        """Update UI with latest frame"""
        if not self.camera_active:
            return

        try:
            start_time = time.time()

            with self.frame_lock:
                if self.current_frame is not None:
                    frame = self.current_frame.copy()
                    gesture = self.current_gesture
                    body_angle = getattr(self, 'current_body_angle', 0)
                else:
                    self.master.after(10, self.update_ui)
                    return

            color_map = {
                "JUMP": "#00ff00",
                "SLIDE": "#ff00ff",
                "LEFT": "#ffff00",
                "RIGHT": "#ff8800",
                "IDLE": "#00fff5",
                "CALIBRATING": "#ffa500",
                "ERROR": "#ff0000"
            }
            self.gesture_label.config(text=gesture, fg=color_map.get(gesture, "#00fff5"))

            self.angle_label.config(text=f"Body Angle: {int(body_angle)}°")

            # Update counter display
            self.update_counter_display()

            frame_time = time.time() - start_time
            self.frame_times.append(frame_time)
            self.fps = int(1.0 / np.mean(self.frame_times)) if len(self.frame_times) > 0 else 0
            self.fps_label.config(text=f"FPS: {self.fps}")

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image=img)

            self.video_canvas.config(image=photo, text="")
            self.video_canvas.image = photo

        except Exception as e:
            print(f"UI update error: {e}")

        self.master.after(30, self.update_ui)

    def cleanup(self):
        """Clean up resources"""
        self.camera_active = False
        time.sleep(0.2)

        if self.cap:
            self.cap.release()
        if self.pose:
            self.pose.close()
        cv2.destroyAllWindows()


def main():
    root = tk.Tk()
    app = TempleRunController(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()