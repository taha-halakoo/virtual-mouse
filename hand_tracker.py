import cv2
import mediapipe as mp
import threading
import time
import numpy as np

# Import the new MediaPipe tasks
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Global drawing constants
# This is the standard set of connections for drawing the hand skeleton
HAND_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (5, 6), (6, 7), (7, 8),                # Index finger
    (9, 10), (10, 11), (11, 12),           # Middle finger
    (13, 14), (14, 15), (15, 16),          # Ring finger
    (17, 18), (18, 19), (19, 20),          # Pinky finger
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17) # Palm
])
WHITE_COLOR = (224, 224, 224)
BLACK_COLOR = (0, 0, 0)

def draw_landmarks_on_image(rgb_image, detection_result: vision.HandLandmarkerResult):
    """A helper function to draw landmarks on the image."""
    annotated_image = np.copy(rgb_image)
    if not detection_result.hand_landmarks:
        return annotated_image

    for hand_landmarks in detection_result.hand_landmarks:
        # Draw the connections
        for connection in HAND_CONNECTIONS:
            start_idx = connection[0]
            end_idx = connection[1]
            if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                start_landmark = hand_landmarks[start_idx]
                end_landmark = hand_landmarks[end_idx]
                
                start_point = (int(start_landmark.x * rgb_image.shape[1]), int(start_landmark.y * rgb_image.shape[0]))
                end_point = (int(end_landmark.x * rgb_image.shape[1]), int(end_landmark.y * rgb_image.shape[0]))
                
                cv2.line(annotated_image, start_point, end_point, WHITE_COLOR, 3)
                cv2.line(annotated_image, start_point, end_point, BLACK_COLOR, 2)

        # Draw the landmarks
        for landmark in hand_landmarks:
            center_coordinates = (int(landmark.x * rgb_image.shape[1]), int(landmark.y * rgb_image.shape[0]))
            cv2.circle(annotated_image, center_coordinates, 7, WHITE_COLOR, -1)
            cv2.circle(annotated_image, center_coordinates, 5, BLACK_COLOR, -1)
            
    return annotated_image


class HandTracker:
    """
    A class to handle hand tracking using the new MediaPipe Tasks API.
    """
    def __init__(self, camera_id=0, max_hands=1, min_detection_confidence=0.5):
        self.camera_id = camera_id
        self.running = False
        self.results = None
        self.annotated_frame = None
        self.landmarker = None
        
        # This model is expected to be bundled with the mediapipe library
        model_path = 'hand_landmarker.task'
        base_options = python.BaseOptions(model_asset_path=model_path)
        
        self.options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=min_detection_confidence
        )
        
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _initialize_landmarker(self):
        """Initializes the HandLandmarker, handling potential errors."""
        try:
            self.landmarker = vision.HandLandmarker.create_from_options(self.options)
            print("HandLandmarker initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize HandLandmarker: {e}")
            print("Please ensure the 'hand_landmarker.task' model is available.")
            self.running = False

    def start(self):
        if not self.running:
            self.running = True
            self.thread.start()
            print("HandTracker started.")

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        if self.landmarker:
            self.landmarker.close()
        print("HandTracker stopped.")

    def _run(self):
        self._initialize_landmarker()
        if not self.running: # Initialization might have failed
            return
            
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print(f"Error: Cannot open camera with ID {self.camera_id}")
            self.running = False
            return

        frame_timestamp_ms = 0
        while self.running and cap.isOpened():
            success, frame = cap.read()
            if not success:
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            frame_timestamp_ms = int(time.time() * 1000)
            
            # Process the frame and find hands
            self.results = self.landmarker.detect_for_video(mp_image, frame_timestamp_ms)

            # Draw annotations
            self.annotated_frame = draw_landmarks_on_image(frame, self.results)
            
            time.sleep(0.001)

        cap.release()

    def get_results(self):
        return self.results

    def get_annotated_frame(self):
        return self.annotated_frame
