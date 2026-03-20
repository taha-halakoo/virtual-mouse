import json
import time
import numpy as np
import pyautogui
import os
import math

from ui_view import UIView
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController

class AppController:
    """
    Orchestrates the Virtual Mouse v2.2 system with One/Two Handed modes.
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
        
        self.view = UIView(self)
        self.view.set_initial_settings(self.config)

        self._running = False
        self.plocx, self.plocy = 0, 0
        self.clocx, self.clocy = 0, 0

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
            
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)

    def start(self):
        if self.hand_tracker is None:
            self.hand_tracker = HandTracker(
                camera_id=self.config['general']['camera_id'],
                max_hands=2 
            )
        self._running = True
        self.hand_tracker.start()
        self.view.update_status("Running")

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
        smoothening = self.config['mouse']['smoothening']
        sensitivity = self.config['mouse']['pointer_sensitivity']

        if action == 'move':
            x1, y1 = args
            target_x = np.interp(x1, (50, frame_shape[1] - 50), (0, self.screen_width))
            target_y = np.interp(y1, (50, frame_shape[0] - 50), (0, self.screen_height))
            
            center_x, center_y = self.screen_width / 2, self.screen_height / 2
            target_x = center_x + (target_x - center_x) * sensitivity
            target_y = center_y + (target_y - center_y) * sensitivity

            dist = math.hypot(target_x - self.plocx, target_y - self.plocy)
            dynamic_smooth = max(2, smoothening - (dist / 100))
            
            self.clocx = self.plocx + (target_x - self.plocx) / dynamic_smooth
            self.clocy = self.plocy + (target_y - self.plocy) / dynamic_smooth
            
            self.mouse_controller.move(self.clocx, self.clocy)
            self.plocx, self.plocy = self.clocx, self.clocy

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

if __name__ == "__main__":
    pass
