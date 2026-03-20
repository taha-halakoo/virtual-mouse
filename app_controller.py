import json
import time
import numpy as np
import pyautogui
import os
import math
import keyboard

from ui_view import UIView
from omni_tracker import OmniTracker
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController
from one_euro_filter import OneEuroFilter

class AppController:
    """
    Virtual Mouse v5.0 "Omni-Sense"
    Integrates async tracking, face/eye logic, and true 1-Euro filters.
    """
    def __init__(self):
        self.config = self.load_config()
        self.screen_width, self.screen_height = pyautogui.size()

        self.tracker = None # OmniTracker
        self.gesture_recognizer = GestureRecognizer(
            click_pinch_distance=self.config['gestures']['click_pinch_distance'],
            control_mode=self.config['general'].get('control_mode', 'face_and_eyes')
        )
        self.mouse_controller = MouseController(self.screen_width, self.screen_height)
        
        smoothening = self.config['mouse'].get('smoothening', 5)
        min_cutoff = max(0.01, 1.0 / smoothening)
        beta = 0.5 
        
        self.filter_x = OneEuroFilter(mincutoff=min_cutoff, beta=beta)
        self.filter_y = OneEuroFilter(mincutoff=min_cutoff, beta=beta)

        self.view = UIView(self)
        self.view.set_initial_settings(self.config)

        self._running = False
        
        self.history_x = []
        self.history_y = []
        self.history_len = 3 

        keyboard.add_hotkey('ctrl+shift+m', self.toggle_tracking_hotkey)

    def load_config(self):
        if not os.path.exists('config.json'):
             return {
                "general": {"camera_id": 0, "control_mode": "face_and_eyes"},
                "mouse": {"smoothening": 5, "pointer_sensitivity": 1.5, "mirror_input": False},
                "gestures": {"click_pinch_distance": 0.15}
            }
        with open('config.json', 'r') as f:
            return json.load(f)
            
    def update_config(self, section, key, value):
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
            
            if key == 'control_mode':
                self.gesture_recognizer.control_mode = value
            elif key == 'smoothening':
                min_cutoff = max(0.01, 1.0 / value)
                self.filter_x.mincutoff = min_cutoff
                self.filter_y.mincutoff = min_cutoff
            
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)

    def toggle_tracking_hotkey(self):
        if self._running:
            self.view.after(0, self.stop)
            self.view.after(0, lambda: self.view.start_stop_button.configure(text="Start Tracking", bootstyle="success"))
        else:
            self.view.after(0, self.start)
            self.view.after(0, lambda: self.view.start_stop_button.configure(text="Stop Tracking", bootstyle="danger"))

    def start(self):
        if self.tracker is None:
            self.tracker = OmniTracker(camera_id=self.config['general']['camera_id'])
        self._running = True
        self.tracker.start()
        self.view.update_status("Running")
        
        self.filter_x = OneEuroFilter(mincutoff=self.filter_x.mincutoff, beta=self.filter_x.beta)
        self.filter_y = OneEuroFilter(mincutoff=self.filter_y.mincutoff, beta=self.filter_y.beta)
        self.mouse_controller.reset_acceleration()
        self.history_x.clear()
        self.history_y.clear()

    def stop(self):
        self._running = False
        if self.tracker:
            self.tracker.stop()
            self.tracker = None 
        self.view.update_status("Stopped")
        self.view.update_mode("N/A")

    def is_running(self):
        return self._running

    def run(self):
        if self._running:
            self.process_frame()
        
        if self.tracker:
            frame = self.tracker.get_annotated_frame()
            if frame is not None:
                self.view.update_video_feed(frame, mode=self.gesture_recognizer.mode, 
                                          pinching=self.gesture_recognizer.pinching)
        
        # High frequency poll (120Hz approx) for zero lag
        self.view.after(8, self.run)

    def process_frame(self):
        # Pull the absolute freshest result from the async queue
        results = self.tracker.get_results()
        if self.tracker:
             annotated_frame = self.tracker.get_annotated_frame()
             if annotated_frame is not None and results:
                frame_shape = annotated_frame.shape
                self.gesture_recognizer.update_result(results, frame_shape)
                actions = self.gesture_recognizer.recognize()
                for action, args in actions:
                    self.execute_action(action, args, frame_shape)

    def execute_action(self, action, args, frame_shape):
        sensitivity = self.config['mouse']['pointer_sensitivity']
        mirror = self.config['mouse'].get('mirror_input', False)

        if action == 'move':
            x1, y1 = args
            
            target_x = np.interp(x1, (50, frame_shape[1] - 50), (0, self.screen_width))
            target_y = np.interp(y1, (50, frame_shape[0] - 50), (0, self.screen_height))
            
            if mirror:
                target_x = self.screen_width - target_x

            center_x, center_y = self.screen_width / 2, self.screen_height / 2
            target_x = center_x + (target_x - center_x) * sensitivity
            target_y = center_y + (target_y - center_y) * sensitivity
            
            target_x = max(0, min(self.screen_width, target_x))
            target_y = max(0, min(self.screen_height, target_y))

            current_time = time.time()
            smooth_x = self.filter_x(current_time, target_x)
            smooth_y = self.filter_y(current_time, target_y)

            self.history_x.append(smooth_x)
            self.history_y.append(smooth_y)
            if len(self.history_x) > self.history_len:
                self.history_x.pop(0)
                self.history_y.pop(0)
            
            avg_x = sum(self.history_x) / len(self.history_x)
            avg_y = sum(self.history_y) / len(self.history_y)
            
            self.mouse_controller.move(avg_x, avg_y)

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
