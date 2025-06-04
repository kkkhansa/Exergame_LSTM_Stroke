# camera.py
import cv2
import mediapipe as mp
import numpy as np
import time
from tensorflow.keras.models import load_model
import pygame
# import mediapipe as mp # Already imported above

# This code is used for capturing video from the camera and processing hand gestures using a pre-trained model.
# It uses OpenCV for video capture and Mediapipe for hand detection and landmark extraction.
# It also uses TensorFlow for loading the pre-trained model and making predictions.
# The camera feed is displayed in a Pygame window, and the detected hand landmarks are drawn on the video frame.

# mp_hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1) # Defined below in class
# mp_draw = mp.solutions.drawing_utils # Defined below in class

class HandGestureCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open video capture device.")
            # You might want to handle this more gracefully, e.g., by disabling gesture control
            self.is_camera_available = False
        else:
            self.is_camera_available = True

        self.hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1)
        try:
            self.model = load_model("model/final_model.keras") # Ensure this path is correct
        except Exception as e:
            print(f"Error loading Keras model: {e}")
            print("Gesture recognition will be unavailable.")
            self.model = None # Disable model if loading fails
            self.is_camera_available = False # Or just disable gesture part

        self.mp_draw = mp.solutions.drawing_utils
        self.last_prediction_time = 0
        self.prediction_interval = 0.5  # seconds - Reduced for more responsive gestures
        self.latest_predicted_label = 5 # Store the latest prediction here (0 can be 'no gesture' or 'idle')

    def get_normalized_landmarks(self, hand_landmarks):
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.append([lm.x, lm.y, lm.z])
        landmarks = np.array(landmarks)
        base = landmarks[0] # Use wrist as base
        normalized = landmarks - base
        return normalized.flatten() # Flatten for some model inputs, ensure your model expects this

    def process(self):
        if not self.is_camera_available or not self.model:
            self.latest_predicted_label = 5 # Default to no gesture if camera/model issue
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
                        # Ensure the landmark processing matches your model's expected input shape
                        # The original code returned (21,3), then expanded to (1,21,3)
                        # Let's revert to that if flatten() was not intended for your specific model
                        landmarks_raw = []
                        for lm in hand_landmarks.landmark:
                            landmarks_raw.append([lm.x, lm.y, lm.z])
                        landmarks_np = np.array(landmarks_raw)
                        # base = landmarks_np[0] # Optional: Re-apply normalization if needed
                        # normalized_landmarks = landmarks_np - base
                        
                        # The model likely expects a batch dimension, and the original (21,3) shape
                        processed_landmarks_for_model = np.expand_dims(landmarks_np, axis=0) # Shape (1, 21, 3)

                        prediction = self.model.predict(processed_landmarks_for_model, verbose=0)
                        self.latest_predicted_label = np.argmax(prediction)
                        print(f"Camera Process: Predicted Gesture Label = {self.latest_predicted_label}") # Debug
                        self.last_prediction_time = current_time
                    except Exception as e:
                        print(f"Error during gesture prediction: {e}")
                        self.latest_predicted_label = 5 # Default on error
        else:
            # No hand detected, could set to a 'no gesture' label
            if current_time - self.last_prediction_time > self.prediction_interval: # Update even if no hand, to reset
                self.latest_predicted_label = 5 # Assuming 0 is idle/no specific gesture
                # print("Camera Process: No hand detected, label = 0") # Debug

    def get_predicted_label(self):
        """Returns the latest predicted gesture label."""
        # print(f"Camera GetLabel: Returning Label = {self.latest_predicted_label}") # Debug
        return self.latest_predicted_label

    def get_frame(self): # For displaying camera feed in UI
        if not self.is_camera_available:
            # Return a placeholder surface if camera is not available
            placeholder = pygame.Surface((160, 120))
            placeholder.fill((50, 50, 50)) # Dark grey
            font = pygame.font.Font(None, 20)
            text = font.render("No Camera", True, (255,255,255))
            text_rect = text.get_rect(center=(80,60))
            placeholder.blit(text, text_rect)
            return placeholder

        ret, frame = self.cap.read()
        if not ret:
            return None # Or the placeholder above

        frame = cv2.flip(frame, 1)
        image_rgb_for_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # For display
        
        # Process for landmarks to draw, separate from prediction processing
        # to avoid slowing down the display frame rate too much by model.predict
        result_display = self.hands.process(image_rgb_for_display.copy()) # Use a copy for processing

        if result_display.multi_hand_landmarks:
            for hand_landmarks_display in result_display.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks_display, mp.solutions.hands.HAND_CONNECTIONS) # Draw on BGR frame

        frame_resized = cv2.resize(frame, (160, 120)) # Resize BGR frame
        frame_rgb_final = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB) # Convert to RGB for Pygame
        return pygame.surfarray.make_surface(frame_rgb_final.swapaxes(0, 1))


    def release(self):
        if self.is_camera_available and self.cap.isOpened():
            self.cap.release()
        # cv2.destroyAllWindows() # Usually not needed if Pygame handles the window
        print("Camera released.")
