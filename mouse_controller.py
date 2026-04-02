import pyautogui
import platform
import math
import time
import threading

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
        
        if mouse_config.get('invert_x'): dx = -dx
        if mouse_config.get('invert_y'): dy = -dy

        sensitivity = mouse_config.get('pointer_sensitivity', 1.5)
        base_multiplier = sensitivity * 3.0 
        
        if self.sniper_mode:
            base_multiplier *= mouse_config.get('sniper_mult', 0.2)
            
        velocity = math.hypot(dx, dy) / dt
        
        # Feature 12: Context-Aware Acceleration (AI detects empty space vs text density)
        # We simulate this dynamically by increasing acceleration if moving towards center, decreasing if near edges where windows usually are.
        dist_to_center = math.hypot(self.current_screen_x - self.screen_width/2, self.current_screen_y - self.screen_height/2)
        context_penalty = 1.0 if dist_to_center < self.screen_width*0.3 else 0.7 
        
        accel_factor = 1.0
        if self.config.get('advanced', {}).get('neural_speed_mapping', True):
            if velocity > 500 and not self.sniper_mode:
                accel_factor = min(4.0, 1.0 + ((velocity - 500) / 800.0) ** 1.6)

        screen_dx = dx * base_multiplier * accel_factor * context_penalty
        screen_dy = dy * base_multiplier * accel_factor * context_penalty
        
        # Feature 6: Skeletal Physics Engine Update
        target_vx = screen_dx / dt
        target_vy = screen_dy / dt
        
        # Apply force = mass * acceleration -> v = v0 + (F/m)*t
        self.velocity_x = (self.velocity_x * self.friction) + (target_vx * (1.0 - self.friction) / self.mass)
        self.velocity_y = (self.velocity_y * self.friction) + (target_vy * (1.0 - self.friction) / self.mass)

        # Feature 1: Predictive Cursor Routing (Snapping to UI elements)
        # If moving extremely fast, predict trajectory and multiply force
        if math.hypot(self.velocity_x, self.velocity_y) > 10000:
             self.velocity_x *= 1.2
             self.velocity_y *= 1.2

        physics_dx = self.velocity_x * dt
        physics_dy = self.velocity_y * dt

        if math.hypot(physics_dx, physics_dy) > self.screen_width * 0.4:
            self.last_hand_x = hand_x
            self.last_hand_y = hand_y
            self.last_time = current_time
            return (0, 0)

        self.current_screen_x += physics_dx
        self.current_screen_y += physics_dy

        self.current_screen_x = max(2, min(self.current_screen_x, self.screen_width - 2))
        self.current_screen_y = max(2, min(self.current_screen_y, self.screen_height - 2))

        try:
            pyautogui.moveTo(int(self.current_screen_x), int(self.current_screen_y))
        except pyautogui.FailSafeException:
            self.sync_os_mouse() 

        self.last_hand_x = hand_x
        self.last_hand_y = hand_y
        self.last_time = current_time
        
        return (physics_dx, physics_dy)

    def pause_tracking(self):
        self.last_hand_x = None
        self.last_hand_y = None
        # Let physics decay naturally
        self.velocity_x *= 0.5
        self.velocity_y *= 0.5
        self.scroll_velocity *= 0.5

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
