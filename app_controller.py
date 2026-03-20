import json
import time
import numpy as np
import pyautogui
import os
import math
import keyboard

from ui_view import UIView
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController
from one_euro_filter import OneEuroFilter

class AppController:
    """
    Orchestrates the Virtual Mouse v3.0 system with True One-Euro Filtering,
    Global Hotkeys, and advanced gesture dispatching.
    """
    def __init__(self):
        self.config = self.load_config()
        self.screen_width, self.screen_height = pyautogui.size()

        self.hand_tracker = None
        self.gesture_recognizer = GestureRecognizer(
            click_pinch_distance=self.config['gestures']['click_pinch_distance'],
            handedness_swap=self.config['general'].get('handedness_swap', True),
            control_mode=self.config['general'].get('control_mode', 'two_handed')
        )
        self.mouse_controller = MouseController(self.screen_width, self.screen_height)
        
        # Initialize True One-Euro Filters for X and Y coordinates
        # mincutoff controls jitter (lower = less jitter), beta controls lag (higher = less lag at high speed)
        smoothening = self.config['mouse'].get('smoothening', 5)
        # Convert the abstract "smoothening 1-20" slider value into reasonable 1Euro parameters
        # High smoothening -> lower cutoff
        min_cutoff = max(0.01, 1.0 / smoothening)
        beta = 0.5 # A good default for hand tracking
        
        self.filter_x = OneEuroFilter(mincutoff=min_cutoff, beta=beta)
        self.filter_y = OneEuroFilter(mincutoff=min_cutoff, beta=beta)

        self.view = UIView(self)
        self.view.set_initial_settings(self.config)

        self._running = False
        
        # Setup Global Hotkey
        keyboard.add_hotkey('ctrl+shift+m', self.toggle_tracking_hotkey)

    def load_config(self):
        if not os.path.exists('config.json'):
             return {
                "general": {"camera_id": 0, "handedness_swap": True, "control_mode": "two_handed"},
                "mouse": {"smoothening": 5, "pointer_sensitivity": 1.2, "mirror_input": False},
                "gestures": {"click_pinch_distance": 0.15}
            }
        with open('config.json', 'r') as f:
            return json.load(f)
            
    def update_config(self, section, key, value):
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
            
            # Live updates
            if key == 'control_mode':
                self.gesture_recognizer.control_mode = value
            elif key == 'smoothening':
                min_cutoff = max(0.01, 1.0 / value)
                self.filter_x.mincutoff = min_cutoff
                self.filter_y.mincutoff = min_cutoff
            
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)

    def toggle_tracking_hotkey(self):
        """Called by the global keyboard hook."""
        # Because this is called from a background thread, we must schedule UI updates safely
        if self._running:
            self.view.after(0, self.stop)
            self.view.after(0, lambda: self.view.start_stop_button.configure(text="Start Tracking", bootstyle="success"))
        else:
            self.view.after(0, self.start)
            self.view.after(0, lambda: self.view.start_stop_button.configure(text="Stop Tracking", bootstyle="danger"))

    def start(self):
        if self.hand_tracker is None:
            self.hand_tracker = HandTracker(
                camera_id=self.config['general']['camera_id'],
                max_hands=2 
            )
        self._running = True
        self.hand_tracker.start()
        self.view.update_status("Running")
        
        # Reset filters on start
        self.filter_x = OneEuroFilter(mincutoff=self.filter_x.mincutoff, beta=self.filter_x.beta)
        self.filter_y = OneEuroFilter(mincutoff=self.filter_y.mincutoff, beta=self.filter_y.beta)

    def stop(self):
        self._running = False
        if self.hand_tracker:
            self.hand_tracker.stop()
            self.hand_tracker = None 
        self.view.update_status("Stopped")
        self.view.update_mode("N/A")

    def is_running(self):
        return self._running

    def run(self):
        if self._running:
            self.process_frame()
        
        if self.hand_tracker:
            frame = self.hand_tracker.get_annotated_frame()
            if frame is not None:
                self.view.update_video_feed(frame, mode=self.gesture_recognizer.mode, 
                                          pinching=self.gesture_recognizer.pinching)
        self.view.after(10, self.run)

    def process_frame(self):
        results = self.hand_tracker.get_results()
        annotated_frame = self.hand_tracker.get_annotated_frame()
        if annotated_frame is not None and results and results.hand_landmarks:
            frame_shape = annotated_frame.shape
            self.gesture_recognizer.update_result(results, frame_shape)
            actions = self.gesture_recognizer.recognize()
            for action, args in actions:
                self.execute_action(action, args, frame_shape)
        elif self._running:
            self.view.update_status("No Hands")

    def execute_action(self, action, args, frame_shape):
        sensitivity = self.config['mouse']['pointer_sensitivity']
        mirror = self.config['mouse'].get('mirror_input', False)

        if action == 'move':
            x1, y1 = args
            
            # 1. Map to screen
            target_x = np.interp(x1, (50, frame_shape[1] - 50), (0, self.screen_width))
            target_y = np.interp(y1, (50, frame_shape[0] - 50), (0, self.screen_height))
            
            if mirror:
                target_x = self.screen_width - target_x

            # 2. Sensitivity multiplier
            center_x, center_y = self.screen_width / 2, self.screen_height / 2
            target_x = center_x + (target_x - center_x) * sensitivity
            target_y = center_y + (target_y - center_y) * sensitivity
            
            # Clamp to screen bounds before filtering
            target_x = max(0, min(self.screen_width, target_x))
            target_y = max(0, min(self.screen_height, target_y))

            # 3. Apply True One-Euro Filter
            current_time = time.time()
            smooth_x = self.filter_x(current_time, target_x)
            smooth_y = self.filter_y(current_time, target_y)
            
            self.mouse_controller.move(smooth_x, smooth_y)

        elif action == 'left_click':
            self.mouse_controller.left_click()
        elif action == 'right_click':
            self.mouse_controller.right_click()
        elif action == 'mouse_down':
            self.mouse_controller.mouse_down()
        elif action == 'mouse_up':
            self.mouse_controller.mouse_up()
        elif action == 'scroll':
            self.mouse_controller.scroll(args)
        elif action == 'set_mode':
            self.view.update_mode(args)
        elif action == 'desktop_left':
            pyautogui.hotkey('win', 'ctrl', 'left') # Windows specific, adjust for OS if needed
            print("Action: Desktop Left")
        elif action == 'desktop_right':
            pyautogui.hotkey('win', 'ctrl', 'right')
            print("Action: Desktop Right")
        elif action == 'volume_up':
            pyautogui.press('volumeup')
        elif action == 'volume_down':
            pyautogui.press('volumedown')

if __name__ == "__main__":
    pass
