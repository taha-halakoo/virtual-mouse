import pyautogui
import platform

class MouseController:
    """
    A wrapper for pyautogui to handle mouse control.
    This class is designed to be simple and can be expanded
    if more complex mouse interactions are needed.
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

    def move(self, x, y):
        """
        Moves the mouse to the specified (x, y) screen coordinates.

        Args:
            x (float): The target x-coordinate.
            y (float): The target y-coordinate.
        """
        # Ensure coordinates are within screen bounds
        x = min(max(x, 0), self.screen_width)
        y = min(max(y, 0), self.screen_height)
        pyautogui.moveTo(x, y)

    def left_click(self):
        """Performs a single left-click."""
        pyautogui.click(button='left')

    def right_click(self):
        """Performs a single right-click."""
        pyautogui.click(button='right')
        
    def double_click(self):
        """Performs a double left-click."""
        pyautogui.doubleClick()

    def scroll(self, amount):
        """
        Scrolls the mouse wheel.

        Args:
            amount (int): The amount to scroll. Positive for up, negative for down.
        """
        pyautogui.scroll(amount)

    def mouse_down(self):
        """Presses and holds the left mouse button."""
        pyautogui.mouseDown()

    def mouse_up(self):
        """Releases the left mouse button."""
        pyautogui.mouseUp()
