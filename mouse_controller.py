import pyautogui
import platform
import math
import time

class MouseController:
    """
    Advanced Mouse Controller with Non-Linear Acceleration (Sniper/Sprint Mode).
    """

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Disable the fail-safe to allow moving the mouse to the corner
        pyautogui.FAILSAFE = False
        
        # Set a shorter pause after each call on non-Windows systems
        # to improve responsiveness.
        if platform.system() != 'Windows':
            pyautogui.PAUSE = 0.01

        # Acceleration state
        self.last_x = None
        self.last_y = None
        self.last_time = time.time()

    def move(self, x, y):
        """
        Moves the mouse with dynamic acceleration.
        Slow physical movement = ultra low sensitivity (pixel precision)
        Fast physical movement = high sensitivity (screen crossing)
        """
        current_time = time.time()
        dt = current_time - self.last_time
        
        if self.last_x is None or dt == 0:
            self.last_x, self.last_y = x, y
            self.last_time = current_time
            # Ensure coordinates are within screen bounds
            target_x = min(max(x, 0), self.screen_width)
            target_y = min(max(y, 0), self.screen_height)
            pyautogui.moveTo(target_x, target_y)
            return

        # Calculate physical velocity of the hand (pixels per second)
        dx = x - self.last_x
        dy = y - self.last_y
        velocity = math.hypot(dx, dy) / dt

        # Non-Linear Acceleration Curve
        # Base multiplier is 1.0. 
        # If moving slower than 100px/s, it drops (Sniper Mode).
        # If moving faster, it scales up exponentially (Sprint Mode).
        accel_factor = 1.0
        
        if velocity < 150:
            # Sniper Mode: Reduce sensitivity by up to 50% for tiny, precise movements
            accel_factor = max(0.5, velocity / 150.0)
        elif velocity > 500:
            # Sprint Mode: Increase sensitivity exponentially for fast flicks
            accel_factor = min(3.0, 1.0 + ((velocity - 500) / 1000.0) ** 1.5)

        # Apply acceleration to the delta
        accelerated_dx = dx * accel_factor
        accelerated_dy = dy * accel_factor

        # Calculate new absolute position based on accelerated delta
        new_x = self.last_x + accelerated_dx
        new_y = self.last_y + accelerated_dy

        # Clamp to screen
        target_x = min(max(new_x, 0), self.screen_width)
        target_y = min(max(new_y, 0), self.screen_height)

        pyautogui.moveTo(target_x, target_y)

        # Update state for next frame based on the ACTUAL cursor position
        # not the raw hand position, to maintain the "gearing" ratio
        self.last_x, self.last_y = target_x, target_y
        self.last_time = current_time

    def reset_acceleration(self):
        """Called when tracking resumes or mode switches to prevent sudden jumps."""
        self.last_x = None
        self.last_y = None

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
