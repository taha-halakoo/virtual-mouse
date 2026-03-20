import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

class UIView(tk.Tk):
    """
    Standard Tkinter GUI with Mode Selection and Help Menu.
    """
    def __init__(self, app_controller):
        super().__init__()

        self.app_controller = app_controller

        self.title("Virtual Mouse v2.2")
        self.geometry("350x650")
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        
        self.hud_colors = {
            "Moving": (255, 100, 0),    # Blue
            "Scrolling": (0, 165, 255)  # Orange
        }

        # --- Webcam Feed ---
        self.video_label = ttk.Label(self, text="Waiting for Stream...")
        self.video_label.grid(row=0, column=0, padx=10, pady=10)

        # --- Control Frame ---
        self.control_frame = ttk.Frame(self, padding="10")
        self.control_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.control_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_stop_button = ttk.Button(self.control_frame, text="Start Tracking", command=self.toggle_tracking)
        self.start_stop_button.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.status_label = ttk.Label(self.control_frame, text="Status: Ready", font=("Arial", 10, "bold"))
        self.status_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.mode_label = ttk.Label(self.control_frame, text="Mode: N/A")
        self.mode_label.grid(row=1, column=1, padx=5, pady=5, sticky="e")

        # --- Mode Selection ---
        self.mode_frame = ttk.LabelFrame(self, text="Control Mode", padding="10")
        self.mode_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.control_mode_var = tk.StringVar()
        ttk.Radiobutton(self.mode_frame, text="One-Handed", variable=self.control_mode_var, 
                        value="one_handed", command=self.update_control_mode).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(self.mode_frame, text="Two-Handed", variable=self.control_mode_var, 
                        value="two_handed", command=self.update_control_mode).grid(row=0, column=1, padx=10)
        
        # --- Settings Frame ---
        self.settings_frame = ttk.LabelFrame(self, text="Precision Controls", padding="10")
        self.settings_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.settings_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(self.settings_frame, text="Sensitivity:").grid(row=0, column=0, sticky="w")
        self.sensitivity_var = tk.DoubleVar()
        self.sensitivity_slider = ttk.Scale(self.settings_frame, from_=0.5, to=3.0, orient="horizontal", 
                                            variable=self.sensitivity_var, command=lambda v: self.update_setting())
        self.sensitivity_slider.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(self.settings_frame, text="Smoothing:").grid(row=1, column=0, sticky="w")
        self.smoothening_var = tk.DoubleVar()
        self.smoothening_slider = ttk.Scale(self.settings_frame, from_=1, to=20, orient="horizontal", 
                                            variable=self.smoothening_var, command=lambda v: self.update_setting())
        self.smoothening_slider.grid(row=1, column=1, sticky="ew", padx=5)

        # --- Help Button ---
        self.help_button = ttk.Button(self, text="Open Gesture Guide (HELP)", command=self.show_help)
        self.help_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

    def toggle_tracking(self):
        if self.app_controller.is_running():
            self.app_controller.stop()
            self.start_stop_button.configure(text="Start Tracking")
        else:
            self.app_controller.start()
            self.start_stop_button.configure(text="Stop Tracking")
            
    def update_video_feed(self, frame, mode="Moving", pinching=False):
        if frame is None: return
        h, w, _ = frame.shape
        color = self.hud_colors.get(mode, (255, 255, 255))
        cv2.rectangle(frame, (0, 0), (w, h), color, 10)
        cv2.putText(frame, f"MODE: {mode.upper()}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        if pinching:
            cv2.circle(frame, (w - 40, 40), 15, (0, 255, 0), -1)
            cv2.putText(frame, "HOLD", (w - 120, 45), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        frame_resized = cv2.resize(frame, (320, 240))
        cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.configure(image=imgtk)
        self.video_label.image = imgtk

    def update_status(self, status_text):
        self.status_label.configure(text=f"Status: {status_text}")
        
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
        self.control_mode_var.set(config['general'].get('control_mode', 'two_handed'))

    def show_help(self):
        mode = self.control_mode_var.get()
        if mode == "one_handed":
            guide = (
                "--- ONE-HANDED GESTURES (RIGHT HAND) ---\n\n"
                "1. MOVE CURSOR: Point with INDEX finger only.\n"
                "2. LEFT CLICK: Pinch THUMB and INDEX tips.\n"
                "3. RIGHT CLICK: Pinch THUMB and MIDDLE tips.\n"
                "4. DRAG & DROP: Pinch and HOLD THUMB+INDEX.\n"
                "5. SCROLL TOGGLE: Show 'V' SIGN (Index + Middle up).\n"
                "   -> When Orange border is active, move hand up/down to scroll."
            )
        else:
            guide = (
                "--- TWO-HANDED GESTURES ---\n\n"
                "RIGHT HAND (The Mouse):\n"
                " - Point INDEX to move cursor.\n"
                " - Move UP/DOWN to scroll (if in Scroll Mode).\n\n"
                "LEFT HAND (The Controller):\n"
                " - LEFT CLICK: Pinch THUMB + INDEX.\n"
                " - RIGHT CLICK: Pinch THUMB + MIDDLE.\n"
                " - DRAG: Pinch and HOLD THUMB + INDEX.\n"
                " - SCROLL TOGGLE: Show 'V' SIGN (Index + Middle up).\n"
                "   -> Hudson border turns Orange."
            )
        messagebox.showinfo("Gesture Guide", guide)
        
    def mainloop(self):
        self.app_controller.run()
        super().mainloop()
