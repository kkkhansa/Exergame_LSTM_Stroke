# camera.py
import cv2
import mediapipe as mp
import numpy as np
import time
from tensorflow.keras.models import load_model
import pygame
import math # Needed for math.pi

# This code is used for capturing video from the camera and processing hand gestures using a pre-trained model.
# It uses OpenCV for video capture and Mediapipe for hand detection and landmark extraction.
# It also uses TensorFlow for loading the pre-trained model and making predictions.
# The camera feed is displayed in a Pygame window, and the detected hand landmarks are drawn on the video frame.

# ==============================================================================
# NEW: Define HAND_CONNECTIONS constant, same as in your training script
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

# ==============================================================================
# NEW: Helper function to calculate angles, same as in your training script
# ==============================================================================
def calculate_angle(v1, v2):
    """Calculates the angle in radians between two vectors."""
    # Ensure vectors are not zero to avoid division by zero
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    v1_u = v1 / np.linalg.norm(v1)
    v2_u = v2 / np.linalg.norm(v2)
    dot_product = np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)
    return np.arccos(dot_product)


class HandGestureCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open video capture device.")
            self.is_camera_available = False
        else:
            self.is_camera_available = True

        # Use a high min_detection_confidence for better tracking stability in real-time
        self.hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
        try:
            # Ensure this path points to the model you trained with the engineered features
            self.model = load_model("model/090625_nonearlystop_lr_T_2.keras")
        except Exception as e:
            print(f"Error loading Keras model: {e}")
            print("Gesture recognition will be unavailable.")
            self.model = None
            self.is_camera_available = False

        self.mp_draw = mp.solutions.drawing_utils
        self.last_prediction_time = 0
        self.prediction_interval = 5  # seconds
        self.latest_predicted_label = 5 # Default to a 'no gesture' or 'idle' label

    # ==============================================================================
    # MODIFIED: This function is now the complete feature engineering pipeline
    # ==============================================================================
    def engineer_features(self, landmarks_np):
        """
        Downgraded feature engineering to produce 76 features to match the old model.
        """
        # 1. Pose-Invariant Normalization
        wrist_landmark = landmarks_np[0]
        relative_landmarks = landmarks_np - wrist_landmark

        # 2. Size Normalization
        max_distance = np.max(np.linalg.norm(relative_landmarks, axis=1))
        if max_distance > 0:
            normalized_landmarks = relative_landmarks / max_distance
        else:
            normalized_landmarks = relative_landmarks

        # 3. Bone Vectors
        bone_vectors = { (start, end): normalized_landmarks[end] - normalized_landmarks[start] for start, end in HAND_CONNECTIONS }

        # 4. Bone Angles (13 specific angles)
        angles = []
        
        # --- Intra-finger angles (Flexion) - 2 per finger = 10 angles ---
        # This is a likely combination for the old model
        flexion_bones = [
            ( (0,1),(1,2) ), ( (1,2),(2,3) ), # Thumb
            ( (0,5),(5,6) ), ( (5,6),(6,7) ), # Index
            ( (0,9),(9,10) ),( (9,10),(10,11) ),# Middle
            ( (0,13),(13,14) ),( (13,14),(14,15) ),# Ring
            ( (0,17),(17,18) ),( (17,18),(18,19) ) # Pinky
        ]
        for bone1, bone2 in flexion_bones:
            angles.append(calculate_angle(bone_vectors.get(bone1, np.zeros(3)), bone_vectors.get(bone2, np.zeros(3))))
            
        # --- Inter-finger angles (Splay) - 3 angles ---
        splay_bones = [( (0,5),(0,9) ), ( (0,9),(0,13) ), ( (0,13),(0,17) )]
        for bone1, bone2 in splay_bones:
            angles.append(calculate_angle(bone_vectors.get(bone1, np.zeros(3)), bone_vectors.get(bone2, np.zeros(3))))

        # Combine all features: 63 (coords) + 13 (angles) = 76 features
        feature_vector = np.concatenate([
            normalized_landmarks.flatten(),
            np.array(angles).flatten()
        ])
        
        return feature_vector

    def process(self):
        if not self.is_camera_available or not self.model:
            self.latest_predicted_label = 5
            return

        ret, frame = self.cap.read()
        if not ret:
            self.latest_predicted_label = 5
            return

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(image_rgb)

        current_time = time.time()
        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                if current_time - self.last_prediction_time > self.prediction_interval:
                    try:
                        # ==============================================================================
                        # MODIFIED: The core prediction logic now uses the full feature engineering
                        # ==============================================================================
                        
                        # 1. Get raw landmarks into a NumPy array
                        landmarks_raw_np = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])

                        # 2. Process landmarks using the new, comprehensive function
                        features = self.engineer_features(landmarks_raw_np)

                        # 3. Reshape the features to match the model's expected input: (batch, timesteps, features)
                        # Our batch size is 1, time steps is 1, and features is the length of our vector (e.g., 81)
                        model_input = np.reshape(features, (1, 1, -1))

                        # 4. Make prediction
                        prediction = self.model.predict(model_input, verbose=0)
                        self.latest_predicted_label = np.argmax(prediction)
                        print(f"Camera Process: Predicted Gesture Label = {self.latest_predicted_label}")
                        self.last_prediction_time = current_time
                        
                    except Exception as e:
                        print(f"Error during gesture prediction: {e}")
                        self.latest_predicted_label = 5
        else:
            if current_time - self.last_prediction_time > self.prediction_interval:
                self.latest_predicted_label = 5

    def get_predicted_label(self):
        return self.latest_predicted_label

    def get_frame(self):
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
            # Create a similar placeholder if frame read fails
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
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks_display, mp.solutions.hands.HAND_CONNECTIONS)

        frame_resized = cv2.resize(frame, (160, 120))
        frame_rgb_final = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        return pygame.surfarray.make_surface(frame_rgb_final.swapaxes(0, 1))

    def release(self):
        if self.is_camera_available and self.cap.isOpened():
            self.cap.release()
        print("Camera released.")