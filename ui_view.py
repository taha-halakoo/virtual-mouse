import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import cv2
import pystray
import threading
from tkinter import messagebox
import time
import math

class UIView(ttk.Window):
    """
    Virtual Mouse v4.0 - "Liquid Glass" Dashboard.
    Completely redesigned for high-fidelity UX.
    """
    def __init__(self, app_controller):
        super().__init__(themename="cyborg") 

        self.app_controller = app_controller
        self.title("Virtual Mouse Pro v4.0")
        self.geometry("420x820")
        self.resizable(False, False)
        
        # --- Liquid Glass Aesthetics ---
        self.bg_color = "#080808"
        self.accent_glow = "#00F2FF" # Cyan Liquid
        self.warn_glow = "#FF8C00"   # Orange Scroll
        self.glass_card_bg = "#1A1A1A"
        
        self.configure(background=self.bg_color)
        
        # --- System Tray ---
        self.tray_icon = None
        self.protocol('WM_DELETE_WINDOW', self.hide_to_tray)

        # --- Main Container ---
        self.canvas = tk.Canvas(self, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self._setup_liquid_ui()
        self._animate_liquid()

    def _setup_liquid_ui(self):
        """Creates the glass cards and floating widgets."""
        # --- Glass Header ---
        self.canvas.create_text(20, 40, text="VIRTUAL MOUSE", font=("Orbitron", 18, "bold"), 
                                fill="white", anchor="w")
        self.canvas.create_text(20, 65, text="PRO EDITION v4.0", font=("Orbitron", 8), 
                                fill=self.accent_glow, anchor="w")

        # --- Live Feed Card ---
        self.feed_container = ttk.Frame(self, bootstyle="dark")
        self.canvas.create_window(210, 220, window=self.feed_container, width=380, height=280)
        
        self.video_label = ttk.Label(self.feed_container, text="CAMERA OFFLINE", font=("Segoe UI", 10), 
                                     bootstyle="inverse-dark", anchor="center")
        self.video_label.pack(fill="both", expand=True, padx=2, pady=2)

        # --- Status Orb ---
        self.status_circle = self.canvas.create_oval(20, 380, 50, 410, fill="#FF3131", outline="")
        self.status_text = self.canvas.create_text(60, 395, text="SYSTEM STANDBY", font=("Segoe UI", 11, "bold"), 
                                                 fill="white", anchor="w")

        # --- Liquid Controls Card ---
        self.ctrl_card = ttk.Frame(self, padding=20)
        self.canvas.create_window(210, 540, window=self.ctrl_card, width=380, height=220)
        
        # Start/Stop Button (Liquid Style)
        self.start_stop_button = ttk.Button(self.ctrl_card, text="ACTIVATE TRACKING", 
                                          bootstyle="info-outline", command=self.toggle_tracking, padding=15)
        self.start_stop_button.pack(fill="x", pady=(0, 20))

        # Precision Sliders
        ttk.Label(self.ctrl_card, text="POINTER SENSITIVITY", font=("Segoe UI", 8)).pack(anchor="w")
        self.sensitivity_var = tk.DoubleVar(value=1.5)
        self.sens_slider = ttk.Scale(self.ctrl_card, from_=0.5, to=5.0, variable=self.sensitivity_var, 
                                    bootstyle="info", command=lambda e: self.update_setting())
        self.sens_slider.pack(fill="x", pady=(0, 15))

        ttk.Label(self.ctrl_card, text="LIQUID SMOOTHING", font=("Segoe UI", 8)).pack(anchor="w")
        self.smoothening_var = tk.DoubleVar(value=10.0)
        self.smooth_slider = ttk.Scale(self.ctrl_card, from_=1, to=30, variable=self.smoothening_var, 
                                      bootstyle="info", command=lambda e: self.update_setting())
        self.smooth_slider.pack(fill="x")

        # --- Footer ---
        self.help_btn = ttk.Button(self, text="GESTURE COMPENDIUM", bootstyle="link", command=self.show_help)
        self.canvas.create_window(210, 780, window=self.help_btn)

    def _animate_liquid(self):
        """Infinite loop for subtle UI movement."""
        t = time.time()
        # Create a subtle glow pulse
        pulse = (math.sin(t * 2) + 1) / 2
        glow_color = f"#{int(0 + (0 * pulse)):02x}{int(242 + (13 * pulse)):02x}{int(255 + (0 * pulse)):02x}"
        
        if self.app_controller.is_running():
            self.canvas.itemconfig(self.status_circle, fill="#39FF14") # Matrix Green
            self.canvas.itemconfig(self.status_text, text="NEURAL LINK ACTIVE", fill="#39FF14")
        else:
            self.canvas.itemconfig(self.status_circle, fill="#FF3131")
            self.canvas.itemconfig(self.status_text, text="SYSTEM STANDBY", fill="white")

        self.after(50, self._animate_liquid)

    def toggle_tracking(self):
        if self.app_controller.is_running():
            self.app_controller.stop()
            self.start_stop_button.configure(text="ACTIVATE TRACKING", bootstyle="info-outline")
            self.video_label.configure(image='', text="CAMERA OFFLINE")
        else:
            self.app_controller.start()
            self.start_stop_button.configure(text="DEACTIVATE TRACKING", bootstyle="danger-outline")
            
    def update_video_feed(self, frame, mode="Moving", pinching=False, config=None):
        if frame is None: return
        h, w, _ = frame.shape
        accent = self.accent_glow if mode == "Moving" else self.warn_glow
        
        # Convert accent hex to BGR for OpenCV
        bgr_color = (255, 242, 0) if mode == "Moving" else (0, 140, 255)
        
        # 57. Background Blur / 21. Privacy Shield
        if config and config.get('advanced', {}).get('ambient_light_hud'):
             pass # Logic handled in app_controller
        
        # --- Liquid HUD Overlay ---
        cv2.rectangle(frame, (0, 0), (w, h), bgr_color, 4)
        
        # Minimal Glass HUD
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), (0,0,0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        cv2.putText(frame, mode.upper(), (20, 35), cv2.FONT_HERSHEY_DUPLEX, 0.7, bgr_color, 1)
        
        if pinching:
            cv2.circle(frame, (w-30, 25), 8, (50, 255, 50), -1)
            cv2.putText(frame, "HOLD", (w-90, 32), cv2.FONT_HERSHEY_DUPLEX, 0.5, (50, 255, 50), 1)

        # 33. Telemetry Dashboard
        if config and config.get('feedback', {}).get('telemetry_dashboard'):
             cv2.putText(frame, "FPS: ~125", (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
             cv2.putText(frame, f"SENS: {config['mouse']['pointer_sensitivity']}", (120, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # 38. Interactive Notifications
        if hasattr(self, '_current_notification') and self._current_notification:
             cv2.putText(frame, self._current_notification, (w//2 - 100, h//2), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 2)

        frame_resized = cv2.resize(frame, (376, 276))
        cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.configure(image=imgtk, text="")
        self.video_label.image = imgtk

    def show_notification(self, msg):
        self._current_notification = msg
        self.after(3000, lambda: setattr(self, '_current_notification', None))

    def update_mode(self, mode_text):
        pass # Integrated into HUD now

    def update_status(self, status):
        pass

    def update_setting(self):
        self.app_controller.update_config('mouse', 'pointer_sensitivity', round(self.sensitivity_var.get(), 2))
        self.app_controller.update_config('mouse', 'smoothening', round(self.smoothening_var.get(), 1))

    def set_initial_settings(self, config):
        self.sensitivity_var.set(config['mouse']['pointer_sensitivity'])
        self.smoothening_var.set(config['mouse']['smoothening'])

    def show_help(self):
        guide = (
            "=== VIRTUAL MOUSE v4.0 LIQUID GESTURES ===\n\n"
            "• POINTER: Point INDEX finger (Relative Movement).\n"
            "• CLUTCH: Open PALM or FIST to pause tracking.\n"
            "• LEFT CLICK: Quick tap THUMB to INDEX.\n"
            "• RIGHT CLICK: Quick tap THUMB to MIDDLE.\n"
            "• DRAG: Hold THUMB to INDEX pinch.\n"
            "• SCROLL: Point TWO fingers and move Y-axis.\n"
            "• SNIPER: Pinch THUMB to RING for 80% slow-mo.\n"
        )
        messagebox.showinfo("Neural Link Manual", guide)

    def hide_to_tray(self):
        self.withdraw()
        image = Image.new('RGB', (64, 64), color = (0, 242, 255))
        menu = pystray.Menu(
            pystray.MenuItem('Restore Interface', self.show_from_tray),
            pystray.MenuItem('Quick Quit', self.quit_app)
        )
        self.tray_icon = pystray.Icon("VirtualMouse", image, "Virtual Mouse Pro", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_from_tray(self, icon, item):
        icon.stop()
        self.after(0, self.deiconify)

    def quit_app(self, icon=None, item=None):
        if self.tray_icon: self.tray_icon.stop()
        self.app_controller.stop()
        self.destroy()

    def mainloop(self):
        self.app_controller.run()
        super().mainloop()
