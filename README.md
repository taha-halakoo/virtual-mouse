# Virtual Mouse v4.0 - "Liquid Glass" Evolution

The absolute pinnacle of hands-free interaction. v4.0 introduces the **Liquid Glass Dashboard**, a high-fidelity, glassmorphism-inspired UI designed for professionals who demand speed, precision, and aesthetics.

## The Liquid Glass Experience (v4.0)

*   **Neural Smoothing 2.0**: Enhanced One-Euro filtering combined with Relative Delta Tracking for a pointer that feels like it's an extension of your mind.
*   **Trackpad Paradigm**: No more "jumping". The air is your trackpad. Move your index finger to drive the cursor relative to its current position.
*   **The Clutch**: Open your palm or make a fist to "lift" the virtual mouse and reposition your arm without moving the cursor.
*   **Sniper Mode**: Pinch your ring finger to drop sensitivity by 80% for pixel-perfect CAD or design work.

## Setup

1.  **Python 3.7+**
2.  **Download Models**:
    *   [hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/hand_landmarker.task)
    *   [face_landmarker.task](https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task)
    *   Place BOTH `.task` files inside the `virtual-mouse` folder.
3.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```
4. **Launch**:
    ```bash
    python main.py
    ```

## Liquid Gesture Compendium

| Action | Neural Gesture |
| :--- | :--- |
| **Move Cursor** | **Index Finger Pointing**. (Relative Delta Tracking) |
| **Clutch (Pause)**| **Fist** OR **Open Palm**. Instantly pauses tracking. |
| **Left Click** | **Quick Pinch (Index + Thumb)**. |
| **Right Click** | **Quick Pinch (Middle + Thumb)**. |
| **Drag & Drop** | **Hold Pinch (Index + Thumb)**. |
| **Smooth Scroll** | **Two Fingers (Index + Middle)** up/down. |
| **Sniper Mode**| **Pinch Ring Finger + Thumb**. Ultra-precision mode. |

---

## 75+ Innovative Enhancements (v4.0 Roadmap)

1. **Bio-Sync Jitter:** Adjusts smoothing based on the user's micro-tremors detected via facial landmarks.
2. **Ambient Light HUD:** Auto-adjusts UI contrast based on room lighting detected by the webcam.
3. **Focus Shroud:** Dims everything on the screen except a circular area around the cursor.
4. **Air-Drawing Signatures:** Sign documents by signing in the air.
5. **Magnetic Buttons:** Cursor slightly "snaps" to UI elements to help with accuracy.
6. **Hand-Identity Locking:** Prevents the mouse from jumping to someone else's hand in the background.
7. **Neural Speed Mapping:** Learns your "flick" speed over time to auto-calibrate acceleration.
8. **Gesture-to-Speech:** Perform a sign to have the computer speak a pre-set phrase.
9. **Visual Echo:** A faint trail behind the cursor to help find it on large 4K displays.
10. **Stress-Relief Smoothing:** Detects "angry" rapid movement and smooths it out into "calm" curves.
11. **Virtual Trackball Mode:** Treat the air as a giant trackball.
12. **Depth-Based DPI:** Sensitivity changes as you move your hand closer/further from the lens.
13. **Hand-Shadow Pointer:** Adds a subtle shadow under the cursor for 3D depth.
14. **Gaze-Hand Fusion:** Eyes pick the target, hand performs the final click.
15. **Air-Typing Haptics:** Audio "ticks" that change frequency over virtual keys.
16. **Automatic Screen Locking:** PC locks instantly if the user walks away.
17. **Multi-User Collaboration:** Support for two cursors simultaneously.
18. **Gesture Profiles:** Custom sets for Gaming, Coding, and Browsing.
19. **Smart Edge-Scroll:** Pushing against the edge scrolls the window.
20. **Inertia-Scroll 2.0:** Scroll "momentum" that respects flick speed.
21. **Palm-Zoom:** Open palm towards camera and "push/pull" to zoom.
22. **Volume Knob Gesture:** Twist your wrist to adjust system volume.
23. **Desktop Swipe-Transition:** 3-finger swipe to change virtual desktops.
24. **App-Specific HUDs:** HUD color changes based on the active application.
25. **One-Eye Mode:** Optimized tracking for asymmetrical facial features.
26. **Tremor Cancellation:** Specialized filter for high-frequency hand shaking.
27. **Voice-Command Overlay:** Visual cues on the HUD when a voice is recognized.
28. **Battery-Aware Tracking:** Drops camera FPS to save power when unplugged.
29. **Privacy Shield:** Instantly blurs camera feed if a second person is detected.
30. **Gesture Macros:** Chain gestures (Pinch + Circle) to launch apps.
31. **Custom Cursor Skins:** Laser pointer, crosshair, or "glowing orb" skins.
32. **Calibration Wizard:** 30-second guided setup for range of motion.
33. **Telemetry Dashboard:** Live tracking of FPS, CPU, and stability.
34. **System Tray Stealth:** Run 100% hidden with hotkey toggle.
35. **Cross-Platform Sync:** Cloud-synced sensitivity and macros.
36. **Auto-Update System:** Silently pull the latest AI models.
37. **Hand-Gesture Password:** Unique finger sequence to unlock the app.
38. **Interactive Notifications:** Notifications that appear inside the HUD.
39. **Click Sound Library:** Mechanical, Digital, or "Liquid" click sounds.
40. **Visual Ripple Effect:** A circular wave appears where you click.
41. **Anti-Fatigue Timer:** HUD alerts to rest your arm after prolonged use.
42. **Posture Corrector:** Alerts if your head position indicates slouching.
43. **Presentation Laser:** Dedicated non-clicking highlight mode.
44. **Quick-Mute Fist:** Fist "punch" towards camera to mute mic.
45. **Brightness Scroll:** Scroll with pinky up to change monitor brightness.
46. **Transparent Overlay:** Click-through mode for the dashboard.
47. **Mini-Map HUD:** A tiny dot showing your hand position relative to the frame.
48. **Dynamic Resolution:** Resolution drops when hand is still to save CPU.
49. **AI Scene Detection:** Adjusts tracking for low light vs sunlight.
50. **Hand-Size Normalization:** Consistent speed regardless of distance.
51. **Virtual Boundary Haptics:** Audio alerts when hand is leaving frame.
52. **Snapshot Gesture:** "Frame" the screen with fingers to screenshot.
53. **Text-Highlight Mode:** Specialized stability for selecting text.
54. **Double-Click Assist:** Automatically converts rapid pinches to double clicks.
55. **Momentum-Stop:** Quick fist-close to stop an inertial cursor.
56. **Sub-frame Interpolation:** Predicts position between frames for 144Hz feel.
57. **Background Blur:** Blurs your room in the HUD for privacy.
58. **Color-Blind HUD:** Pattern-based mode indicators.
59. **Multi-Camera Support:** Use two webcams for true 3D sensing.
60. **Gesture-Based Browser Nav:** "Draw" arrows to navigate history.
61. **Panic Gesture:** Raise both hands to hide all windows instantly.
62. **Search-in-Air:** Perform a "Magnifying Glass" to trigger search.
63. **Sleep-Wake Gesture:** Computer wakes when it sees a specific wave.
64. **Virtual Ruler:** Measure screen pixels by moving finger.
65. **Magnifier Gesture:** Circle around a target to zoom in.
66. **Clipboard Gestures:** "Grab" to copy, "Release" to paste.
67. **Emoji Gestures:** Hand signs trigger emoji reactions.
68. **Network Remote:** Control a second PC via the first PC's camera.
69. **Hand-Rotation Scroll:** Tilt hand to scroll horizontally.
70. **Macro Recording:** Map hand movement paths to hotkeys.
71. **Smart-Pause:** Auto-pause when user looks away from monitor.
72. **Low-CPU Mode:** Uses a lightweight AI model.
73. **Interactive HUD Widgets:** Buttons on the camera overlay.
74. **3D Space Cursor:** Depth-to-Z-axis for modeling apps.
75. **Neural Smoothing Calibration:** AI adapts to your unique jitter pattern.
