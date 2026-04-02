import tkinter as tk
import ttkbootstrap as ttk
# from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import cv2
import pystray
import threading
from tkinter import messagebox
import time
import math
import numpy as np

class MinorityReportDashboard(tk.Toplevel):
    """
    Feature 76: The "Minority Report" Dashboard
    A full-screen, translucent UI overlay for immersive sorting.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.attributes('-fullscreen', True)
        self.attributes('-alpha', 0.8) # Translucent
        self.configure(bg='black')
        self.wm_attributes("-topmost", True)
        
        self.canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Draw sci-fi grid
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        for i in range(0, w, 100):
            self.canvas.create_line(i, 0, i, h, fill='#00F2FF', stipple='gray50')
        for i in range(0, h, 100):
            self.canvas.create_line(0, i, w, i, fill='#00F2FF', stipple='gray50')
            
        self.canvas.create_text(w//2, h//2, text="MINORITY REPORT DASHBOARD ACTIVE", font=("Orbitron", 40, "bold"), fill="#00F2FF")
        self.canvas.create_text(w//2, h//2 + 60, text="SWIPE DESKTOP TO CLOSE", font=("Orbitron", 20), fill="white")
        
        # Auto-close after a few seconds for this implementation
        self.after(5000, self.destroy)

class UIView(ttk.Window):
    """
    Virtual Mouse v10 - "Liquid Glass" Dashboard.
    Featuring Minority Report overlays, Sensory Deprivation, and APM tracking.
    """
    def __init__(self, app_controller):
        super().__init__(themename="cyborg") 

        self.app_controller = app_controller
        self.title("Virtual Mouse Pro v10")
        self.geometry("420x820")
        self.resizable(False, False)
        
        self.bg_color = "#080808"
        self.accent_glow = "#00F2FF"
        self.warn_glow = "#FF8C00"
        
        self.configure(background=self.bg_color)
        
        self.tray_icon = None
        self.protocol('WM_DELETE_WINDOW', self.hide_to_tray)

        self.canvas = tk.Canvas(self, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Feature 91: APM Tracker
        self.action_count = 0
        self.apm_start_time = time.time()
        
        # Feature 80: Particle Trail Feedback
        self.particles = []

        self._setup_liquid_ui()
        self._animate_liquid()

    def increment_apm(self):
        self.action_count += 1

    def _setup_liquid_ui(self):
        self.canvas.create_text(20, 40, text="VIRTUAL MOUSE", font=("Orbitron", 18, "bold"), fill="white", anchor="w")
        self.canvas.create_text(20, 65, text="PRO EDITION v10", font=("Orbitron", 8), fill=self.accent_glow, anchor="w")

        self.feed_container = ttk.Frame(self, bootstyle="dark")
        self.canvas.create_window(210, 220, window=self.feed_container, width=380, height=280)
        
        self.video_label = ttk.Label(self.feed_container, text="CAMERA OFFLINE", font=("Segoe UI", 10), bootstyle="inverse-dark", anchor="center")
        self.video_label.pack(fill="both", expand=True, padx=2, pady=2)

        self.status_circle = self.canvas.create_oval(20, 380, 50, 410, fill="#FF3131", outline="")
        self.status_text = self.canvas.create_text(60, 395, text="SYSTEM STANDBY", font=("Segoe UI", 11, "bold"), fill="white", anchor="w")

        # Minority Report Toggle
        self.mr_btn = ttk.Button(self, text="LAUNCH SPATIAL DASHBOARD", bootstyle="info-outline", command=self.launch_minority_report)
        self.canvas.create_window(210, 450, window=self.mr_btn, width=380)

        self.ctrl_card = ttk.Frame(self, padding=20)
        self.canvas.create_window(210, 580, window=self.ctrl_card, width=380, height=220)
        
        self.start_stop_button = ttk.Button(self.ctrl_card, text="ACTIVATE TRACKING", bootstyle="info", command=self.toggle_tracking, padding=15)
        self.start_stop_button.pack(fill="x", pady=(0, 20))

        ttk.Label(self.ctrl_card, text="POINTER SENSITIVITY", font=("Segoe UI", 8)).pack(anchor="w")
        self.sensitivity_var = tk.DoubleVar(value=1.5)
        self.sens_slider = ttk.Scale(self.ctrl_card, from_=0.5, to=5.0, variable=self.sensitivity_var, bootstyle="info", command=lambda e: self.update_setting())
        self.sens_slider.pack(fill="x", pady=(0, 15))

        ttk.Label(self.ctrl_card, text="LIQUID SMOOTHING", font=("Segoe UI", 8)).pack(anchor="w")
        self.smoothening_var = tk.DoubleVar(value=10.0)
        self.smooth_slider = ttk.Scale(self.ctrl_card, from_=1, to=30, variable=self.smoothening_var, bootstyle="info", command=lambda e: self.update_setting())
        self.smooth_slider.pack(fill="x")

    def launch_minority_report(self):
        MinorityReportDashboard(self)

    def _animate_liquid(self):
        if self.app_controller.is_running():
            self.canvas.itemconfig(self.status_circle, fill="#39FF14")
            self.canvas.itemconfig(self.status_text, text="NEURAL LINK ACTIVE", fill="#39FF14")
        else:
            self.canvas.itemconfig(self.status_circle, fill="#FF3131")
            self.canvas.itemconfig(self.status_text, text="SYSTEM STANDBY", fill="white")

        self.after(50, self._animate_liquid)

    def toggle_tracking(self):
        if self.app_controller.is_running():
            self.app_controller.stop()
            self.start_stop_button.configure(text="ACTIVATE TRACKING", bootstyle="info")
            self.video_label.configure(image='', text="CAMERA OFFLINE")
        else:
            self.app_controller.start()
            self.start_stop_button.configure(text="DEACTIVATE TRACKING", bootstyle="danger")
            self.apm_start_time = time.time()
            self.action_count = 0
            
    def update_video_feed(self, frame, mode="Moving", pinching=False, config=None):
        if frame is None: return
        h, w, _ = frame.shape
        
        # Feature 85: Sensory Deprivation Mode (Blackout everything except HUD elements)
        if config and config.get('advanced', {}).get('sensory_deprivation', False):
            frame = np.zeros_like(frame)

        bgr_color = (255, 242, 0) if mode == "Moving" else (0, 140, 255)
        
        cv2.rectangle(frame, (0, 0), (w, h), bgr_color, 4)
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), (0,0,0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        cv2.putText(frame, mode.upper(), (20, 35), cv2.FONT_HERSHEY_DUPLEX, 0.7, bgr_color, 1)
        
        if pinching:
            self.increment_apm()
            # Feature 45: High-Contrast Cursor Halos
            if config and config.get('accessibility', {}).get('high_contrast_halos', False):
                cv2.circle(frame, (w//2, h//2), int(50 + math.sin(time.time()*10)*10), (0, 255, 255), 3)

            cv2.circle(frame, (w-30, 25), 8, (50, 255, 50), -1)
            cv2.putText(frame, "HOLD", (w-90, 32), cv2.FONT_HERSHEY_DUPLEX, 0.5, (50, 255, 50), 1)

        # Feature 91: APM Tracker UI
        elapsed = max(1, time.time() - self.apm_start_time)
        apm = int((self.action_count / elapsed) * 60)
        cv2.putText(frame, f"APM: {apm}", (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame, f"SENS: {self.sensitivity_var.get()}", (120, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        if hasattr(self, '_current_notification') and self._current_notification:
             cv2.putText(frame, self._current_notification, (w//2 - 120, h//2), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 255), 2)

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
        pass

    def update_setting(self):
        self.app_controller.update_config('mouse', 'pointer_sensitivity', round(self.sensitivity_var.get(), 2))
        self.app_controller.update_config('mouse', 'smoothening', round(self.smoothening_var.get(), 1))

    def set_initial_settings(self, config):
        self.sensitivity_var.set(config['mouse']['pointer_sensitivity'])
        self.smoothening_var.set(config['mouse']['smoothening'])

    def show_help(self):
        pass

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
