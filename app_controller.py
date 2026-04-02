import json
import time
import numpy as np
import pyautogui
import os
import math
import keyboard
import threading
import cv2
from PIL import ImageGrab
import subprocess

from ui_view import UIView
from omni_tracker import OmniTracker
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController
from one_euro_filter import OneEuroFilter, AcousticEnvironmentSync

class AppController:
    """
    Virtual Mouse v10 "Liquid Glass"
    Includes 95 Features spanning AI, Workflow, and Accessibility
    """
    def __init__(self):
        self.config = self.load_config()
        self.screen_width, self.screen_height = pyautogui.size()

        self._running = False
        self.tracker = None 
        self.gesture_recognizer = GestureRecognizer(config=self.config)
        self.mouse_controller = MouseController(self.screen_width, self.screen_height, config=self.config)
        
        # Feature 5: Acoustic Environment Syncing
        self.acoustic_sync = AcousticEnvironmentSync(enabled=self.config['advanced'].get('acoustic_sync', True))

        smoothening = self.config['mouse'].get('smoothening', 10)
        min_cutoff = max(0.01, 1.0 / smoothening)
        
        # Feature 44: Parkinson's Assist
        parkinsons = self.config['accessibility'].get('parkinsons_assist', False)
        
        self.filter_x = OneEuroFilter(mincutoff=min_cutoff, beta=self.config['advanced'].get('one_euro_beta', 0.5), parkinsons_assist=parkinsons, acoustic_sync=self.acoustic_sync)
        self.filter_y = OneEuroFilter(mincutoff=min_cutoff, beta=self.config['advanced'].get('one_euro_beta', 0.5), parkinsons_assist=parkinsons, acoustic_sync=self.acoustic_sync)

        self.view = UIView(self)
        self.view.set_initial_settings(self.config)

        keyboard.add_hotkey('ctrl+shift+m', self.toggle_tracking_hotkey)
        keyboard.add_hotkey('ctrl+shift+p', self.panic_gesture_hook)

        self.start_time = time.time()
        self.fatigue_warned = False

    def load_config(self):
        default_config = {
            "general": {
                "camera_id": 0, "multi_camera": False, "one_eye_mode": False,
                "low_cpu_mode": False, "auto_update": True, "privacy_shield": True
            },
            "mouse": {
                "smoothening": 10, "pointer_sensitivity": 1.5, "mirror_input": False,
                "drag_lock": False, "smooth_scroll_mult": 1.2, "sniper_mult": 0.2
            },
            "gestures": {
                "click_pinch_distance": 0.15, "swipe_threshold": 0.3, 
                "momentum_stop_enabled": True, "clipboard_gestures": True
            },
            "advanced": {
                "stress_relief_smoothing": True, "hand_size_normalization": True, 
                "one_euro_beta": 0.5, "ambient_light_hud": True, "acoustic_sync": True
            },
            "accessibility": {
                "parkinsons_assist": False, "color_blind_hud": False, 
                "high_contrast_halos": False, "audio_spatial_feedback": False
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
            if key == 'acoustic_sync':
                self.acoustic_sync.enabled = value
                if value: self.acoustic_sync.start()
                else: self.acoustic_sync.stop()
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)

    def toggle_tracking_hotkey(self):
        self.view.after(0, self.view.toggle_tracking)

    def panic_gesture_hook(self):
        pyautogui.hotkey('win', 'd')

    def start(self):
        if self.tracker is None:
            self.tracker = OmniTracker(camera_id=self.config['general']['camera_id'], multi_camera=self.config['general']['multi_camera'])
        self._running = True
        self.start_time = time.time()
        self.fatigue_warned = False
        self.tracker.start()
        self.filter_x.t_prev = None
        self.filter_y.t_prev = None
        self.mouse_controller.reset_acceleration()
        if self.config['advanced'].get('acoustic_sync', True):
            self.acoustic_sync.start()

    def stop(self):
        self._running = False
        if self.tracker:
            self.tracker.stop()
            self.tracker = None 
        self.acoustic_sync.stop()

    def is_running(self):
        return self._running

    def run(self):
        if self._running:
            self.process_frame()
        
        if self.tracker:
            frame = self.tracker.get_annotated_frame()
            if frame is not None:
                # 2. Ambient Light HUD
                if self.config['advanced']['ambient_light_hud']:
                    brightness = np.mean(frame)
                    if brightness < 50:
                        self.view.bg_color = "#000000"
                    elif brightness > 200:
                        self.view.bg_color = "#2A2A2A"
                    self.view.configure(background=self.view.bg_color)
                    self.view.canvas.configure(bg=self.view.bg_color)

                self.view.update_video_feed(frame, mode=self.gesture_recognizer.mode, 
                                          pinching=self.gesture_recognizer.pinching_left,
                                          config=self.config)
        
        self.view.after(8, self.run)

    def process_frame(self):
        if self.config['general']['low_cpu_mode']:
            time.sleep(0.016)

        results = self.tracker.get_results()
        if self.tracker:
             annotated_frame = self.tracker.get_annotated_frame()
             if annotated_frame is not None and results:
                
                if self.config['general']['privacy_shield'] and results.face_landmarks and len(results.face_landmarks) > 1:
                     annotated_frame[:] = cv2.blur(annotated_frame, (50, 50))

                frame_shape = annotated_frame.shape
                self.gesture_recognizer.update_result(results, frame_shape)
                actions = self.gesture_recognizer.recognize()
                
                # 93. Ergonomic Scorecard / Timer
                if time.time() - self.start_time > 3600 and not self.fatigue_warned:
                    actions.append(('notify', "STRETCH REMINDER: 1 HR"))
                    self.fatigue_warned = True

                for action, args in actions:
                    self.execute_action(action, args, frame_shape)

    def execute_action(self, action, args, frame_shape):
        if action == 'move':
            x, y = args
            current_time = time.time()
            if self.config['advanced']['stress_relief_smoothing']:
                t_prev = self.filter_x.t_prev if self.filter_x.t_prev is not None else current_time
                dt = current_time - t_prev
                if dt > 0:
                    x_prev = self.filter_x.x_prev if self.filter_x.x_prev is not None else x
                    y_prev = self.filter_y.x_prev if self.filter_y.x_prev is not None else y
                    vel = math.hypot(x - x_prev, y - y_prev) / dt
                    if vel > 2000:
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
            if self.config['accessibility'].get('audio_spatial_feedback', False):
                pass # Stereoscopic ping could be played here

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
            self.view.show_notification(args)

        # --- New V10 OS Integrations ---
        elif action == 'swipe_desktop':
            pyautogui.hotkey('ctrl', 'win', args)
            
        elif action == 'cad_orbit':
            # Feature 27: Middle click drag to rotate CAD
            zoom_delta, angle_delta = args
            pyautogui.scroll(int(zoom_delta * 10))
            if abs(angle_delta) > 0.1:
                # Simulate middle click dragging based on angle
                pyautogui.mouseDown(button='middle')
                dx = int(math.cos(angle_delta) * 50)
                dy = int(math.sin(angle_delta) * 50)
                pyautogui.moveRel(dx, dy)
                pyautogui.mouseUp(button='middle')
                
        elif action == 'trigger_screenshot':
            # Feature 30: Save screenshot to desktop
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            fname = os.path.join(desktop, f"AirGrab_{int(time.time())}.png")
            ImageGrab.grab().save(fname)
            self.view.show_notification("SCREENSHOT SAVED")
            
        elif action == 'ide_collapse':
            # Feature 39: VS Code collapse all
            pyautogui.hotkey('ctrl', 'k')
            pyautogui.hotkey('ctrl', '0')
            self.view.show_notification("CODE COLLAPSED")
            
        elif action == 'jedi_swipe':
            # Feature 33: Presentation control
            if args == 'next':
                pyautogui.press('pagedown')
            else:
                pyautogui.press('pageup')
                
        elif action == 'semantic_highlight':
            # Feature 24: Fast double click to highlight word contextually
            pyautogui.doubleClick()
            
        elif action == 'terminal_command':
            # Feature 40: Open Windows Terminal
            subprocess.Popen("cmd.exe")
            self.view.show_notification("TERMINAL OPENED")

if __name__ == "__main__":
    pass
