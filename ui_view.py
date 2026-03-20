import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import cv2
import pystray
import threading
from tkinter import messagebox

class UIView(ttk.Window):
    """
    Premium ttkbootstrap GUI with System Tray support.
    """
    def __init__(self, app_controller):
        super().__init__(themename="cyborg") # Dark, modern theme

        self.app_controller = app_controller

        self.title("Virtual Mouse Pro")
        self.geometry("380x720")
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        
        self.hud_colors = {
            "Moving": (0, 191, 255),    # Deep Sky Blue
            "Scrolling": (255, 140, 0)  # Dark Orange
        }

        # --- System Tray Setup ---
        self.tray_icon = None
        self.protocol('WM_DELETE_WINDOW', self.hide_to_tray)

        # --- Main Layout ---
        main_frame = ttk.Frame(self, padding=20)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        # --- Webcam Feed ---
        self.video_card = ttk.Labelframe(main_frame, text=" Live Feed ", bootstyle="info")
        self.video_card.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        self.video_card.grid_columnconfigure(0, weight=1)
        
        self.video_label = ttk.Label(self.video_card, text="Camera Offline", anchor="center")
        self.video_label.grid(row=0, column=0, pady=10)

        # --- Status Panel ---
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, pady=(0, 15), sticky="ew")
        status_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.status_badge = ttk.Label(status_frame, text=" STOPPED ", bootstyle="danger-inverse", font="-size 12 -weight bold")
        self.status_badge.grid(row=0, column=0, sticky="w")
        
        self.mode_label = ttk.Label(status_frame, text="Mode: N/A", font="-size 11")
        self.mode_label.grid(row=0, column=1, sticky="e")

        # --- Main Controls ---
        self.start_stop_button = ttk.Button(main_frame, text="START TRACKING", bootstyle="success-outline", 
                                          command=self.toggle_tracking, padding=10)
        self.start_stop_button.grid(row=2, column=0, pady=(0, 15), sticky="ew")

        # --- Configuration Notebook (Tabs) ---
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=3, column=0, sticky="nsew")

        # Tab 1: Mode Selection
        tab_mode = ttk.Frame(notebook, padding=15)
        notebook.add(tab_mode, text="Control Scheme")
        
        self.control_mode_var = tk.StringVar()
        ttk.Radiobutton(tab_mode, text=" Face & Eyes (Omni-Sense)", variable=self.control_mode_var, 
                        value="face_and_eyes", bootstyle="info", command=self.update_control_mode).pack(anchor="w", pady=5)
        ttk.Radiobutton(tab_mode, text=" One-Handed (Right Hand)", variable=self.control_mode_var, 
                        value="one_handed", bootstyle="info", command=self.update_control_mode).pack(anchor="w", pady=5)
        ttk.Radiobutton(tab_mode, text=" Two-Handed (Pro Split)", variable=self.control_mode_var, 
                        value="two_handed", bootstyle="info", command=self.update_control_mode).pack(anchor="w", pady=5)

        # Tab 2: Precision Tuning
        tab_tune = ttk.Frame(notebook, padding=15)
        notebook.add(tab_tune, text="Precision")
        
        ttk.Label(tab_tune, text="Cursor Sensitivity").pack(anchor="w")
        self.sensitivity_var = tk.DoubleVar()
        ttk.Scale(tab_tune, from_=0.5, to=3.0, variable=self.sensitivity_var, bootstyle="primary", 
                  command=lambda v: self.update_setting()).pack(fill="x", pady=(0, 15))

        ttk.Label(tab_tune, text="One-Euro Smoothing (Higher = Less Jitter)").pack(anchor="w")
        self.smoothening_var = tk.DoubleVar()
        ttk.Scale(tab_tune, from_=1, to=20, variable=self.smoothening_var, bootstyle="primary", 
                  command=lambda v: self.update_setting()).pack(fill="x")

        # --- Help Button ---
        ttk.Button(main_frame, text="View Gesture Manual", bootstyle="link-info", 
                   command=self.show_help).grid(row=4, column=0, pady=10)
                   
        ttk.Label(main_frame, text="Hotkey: Ctrl+Shift+M to toggle", font="-size 8", foreground="gray").grid(row=5, column=0)

    def hide_to_tray(self):
        """Hides the window and shows a system tray icon."""
        self.withdraw()
        image = Image.new('RGB', (64, 64), color = (0, 191, 255)) # Simple blue icon for now
        menu = pystray.Menu(
            pystray.MenuItem('Show App', self.show_from_tray),
            pystray.MenuItem('Toggle Tracking', self.toggle_tracking_from_tray),
            pystray.MenuItem('Quit', self.quit_app)
        )
        self.tray_icon = pystray.Icon("VirtualMouse", image, "Virtual Mouse Pro", menu)
        # Run tray icon in a separate thread so it doesn't block the main Tkinter loop
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_from_tray(self, icon, item):
        icon.stop()
        self.after(0, self.deiconify)

    def toggle_tracking_from_tray(self, icon, item):
        self.after(0, self.toggle_tracking)

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        if self.app_controller.is_running():
            self.app_controller.stop()
        self.quit()

    def toggle_tracking(self):
        if self.app_controller.is_running():
            self.app_controller.stop()
            self.start_stop_button.configure(text="START TRACKING", bootstyle="success-outline")
            self.status_badge.configure(text=" STOPPED ", bootstyle="danger-inverse")
            self.video_label.configure(image='', text="Camera Offline")
        else:
            self.app_controller.start()
            self.start_stop_button.configure(text="STOP TRACKING", bootstyle="danger-outline")
            self.status_badge.configure(text=" RUNNING ", bootstyle="success-inverse")
            
    def update_video_feed(self, frame, mode="Moving", pinching=False):
        if frame is None: return
        h, w, _ = frame.shape
        color = self.hud_colors.get(mode, (255, 255, 255))
        
        # Pro HUD Overlay
        cv2.rectangle(frame, (0, 0), (w, h), color, 8)
        
        # Overlay Background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 60), (0,0,0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        cv2.putText(frame, f"MODE: {mode.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        if pinching:
            cv2.circle(frame, (w - 40, 30), 12, (0, 255, 0), -1)
            cv2.putText(frame, "HOLD", (w - 110, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        frame_resized = cv2.resize(frame, (320, 240))
        cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.configure(image=imgtk, text="")
        self.video_label.image = imgtk
        
    def update_status(self, status_text):
        pass # Managed by toggle_tracking now for cleaner state
        
    def update_mode(self, mode_text):
        self.mode_label.configure(text=f"Mode: {mode_text}")
        
    def update_setting(self):
        self.app_controller.update_config('mouse', 'pointer_sensitivity', round(self.sensitivity_var.get(), 2))
        self.app_controller.update_config('mouse', 'smoothening', round(self.smoothening_var.get(), 1))

    def update_control_mode(self):
        self.app_controller.update_config('general', 'control_mode', self.control_mode_var.get())

    def set_initial_settings(self, config):
        self.sensitivity_var.set(config['mouse']['pointer_sensitivity'])
        self.smoothening_var.set(config['mouse']['smoothening'])
        self.control_mode_var.set(config['general'].get('control_mode', 'face_and_eyes'))

    def show_help(self):
        mode = self.control_mode_var.get()
        if mode == "face_and_eyes":
            guide = (
                "=== OMNI-SENSE GESTURES (FACE & EYES) ===\n\n"
                "• Pointer: Move your NOSE to aim.\n"
                "• L-Click: Wink LEFT eye.\n"
                "• R-Click: Wink RIGHT eye.\n"
                "• Drag & Drop: Open MOUTH (bite to hold, close to release).\n"
            )
        elif mode == "one_handed":
            guide = (
                "=== ONE-HANDED PRO GESTURES ===\n\n"
                "Right Hand Only:\n"
                "• Move: Point INDEX finger.\n"
                "• L-Click: Pinch THUMB & INDEX.\n"
                "• R-Click: Pinch THUMB & MIDDLE.\n"
                "• Drag: Hold THUMB & INDEX pinch.\n"
                "• Mode Swap: Show 'V' Sign (Index+Middle up).\n"
                "• Scroll: (In Scroll Mode) Move hand Up/Down.\n\n"
                "• Volume: (In Scroll Mode) Pinch Thumb & Pinky and move Up/Down.\n"
                "• Desktop Switch: Swipe Right Hand quickly Left/Right."
            )
        else:
            guide = (
                "=== TWO-HANDED PRO GESTURES ===\n\n"
                "RIGHT HAND (Pointer):\n"
                "• Point INDEX to move or scroll.\n"
                "• Desktop Switch: Swipe Left/Right quickly.\n\n"
                "LEFT HAND (Commander):\n"
                "• L-Click: Pinch THUMB & INDEX.\n"
                "• R-Click: Pinch THUMB & MIDDLE.\n"
                "• Drag: Hold THUMB & INDEX pinch.\n"
                "• Mode Swap: Show 'V' Sign (Index+Middle up).\n"
                "• Volume Control: Pinch Thumb & Pinky and move hand Up/Down."
            )
        messagebox.showinfo("Virtual Mouse Pro Manual", guide)
        
    def mainloop(self):
        self.app_controller.run()
        super().mainloop()
