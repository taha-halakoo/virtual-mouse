# Virtual Mouse v3.0 - Pro Studio Edition

The ultimate, premium-grade webcam mouse controller. Built for zero-jitter precision, deep OS integration, and a sleek, professional user experience.

## The Pro Upgrades (v3.0)

*   **True One-Euro Filter**: Replaced basic smoothing with an advanced mathematical filter (used in AR/VR). Zero jitter when stationary, zero lag when moving fast.
*   **System Tray Integration**: Runs cleanly in the background. Minimize it to the Windows System Tray to keep your taskbar clean.
*   **Global Hotkey Support**: Press `Ctrl+Shift+M` from *anywhere* in your OS to instantly pause or resume tracking.
*   **Modern UI**: Rebuilt the interface using `ttkbootstrap` for a stunning, native "Cyborg" dark theme.
*   **Advanced OS Gestures**:
    *   **Volume Control**: Pinch (Thumb + Pinky) and move up/down to adjust system volume.
    *   **Desktop Switcher**: Swipe your Right Hand left or right to switch virtual desktops instantly.

## Setup

1.  **Python 3.7+**
2.  **Download Model**: [hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/hand_landmarker.task) must be in the `virtual-mouse` folder.
3.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```

## Control Manual

**Right Hand (The Pointer / Scroller):**
*   **Move**: Point with your INDEX finger.
*   **Scroll**: (In Scroll Mode) Move hand Up/Down.
*   **Switch Desktop**: Swipe hand quickly Left or Right.

**Left Hand (The Commander):**
*   **L-Click**: Pinch THUMB & INDEX.
*   **R-Click**: Pinch THUMB & MIDDLE.
*   **Drag**: Hold THUMB & INDEX pinch.
*   **Mode Swap**: Show 'V' Sign (Index+Middle up).
*   **Volume**: Pinch THUMB & PINKY and move hand Up/Down.

*(Note: In One-Handed mode, all these gestures are performed with the Right Hand).*
