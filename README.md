# Virtual Mouse v5.1 - "Omni-Sense"

The absolute cutting-edge in webcam mouse control. This version introduces multi-modal biometrics (Face, Eyes, Hands) using the modern MediaPipe Tasks API.

## The Omni-Sense Upgrades (v5.1)

*   **Zero-Latency Pipeline**: Completely rewrote the threading model. The camera, AI inference, and mouse control now run on entirely separate, asynchronous queues. This eliminates the "lag" caused by Python's Global Interpreter Lock (GIL). It feels instant.
*   **Modern AI Models**: Updated to use the latest, highly optimized MediaPipe `FaceLandmarker` and `HandLandmarker` Tasks API.
*   **Face & Eye Tracking**:
    *   **Nose Pointer**: Use the tip of your nose for ultra-stable, fatigue-free pointing. (We amplify the movement so you don't have to turn your head far).
    *   **Eye Blinks**: Wink your Left Eye to Left Click. Wink your Right Eye to Right Click.
    *   **Facial Drag**: Open your mouth slightly (like "biting" the screen) to start a drag. Close to drop.

## Setup

1.  **Python 3.7+**
2.  **Download Models**: You need **TWO** model files for this version.
    *   [hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/hand_landmarker.task)
    *   [face_landmarker.task](https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task)
    *   Place BOTH `.task` files inside the `virtual-mouse` folder.
3.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```

## Control Manual

Open the app and select your mode:

**1. Face & Eyes (Omni-Sense)**
*   Aim: Move Nose
*   L-Click: Wink Left Eye
*   R-Click: Wink Right Eye
*   Drag: Open Mouth

**2. One-Handed Pro**
*   Move: Point Index Finger
*   Click: Pinch Thumb + Index
*   Scroll: Hold 'V' sign, move hand Up/Down

**3. Two-Handed Pro**
*   Right Hand: Point to move. Swipe Left/Right to change Desktops.
*   Left Hand: Pinch to Click. Hold 'V' to Scroll. Pinch Thumb+Pinky to change Volume.
