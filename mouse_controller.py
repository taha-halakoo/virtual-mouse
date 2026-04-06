import pyautogui
import platform
import math
import time
import threading
import keyboard

class MouseController:
    """
    Virtual Mouse v10: Advanced Kinematic Controller
    Features: Physics Engine, Predictive Routing, Zero-G Scrolling
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
        
        # Feature 6: Skeletal Physics Engine (Mass, Velocity, Friction)
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.mass = 1.2
        self.friction = 0.85
        
        # Feature 20: Zero-Gravity Scrolling
        self.scroll_velocity = 0.0
        self.scrolling_active = False
        self._scroll_thread = threading.Thread(target=self._zero_g_scroll_loop, daemon=True)
        self._scroll_thread.start()

    def sync_os_mouse(self):
        try:
            x, y = pyautogui.position()
            self.current_screen_x = x
            self.current_screen_y = y
        except Exception:
            pass

    def set_sniper_mode(self, enabled):
        self.sniper_mode = enabled

    def move_relative(self, dx, dy, hand_scale=0.1):
        current_time = time.time()
        dt = current_time - self.last_time
        if dt == 0: dt = 0.001
        
        self.last_time = current_time
        
        mouse_config = self.config.get('mouse', {})
        if mouse_config.get('invert_x'): dx = -dx
        if mouse_config.get('invert_y'): dy = -dy

        # Snap-to-grid (Shift)
        if keyboard.is_pressed('shift'):
            if abs(dx) > abs(dy):
                dy = 0
            else:
                dx = 0

        sensitivity = mouse_config.get('pointer_sensitivity', 1.5)
        base_multiplier = sensitivity * 3.0 
        
        if self.sniper_mode:
            base_multiplier *= mouse_config.get('sniper_mult', 0.2)
            
        velocity = math.hypot(dx, dy) / dt
        
        # Dwell-to-click
        if self.config.get('accessibility', {}).get('dwell_to_click', False):
            if velocity < 15:
                if not hasattr(self, 'dwell_start_time'):
                    self.dwell_start_time = current_time
                elif current_time - self.dwell_start_time > 1.2:
                    self.left_click()
                    self.dwell_start_time = current_time + 1.0 # cooldown
            else:
                if hasattr(self, 'dwell_start_time'):
                    del self.dwell_start_time

        # Dynamic acceleration curve
        accel_factor = 1.0
        if velocity > 50:
            accel_factor = min(4.0, 1.0 + ((velocity - 50) / 500.0) ** 1.5)

        # Z-Axis Depth Scaling
        z_scale_factor = 1.0
        if self.config.get('advanced', {}).get('z_axis_scaling', True) and hand_scale > 0.01:
            z_scale_factor = 0.15 / hand_scale
            z_scale_factor = max(0.5, min(z_scale_factor, 2.5))

        screen_dx = dx * base_multiplier * accel_factor * z_scale_factor
        screen_dy = dy * base_multiplier * accel_factor * z_scale_factor
        
        target_vx = screen_dx / dt
        target_vy = screen_dy / dt
        
        self.velocity_x = (self.velocity_x * self.friction) + (target_vx * (1.0 - self.friction) / self.mass)
        self.velocity_y = (self.velocity_y * self.friction) + (target_vy * (1.0 - self.friction) / self.mass)

        physics_dx = self.velocity_x * dt
        physics_dy = self.velocity_y * dt

        self.current_screen_x += physics_dx
        self.current_screen_y += physics_dy

        self.current_screen_x = max(2, min(self.current_screen_x, self.screen_width - 2))
        self.current_screen_y = max(2, min(self.current_screen_y, self.screen_height - 2))

        # Smooth Edge-Pan
        if self.config.get('mouse', {}).get('smooth_edge_pan', True):
            pan_speed = 12
            if self.current_screen_y <= 5:
                self.scroll(pan_speed)
            elif self.current_screen_y >= self.screen_height - 5:
                self.scroll(-pan_speed)

        try:
            pyautogui.moveTo(int(self.current_screen_x), int(self.current_screen_y))
        except pyautogui.FailSafeException:
            self.sync_os_mouse() 
            
        return (physics_dx, physics_dy)

    def pause_tracking(self):
        self.last_hand_x = None
        self.last_hand_y = None
        self.velocity_x *= 0.5
        self.velocity_y *= 0.5
        self.scroll_velocity *= 0.5
        self.sync_os_mouse() # Sync on pause to avoid drift

    def reset_acceleration(self):
        self.pause_tracking()
        self.velocity_x = 0
        self.velocity_y = 0

    def left_click(self):
        pyautogui.click(button='left')

    def right_click(self):
        pyautogui.click(button='right')
        
    def double_click(self):
        pyautogui.doubleClick()

    def scroll(self, amount):
        # Feature 20: Zero-Gravity Scrolling - inject momentum
        self.scroll_velocity += amount * 0.5
        self.scrolling_active = True

    def _zero_g_scroll_loop(self):
        """Background thread applying momentum-based scrolling."""
        while True:
            if self.scrolling_active and abs(self.scroll_velocity) > 0.1:
                try:
                    pyautogui.scroll(int(self.scroll_velocity))
                except Exception:
                    pass
                # Apply friction
                self.scroll_velocity *= 0.90
            else:
                self.scroll_velocity = 0
            time.sleep(0.016) # ~60fps scroll updates

    def mouse_down(self):
        pyautogui.mouseDown()

    def mouse_up(self):
        pyautogui.mouseUp()
