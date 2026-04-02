import cv2
import mediapipe as mp
import threading
import time
import queue
import numpy as np
import math
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --- Custom Drawing Utilities ---
HAND_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (5, 6), (6, 7), (7, 8),                # Index finger
    (9, 10), (10, 11), (11, 12),           # Middle finger
    (13, 14), (14, 15), (15, 16),          # Ring finger
    (17, 18), (18, 19), (19, 20),          # Pinky finger
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17) # Palm
])

class OmniResults:
    """A wrapper to hold both face and hand results, including new advanced AI metadata."""
    def __init__(self, face_result, hand_result, is_looking=True, frustration_level=0.0, hand_depths=None):
        self.face_landmarks = face_result.face_landmarks if face_result and face_result.face_landmarks else None
        self.hand_landmarks = hand_result.hand_landmarks if hand_result and hand_result.hand_landmarks else None
        self.handedness = hand_result.handedness if hand_result and hand_result.handedness else None
        
        # Feature 14: Gaze-Gating
        self.is_looking = is_looking
        
        # Feature 2: Micro-Expression Calibration
        self.frustration_level = frustration_level
        
        # Feature 4: Depth-Aware Z-Axis Navigation
        self.hand_depths = hand_depths if hand_depths else []

class OmniTracker:
    """
    Zero-Latency Multi-Modal Tracker using the modern MediaPipe Tasks API.
    Includes Gaze-Gating, Micro-Expression Analysis, and Depth estimation.
    """
    def __init__(self, camera_id=0, multi_camera=False):
        # Feature 62: Smartphone Secondary Sensor (camera_id can be a URL string like 'http://192.168.1.5:8080/video')
        self.camera_id = camera_id
        self.multi_camera = multi_camera
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
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.hand_landmarker = vision.HandLandmarker.create_from_options(hand_options)
            
            # Initialize Face Landmarker (Need blendshapes for Micro-Expressions)
            face_options = vision.FaceLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path='face_landmarker.task'),
                running_mode=vision.RunningMode.VIDEO,
                output_face_blendshapes=True,
                output_facial_transformation_matrixes=True,
                num_faces=5,
                min_face_detection_confidence=0.5
            )
            self.face_landmarker = vision.FaceLandmarker.create_from_options(face_options)
            print("Models initialized successfully.")
            return True
        except Exception as e:
            print(f"FAILED TO LOAD MODELS: {e}")
            print("CRITICAL: You must download both 'hand_landmarker.task' AND 'face_landmarker.task'.")
            return False

    def start(self):
        if not self.running:
            if not self._initialize_models():
                return
                
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
        # Feature 61: Multi-Camera Triangulation (stubbed logic for 2nd cam if enabled)
        # If camera_id is string (IP webcam), cv2 handles it natively.
        cap = cv2.VideoCapture(self.camera_id)
        # Try to force 60 FPS, but webcams may ignore
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

            try:
                hand_result = self.hand_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
                face_result = self.face_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
                
                # Analyze AI Intent & State
                is_looking = True
                frustration = 0.0
                
                if face_result.face_blendshapes:
                    blendshapes = face_result.face_blendshapes[0]
                    # Feature 14: Gaze-Gating (Check if looking away via head pitch/yaw/roll proxy)
                    # For simplicity, we use eyeLookOutRight/Left blendshapes
                    look_left = next((b.score for b in blendshapes if b.category_name == 'eyeLookOutLeft'), 0)
                    look_right = next((b.score for b in blendshapes if b.category_name == 'eyeLookOutRight'), 0)
                    if look_left > 0.7 or look_right > 0.7:
                        is_looking = False

                    # Feature 2: Micro-Expression Calibration (Frustration = brow down + mouth frown)
                    brow_down_left = next((b.score for b in blendshapes if b.category_name == 'browDownLeft'), 0)
                    brow_down_right = next((b.score for b in blendshapes if b.category_name == 'browDownRight'), 0)
                    mouth_frown = next((b.score for b in blendshapes if b.category_name == 'mouthFrownLeft'), 0)
                    frustration = (brow_down_left + brow_down_right + mouth_frown) / 3.0

                # Feature 4: Depth-Aware Z-Axis Navigation
                hand_depths = []
                if hand_result.hand_landmarks:
                    for hm in hand_result.hand_landmarks:
                        # Calculate bounding box area as proxy for depth (Z-axis)
                        xs = [lm.x for lm in hm]
                        ys = [lm.y for lm in hm]
                        width = max(xs) - min(xs)
                        height = max(ys) - min(ys)
                        area = width * height
                        # Larger area = closer to camera. Normalize to 0.0 - 1.0 roughly.
                        depth_z = min(1.0, area * 10.0) 
                        hand_depths.append(depth_z)

                combined_results = OmniResults(face_result, hand_result, is_looking, frustration, hand_depths)
                annotated_frame = self._draw_annotations(frame, combined_results)

                self.latest_results = combined_results
                self.latest_frame = annotated_frame
            except Exception as e:
                print(f"Inference Error: {e}")
                time.sleep(0.1)

    def _draw_annotations(self, frame, results):
        annotated_image = frame.copy()
        h, w, _ = frame.shape
        
        # Draw Gaze/Frustration UI overlay
        if not results.is_looking:
            cv2.putText(annotated_image, "GAZE LOST - PAUSED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if results.frustration_level > 0.4:
            cv2.putText(annotated_image, f"FRUSTRATION DETECTED: {results.frustration_level:.2f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        # Draw Face
        if results.face_landmarks:
            face = results.face_landmarks[0]
            nose = face[1]
            cx, cy = int(nose.x * w), int(nose.y * h)
            color = (0, 255, 0) if results.is_looking else (0, 0, 255)
            cv2.circle(annotated_image, (cx, cy), 5, color, -1)

        # Draw Hands
        if results.hand_landmarks:
            for idx, hand_landmarks in enumerate(results.hand_landmarks):
                # Depth Proxy Visualizer (Feature 4)
                if idx < len(results.hand_depths):
                    depth = results.hand_depths[idx]
                    cv2.putText(annotated_image, f"Z-Depth: {depth:.2f}", (int(hand_landmarks[0].x * w), int(hand_landmarks[0].y * h) - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                for connection in HAND_CONNECTIONS:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                        start_lm = hand_landmarks[start_idx]
                        end_lm = hand_landmarks[end_idx]
                        pt1 = (int(start_lm.x * w), int(start_lm.y * h))
                        pt2 = (int(end_lm.x * w), int(end_lm.y * h))
                        cv2.line(annotated_image, pt1, pt2, (224, 224, 224), 2)
                
                for lm in hand_landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(annotated_image, (cx, cy), 4, (0, 0, 255), -1)

        return annotated_image

    def get_results(self):
        return self.latest_results

    def get_annotated_frame(self):
        return self.latest_frame
