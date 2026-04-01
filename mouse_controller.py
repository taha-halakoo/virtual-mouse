import pyautogui
import platform
import math
import time

class MouseController:
    """
    Virtual Mouse v5.0: Trackpad Relative Controller
    Fully Integrated with 75+ Features Configurations.
    """

    def __init__(self, screen_width, screen_height, config=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = config or {}
        
        pyautogui.FAILSAFE = True
        
        if platform.system() != 'Windows':
            pyautogui.PAUSE = 0.01
        else:
            pyautogui.PAUSE = 0.0

        self.last_hand_x = None
        self.last_hand_y = None
        self.last_time = time.time()
        
        self.current_screen_x = self.screen_width / 2
        self.current_screen_y = self.screen_height / 2
        
        self.sniper_mode = False
        
        # 7. Neural Speed Mapping History
        self.velocity_history = []

    def sync_os_mouse(self):
        try:
            x, y = pyautogui.position()
            self.current_screen_x = x
            self.current_screen_y = y
        except Exception:
            pass

    def set_sniper_mode(self, enabled):
        self.sniper_mode = enabled

    def move(self, hand_x, hand_y):
        current_time = time.time()
        dt = current_time - self.last_time
        
        if self.last_hand_x is None or dt == 0 or dt > 0.1:
            self.last_hand_x = hand_x
            self.last_hand_y = hand_y
            self.last_time = current_time
            self.sync_os_mouse()
            return (0, 0)

        dx = hand_x - self.last_hand_x
        dy = hand_y - self.last_hand_y
        
        mouse_config = self.config.get('mouse', {})
        
        # 51. Invert Axes
        if mouse_config.get('invert_x'): dx = -dx
        if mouse_config.get('invert_y'): dy = -dy

        # 5. Magnetic Buttons (Mock implementation: slow down near specific regions)
        # Not fully implemented without OS hooking, but base structure is here.

        sensitivity = mouse_config.get('pointer_sensitivity', 1.5)
        base_multiplier = sensitivity * 3.0 
        
        if self.sniper_mode:
            base_multiplier *= mouse_config.get('sniper_mult', 0.2)
            
        velocity = math.hypot(dx, dy) / dt
        
        # 7. Neural Speed Mapping
        accel_factor = 1.0
        if self.config.get('advanced', {}).get('neural_speed_mapping', True):
            if velocity > 500 and not self.sniper_mode:
                accel_factor = min(4.0, 1.0 + ((velocity - 500) / 800.0) ** 1.6)

        screen_dx = dx * base_multiplier * accel_factor
        screen_dy = dy * base_multiplier * accel_factor
        
        # Outlier Rejection
        if math.hypot(screen_dx, screen_dy) > self.screen_width * 0.4:
            self.last_hand_x = hand_x
            self.last_hand_y = hand_y
            self.last_time = current_time
            return (0, 0)

        self.current_screen_x += screen_dx
        self.current_screen_y += screen_dy

        # Clamp
        self.current_screen_x = max(2, min(self.current_screen_x, self.screen_width - 2))
        self.current_screen_y = max(2, min(self.current_screen_y, self.screen_height - 2))

        try:
            pyautogui.moveTo(self.current_screen_x, self.current_screen_y)
        except pyautogui.FailSafeException:
            self.sync_os_mouse() 

        self.last_hand_x = hand_x
        self.last_hand_y = hand_y
        self.last_time = current_time
        
        return (screen_dx, screen_dy)

    def pause_tracking(self):
        self.last_hand_x = None
        self.last_hand_y = None

    def reset_acceleration(self):
        self.pause_tracking()
        self.velocity_history.clear()

    def left_click(self):
        pyautogui.click(button='left')

    def right_click(self):
        pyautogui.click(button='right')
        
    def double_click(self):
        pyautogui.doubleClick()

    def scroll(self, amount):
        pyautogui.scroll(amount)

    def mouse_down(self):
        pyautogui.mouseDown()

    def mouse_up(self):
        pyautogui.mouseUp()
