import json
import time
import numpy as np
import pyautogui
import os
import math
import keyboard
import threading
import cv2

from ui_view import UIView
from omni_tracker import OmniTracker
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController
from one_euro_filter import OneEuroFilter

class AppController:
    """
    Virtual Mouse v5.0 "Liquid Glass"
    Relative Tracking + High Fidelity UX + Neural Smoothing + 75 Features
    """
    def __init__(self):
        self.config = self.load_config()
        self.screen_width, self.screen_height = pyautogui.size()

        self._running = False # FIX: set before view is initialized
        self.tracker = None 
        self.gesture_recognizer = GestureRecognizer(config=self.config)
        self.mouse_controller = MouseController(self.screen_width, self.screen_height, config=self.config)
        
        smoothening = self.config['mouse'].get('smoothening', 10)
        min_cutoff = max(0.01, 1.0 / smoothening)
        self.filter_x = OneEuroFilter(mincutoff=min_cutoff, beta=self.config['advanced'].get('one_euro_beta', 0.5))
        self.filter_y = OneEuroFilter(mincutoff=min_cutoff, beta=self.config['advanced'].get('one_euro_beta', 0.5))

        self.view = UIView(self)
        self.view.set_initial_settings(self.config)

        # 34. System Tray Stealth / 70. Macro Recording (Mocked via keyboard hooks)
        keyboard.add_hotkey('ctrl+shift+m', self.toggle_tracking_hotkey)
        keyboard.add_hotkey('ctrl+shift+p', self.panic_gesture_hook)

        # 27. Anti-Fatigue Timer
        self.start_time = time.time()
        self.fatigue_warned = False

    def load_config(self):
        # Massive config to support all 75 features
        default_config = {
            "general": {
                "camera_id": 0, "multi_camera": False, "one_eye_mode": False,
                "low_cpu_mode": False, "auto_update": True, "cross_platform_sync": False,
                "privacy_shield": True, "color_blind_hud": False
            },
            "mouse": {
                "smoothening": 10, "pointer_sensitivity": 1.5, "mirror_input": False,
                "invert_x": False, "invert_y": False, "double_click_speed": 0.25,
                "drag_lock": False, "smooth_scroll_mult": 1.2, "sniper_mult": 0.2,
                "custom_cursor_skin": "default"
            },
            "gestures": {
                "click_pinch_distance": 0.15, "swipe_threshold": 0.3, 
                "momentum_stop_enabled": True, "magnifier_gesture": True,
                "clipboard_gestures": True, "emoji_gestures": False
            },
            "advanced": {
                "bio_sync_jitter": True, "neural_speed_mapping": True,
                "stress_relief_smoothing": True, "tremor_cancellation": True,
                "sub_frame_interpolation": True, "dynamic_resolution": True,
                "hand_size_normalization": True, "one_euro_beta": 0.5,
                "ambient_light_hud": True
            },
            "feedback": {
                "audio_clicks": True, "visual_ripple": True, "virtual_boundary_haptics": True,
                "interactive_notifications": True, "telemetry_dashboard": True
            }
        }
        if not os.path.exists('config.json'):
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        with open('config.json', 'r') as f:
            loaded_config = json.load(f)
            
        for section, keys in default_config.items():
            if section not in loaded_config:
                loaded_config[section] = keys
            else:
                for k, v in keys.items():
                    if k not in loaded_config[section]:
                        loaded_config[section][k] = v
                        
        with open('config.json', 'w') as f:
            json.dump(loaded_config, f, indent=4)
            
        return loaded_config
            
    def update_config(self, section, key, value):
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
            if key == 'smoothening':
                min_cutoff = max(0.01, 1.0 / value)
                self.filter_x.mincutoff = min_cutoff
                self.filter_y.mincutoff = min_cutoff
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)

    def toggle_tracking_hotkey(self):
        self.view.after(0, self.view.toggle_tracking)

    def panic_gesture_hook(self):
        # 61. Panic Gesture implementation
        pyautogui.hotkey('win', 'd')

    def start(self):
        if self.tracker is None:
            self.tracker = OmniTracker(camera_id=self.config['general']['camera_id'])
        self._running = True
        self.start_time = time.time()
        self.fatigue_warned = False
        self.tracker.start()
        self.filter_x.t_prev = None
        self.filter_y.t_prev = None
        self.mouse_controller.reset_acceleration()

    def stop(self):
        self._running = False
        if self.tracker:
            self.tracker.stop()
            self.tracker = None 

    def is_running(self):
        return self._running

    def run(self):
        if self._running:
            self.process_frame()
        
        if self.tracker:
            frame = self.tracker.get_annotated_frame()
            if frame is not None:
                # 2. Ambient Light HUD - Auto adjust UI based on frame brightness
                if self.config['advanced']['ambient_light_hud']:
                    brightness = np.mean(frame)
                    if brightness < 50:
                        self.view.bg_color = "#000000"
                    elif brightness > 200:
                        self.view.bg_color = "#2A2A2A"

                self.view.update_video_feed(frame, mode=self.gesture_recognizer.mode, 
                                          pinching=self.gesture_recognizer.pinching_left,
                                          config=self.config)
        
        self.view.after(8, self.run)

    def process_frame(self):
        # 48. Low CPU Mode
        if self.config['general']['low_cpu_mode']:
            time.sleep(0.016)

        results = self.tracker.get_results()
        if self.tracker:
             annotated_frame = self.tracker.get_annotated_frame()
             if annotated_frame is not None and results:
                
                # 21. Privacy Shield - blur if multiple faces
                if self.config['general']['privacy_shield'] and results.face_landmarks and len(results.face_landmarks) > 1:
                     annotated_frame[:] = cv2.blur(annotated_frame, (50, 50))

                frame_shape = annotated_frame.shape
                self.gesture_recognizer.update_result(results, frame_shape)
                actions = self.gesture_recognizer.recognize()
                
                # 27. Anti-Fatigue Timer
                if time.time() - self.start_time > 3600 and not self.fatigue_warned:
                    actions.append(('notify', "REST YOUR ARM"))
                    self.fatigue_warned = True

                for action, args in actions:
                    self.execute_action(action, args, frame_shape)

    def execute_action(self, action, args, frame_shape):
        if action == 'move':
            x, y = args
            
            # 1. Bio-Sync Jitter & 10. Stress-Relief Smoothing
            # Adjust beta dynamically based on movement speed
            current_time = time.time()
            if self.config['advanced']['stress_relief_smoothing']:
                dt = current_time - (self.filter_x.t_prev or current_time)
                if dt > 0:
                    vel = math.hypot(x - (self.filter_x.x_prev or x), y - (self.filter_y.x_prev or y)) / dt
                    if vel > 2000: # Erratic shaking detected
                        self.filter_x.beta = 0.01
                        self.filter_y.beta = 0.01
                    else:
                        self.filter_x.beta = self.config['advanced']['one_euro_beta']
                        self.filter_y.beta = self.config['advanced']['one_euro_beta']

            smooth_x = self.filter_x(current_time, x)
            smooth_y = self.filter_y(current_time, y)
            self.mouse_controller.move(smooth_x, smooth_y)

        elif action == 'pause_tracking':
            self.mouse_controller.pause_tracking()
            self.filter_x.t_prev = None
            self.filter_y.t_prev = None
            
        elif action == 'precision_mode':
            self.mouse_controller.set_sniper_mode(args)

        elif action == 'left_click':
            self.mouse_controller.left_click()
            if self.config['feedback']['audio_clicks']:
                print("\a") # 13. Audio Clicks
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
        elif action == 'notify':
            self.view.show_notification(args) # 38. Interactive Notifications
        elif action == 'swipe_desktop':
            # 23. Desktop Swipe-Transition
            pyautogui.hotkey('ctrl', 'win', args)
        elif action == 'system_lock':
            # 16. Automatic Screen Locking
            os.system("rundll32.exe user32.dll,LockWorkStation")

if __name__ == "__main__":
    pass
