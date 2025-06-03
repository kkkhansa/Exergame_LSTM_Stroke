# code/camera.py
import cv2
import mediapipe as mp
import numpy as np
import time
from tensorflow.keras.models import load_model
import pygame
import mediapipe as mp

# This code is used for capturing video from the camera and processing hand gestures using a pre-trained model.
# It uses OpenCV for video capture and Mediapipe for hand detection and landmark extraction.
# It also uses TensorFlow for loading the pre-trained model and making predictions.
# The camera feed is displayed in a Pygame window, and the detected hand landmarks are drawn on the video frame.

mp_hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

class HandGestureCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1)
        self.model = load_model("model/final_model.keras")
        self.mp_draw = mp.solutions.drawing_utils
        self.last_prediction_time = 0
        self.prediction_interval = 1  # seconds
        self.latest_prediction_label = None

    def get_normalized_landmarks(self, hand_landmarks):
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.append([lm.x, lm.y, lm.z])
        landmarks = np.array(landmarks)
        base = landmarks[0]
        normalized = landmarks - base
        return normalized  # shape (21, 3), NOT flattened

    def process(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(image_rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                current_time = time.time()
                if current_time - self.last_prediction_time > self.prediction_interval:
                    landmarks = self.get_normalized_landmarks(hand_landmarks)
                    landmarks = np.expand_dims(landmarks, axis=0)  # shape (1, 21, 3)
                    prediction = self.model.predict(landmarks, verbose=0)
                    predicted_label = np.argmax(prediction)
                    print("Predicted Gesture:", predicted_label)
                    self.last_prediction_time = current_time

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None

        frame = cv2.flip(frame, 1)  # Mirror image for user-friendly view
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(image_rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

        frame = cv2.resize(frame, (160, 120))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    def get_predicted_label(self):
        return self.latest_prediction_label

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()



