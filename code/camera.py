# camera.py
import cv2
import mediapipe as mp
import numpy as np
import time
from tensorflow.keras.models import load_model
import pygame
import math 

# This code is used for capturing video from the camera and processing hand gestures using a pre-trained model.
# It uses OpenCV for video capture and Mediapipe for hand detection and landmark extraction.
# It also uses TensorFlow for loading the pre-trained model and making predictions.
# The camera feed is displayed in a Pygame window, and the detected hand landmarks are drawn on the video frame.

# ==============================================================================
# Constants
# ==============================================================================
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),         # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),         # Index finger
    (9, 10), (10, 11), (11, 12),            # Middle finger
    (13, 14), (14, 15), (15, 16),           # Ring finger
    (17, 18), (18, 19), (19, 20),           # Pinky finger
    (0, 9), (0, 13), (0, 17),               # Palm connections from wrist
    (5, 9), (9, 13), (13, 17)               # Palm connections across fingers
]

# Helper function to calculate angles
def calculate_angle(v1, v2):
    """Calculates the angle in radians between two vectors."""
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    v1_u = v1 / np.linalg.norm(v1)
    v2_u = v2 / np.linalg.norm(v2)
    dot_product = np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)
    return np.arccos(dot_product)


class HandGestureCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.is_camera_available = self.cap.isOpened()
        if not self.is_camera_available:
            print("Error: Could not open video capture device.")

        self.hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
        self.model = None
        try:
            self.model = load_model("model/090625_nonearlystop_lr_T_2.keras")
        except Exception as e:
            print(f"Error loading Keras model: {e}. Gesture recognition will be unavailable.")
            self.is_camera_available = False

        self.mp_draw = mp.solutions.drawing_utils

        # --- Dwell Time and State Machine ---
        self.DWELL_TIME_SECONDS = 3  # How long to hold a gesture to confirm it
        self.POST_ACTION_COOLDOWN = 0.5 # A short pause after an action to prevent immediate re-triggering

        self._potential_label = None          # The gesture currently being held
        self._potential_label_start_time = 0  # Timestamp when the potential gesture was first seen
        
        self._action_to_consume = None        # The confirmed action label to be fetched by the game
        
        self._is_in_cooldown = False          # Flag to indicate if we are in the post-action cooldown phase
        self._cooldown_end_time = 0           # Timestamp when the cooldown finishes
        # --- End Dwell Time ---

    def engineer_features(self, landmarks_np):
        """
        Downgraded feature engineering to produce 76 features to match the old model.
        """
        wrist_landmark = landmarks_np[0]
        relative_landmarks = landmarks_np - wrist_landmark

        max_distance = np.max(np.linalg.norm(relative_landmarks, axis=1))
        normalized_landmarks = relative_landmarks / max_distance if max_distance > 0 else relative_landmarks

        bone_vectors = { (start, end): normalized_landmarks[end] - normalized_landmarks[start] for start, end in HAND_CONNECTIONS }
        
        angles = []
        flexion_bones = [((0,1),(1,2)), ((1,2),(2,3)), ((0,5),(5,6)), ((5,6),(6,7)), ((0,9),(9,10)), ((9,10),(10,11)), ((0,13),(13,14)), ((13,14),(14,15)), ((0,17),(17,18)), ((17,18),(18,19))]
        for bone1, bone2 in flexion_bones:
            angles.append(calculate_angle(bone_vectors.get(bone1, np.zeros(3)), bone_vectors.get(bone2, np.zeros(3))))
            
        splay_bones = [((0,5),(0,9)), ((0,9),(0,13)), ((0,13),(0,17))]
        for bone1, bone2 in splay_bones:
            angles.append(calculate_angle(bone_vectors.get(bone1, np.zeros(3)), bone_vectors.get(bone2, np.zeros(3))))

        return np.concatenate([normalized_landmarks.flatten(), np.array(angles).flatten()])

    def process(self):
        """
        Processes a single camera frame to update the gesture dwell state machine.
        This should be called once per game loop.
        """
        if not self.is_camera_available or not self.model:
            return

        # Check if we are in a post-action cooldown
        if self._is_in_cooldown and time.time() < self._cooldown_end_time:
            return
        elif self._is_in_cooldown:
            self._is_in_cooldown = False # Cooldown finished, ready for next gesture

        ret, frame = self.cap.read()
        if not ret: return

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(image_rgb)
        
        current_prediction = None
        if result.multi_hand_landmarks:
            try:
                # Feature engineering and prediction
                landmarks_raw_np = np.array([[lm.x, lm.y, lm.z] for lm in result.multi_hand_landmarks[0].landmark])
                features = self.engineer_features(landmarks_raw_np)
                model_input = np.reshape(features, (1, 1, -1))
                prediction = self.model.predict(model_input, verbose=0)
                current_prediction = np.argmax(prediction)
            except Exception as e:
                print(f"Error during gesture prediction: {e}")
                current_prediction = None
        
        # --- State Machine Logic ---
        # If the current prediction is idle (5), reset everything.
        if current_prediction == 5 or current_prediction is None:
            self._potential_label = None
            self._potential_label_start_time = 0
            return

        # If the prediction is a new, non-idle gesture
        if current_prediction != self._potential_label:
            self._potential_label = current_prediction
            self._potential_label_start_time = time.time()
        # If the same gesture is being held
        else:
            time_held = time.time() - self._potential_label_start_time
            # If dwell time is exceeded, confirm the action and start cooldown
            if time_held >= self.DWELL_TIME_SECONDS:
                print(f"ACTION CONFIRMED: {self._potential_label}")
                self._action_to_consume = self._potential_label
                self._potential_label = None # Reset potential label
                self._potential_label_start_time = 0
                self._is_in_cooldown = True
                self._cooldown_end_time = time.time() + self.POST_ACTION_COOLDOWN

    def consume_action(self):
        """
        Called by the game to get a confirmed action. Returns the label then resets.
        This ensures an action is only processed once.
        """
        action = self._action_to_consume
        if action is not None:
            self._action_to_consume = None # Consume the action
        return action

    def get_dwell_progress(self):
        """
        Returns the progress of the current dwell timer as a float (0.0 to 1.0).
        Used by the UI to draw the clock.
        """
        if self._potential_label is not None and self._potential_label_start_time > 0:
            time_held = time.time() - self._potential_label_start_time
            progress = min(time_held / self.DWELL_TIME_SECONDS, 1.0)
            return progress
        return 0.0

    def get_frame(self):
        """Returns a Pygame surface of the current camera view for display."""
        if not self.is_camera_available:
            placeholder = pygame.Surface((160, 120))
            placeholder.fill((50, 50, 50))
            font = pygame.font.Font(None, 20)
            text = font.render("No Camera", True, (255, 255, 255))
            text_rect = text.get_rect(center=(80, 60))
            placeholder.blit(text, text_rect)
            return placeholder

        ret, frame = self.cap.read()
        if not ret:
            placeholder = pygame.Surface((160, 120))
            placeholder.fill((50, 50, 50))
            font = pygame.font.Font(None, 20)
            text = font.render("Frame Error", True, (255, 255, 255))
            text_rect = text.get_rect(center=(80, 60))
            placeholder.blit(text, text_rect)
            return placeholder

        frame = cv2.flip(frame, 1)
        image_rgb_for_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result_display = self.hands.process(image_rgb_for_display.copy())

        if result_display.multi_hand_landmarks:
            for hand_landmarks_display in result_display.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks_display, mp.solutions.hands.HAND_CONNECTIONS)

        frame_resized = cv2.resize(frame, (160, 120))
        frame_rgb_final = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        return pygame.surfarray.make_surface(frame_rgb_final.swapaxes(0, 1))

    def release(self):
        if self.is_camera_available and self.cap.isOpened():
            self.cap.release()
        print("Camera released.")
