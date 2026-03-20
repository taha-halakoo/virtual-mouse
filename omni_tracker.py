import cv2
import mediapipe as mp
import threading
import time
import queue
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --- Custom Drawing Utilities ---
# Since mp.solutions is deprecated, we draw the basics ourselves for the HUD.
HAND_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (5, 6), (6, 7), (7, 8),                # Index finger
    (9, 10), (10, 11), (11, 12),           # Middle finger
    (13, 14), (14, 15), (15, 16),          # Ring finger
    (17, 18), (18, 19), (19, 20),          # Pinky finger
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17) # Palm
])

class OmniResults:
    """A wrapper to hold both face and hand results to match the old API structure conceptually."""
    def __init__(self, face_result, hand_result):
        self.face_landmarks = face_result.face_landmarks if face_result and face_result.face_landmarks else None
        self.hand_landmarks = hand_result.hand_landmarks if hand_result and hand_result.hand_landmarks else None
        self.handedness = hand_result.handedness if hand_result and hand_result.handedness else None

class OmniTracker:
    """
    Zero-Latency Multi-Modal Tracker using the modern MediaPipe Tasks API.
    """
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.running = False
        
        self.frame_queue = queue.Queue(maxsize=1)
        self.latest_results = None
        self.latest_frame = None

        self.face_landmarker = None
        self.hand_landmarker = None

        self.grabber_thread = None
        self.inference_thread = None

    def _initialize_models(self):
        print("Initializing MediaPipe Tasks API...")
        try:
            # Initialize Hand Landmarker
            hand_options = vision.HandLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path='hand_landmarker.task'),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.5
            )
            self.hand_landmarker = vision.HandLandmarker.create_from_options(hand_options)
            
            # Initialize Face Landmarker
            face_options = vision.FaceLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path='face_landmarker.task'),
                running_mode=vision.RunningMode.VIDEO,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1,
                min_face_detection_confidence=0.5
            )
            self.face_landmarker = vision.FaceLandmarker.create_from_options(face_options)
            print("Models initialized successfully.")
            return True
        except Exception as e:
            print(f"FAILED TO LOAD MODELS: {e}")
            print("CRITICAL: You must download both 'hand_landmarker.task' AND 'face_landmarker.task' and place them in this folder.")
            return False

    def start(self):
        if not self.running:
            if not self._initialize_models():
                return # Abort start if models are missing
                
            self.running = True
            self.grabber_thread = threading.Thread(target=self._frame_grabber_loop, daemon=True)
            self.grabber_thread.start()
            
            self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
            self.inference_thread.start()
            print("OmniTracker started.")

    def stop(self):
        self.running = False
        if self.grabber_thread and self.grabber_thread.is_alive():
            self.grabber_thread.join()
        if self.inference_thread and self.inference_thread.is_alive():
            self.inference_thread.join()
        if self.face_landmarker: self.face_landmarker.close()
        if self.hand_landmarker: self.hand_landmarker.close()
        print("OmniTracker stopped.")

    def _frame_grabber_loop(self):
        cap = cv2.VideoCapture(self.camera_id)
        cap.set(cv2.CAP_PROP_FPS, 60)
        
        if not cap.isOpened():
            print("Error: Camera not found.")
            self.running = False
            return

        while self.running and cap.isOpened():
            success, frame = cap.read()
            if success:
                frame = cv2.flip(frame, 1)
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
            else:
                time.sleep(0.01)
        cap.release()

    def _inference_loop(self):
        last_timestamp_ms = 0
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            frame_timestamp_ms = int(time.time() * 1000)
            if frame_timestamp_ms <= last_timestamp_ms:
                frame_timestamp_ms = last_timestamp_ms + 1
            last_timestamp_ms = frame_timestamp_ms

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Run both inferences
            try:
                hand_result = self.hand_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
                face_result = self.face_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
                
                # Combine results
                combined_results = OmniResults(face_result, hand_result)
                
                annotated_frame = self._draw_annotations(frame, combined_results)

                self.latest_results = combined_results
                self.latest_frame = annotated_frame
            except Exception as e:
                print(f"Inference Error: {e}")
                time.sleep(0.1)

    def _draw_annotations(self, frame, results):
        annotated_image = frame.copy()
        h, w, _ = frame.shape
        
        # Draw Face (Minimal - Just the Nose Pointer for HUD clarity)
        if results.face_landmarks:
            face = results.face_landmarks[0]
            nose = face[1] # Tip of nose
            cx, cy = int(nose.x * w), int(nose.y * h)
            cv2.circle(annotated_image, (cx, cy), 5, (0, 255, 0), -1)

        # Draw Hands
        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                # Draw connections
                for connection in HAND_CONNECTIONS:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                        start_lm = hand_landmarks[start_idx]
                        end_lm = hand_landmarks[end_idx]
                        pt1 = (int(start_lm.x * w), int(start_lm.y * h))
                        pt2 = (int(end_lm.x * w), int(end_lm.y * h))
                        cv2.line(annotated_image, pt1, pt2, (224, 224, 224), 2)
                
                # Draw joints
                for lm in hand_landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(annotated_image, (cx, cy), 4, (0, 0, 255), -1)

        return annotated_image

    def get_results(self):
        return self.latest_results

    def get_annotated_frame(self):
        return self.latest_frame
