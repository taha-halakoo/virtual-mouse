# Virtual Mouse v2.1 - Professional Edition

A high-performance, two-handed webcam mouse controller with adaptive smoothing, mirroring fix, and simplified gestures.

## Professional Features (v2.1)

*   **Mirroring Fix**: Cursor movement now correctly matches your "real" left/right movements in the webcam selfie-view.
*   **Super-Easy Gestures**: Uses clear finger-count logic for maximum reliability.
*   **Adaptive Smoothing**: Rock-solid precision when still, instant response when moving fast.
*   **Two-Handed Mastery**:
    *   **Right Hand**: Precision pointer.
    *   **Left Hand**: Action commander (Click, Drag, Scroll).

## Setup

1.  **Python 3.7+**
2.  **Download Model**: [hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/hand_landmarker.task) must be in the `virtual-mouse` folder.
3.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```

## Control Manual (Super-Easy Mode)

### Right Hand (The Pointer)
*   **Move Cursor**: Simply point with your **Index Finger**. (Keep other fingers down for best results).
*   **Scroll**: If **Scrolling Mode** is active, move your hand up/down.

### Left Hand (The Commander)
*   **Left Click**: Quick pinch (Thumb + Index).
*   **Right Click**: Quick pinch (Thumb + Middle).
*   **Drag & Drop**: Pinch and **hold** (Thumb + Index). Release to drop.
*   **Toggle Scroll Mode**: Show the **"V" or "Peace" Sign** (Index + Middle fingers raised). Hold it for a second until the HUD border turns Orange.

---
**Note**: If your hands are misidentified (Left is Right), you can change `handedness_swap` to `true` in the `config.json` file.
