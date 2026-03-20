from app_controller import AppController

def main():
    """
    The main entry point for the Virtual Mouse application.
    
    This function initializes the AppController, which in turn sets up
    the GUI (UIView) and all other components. The application's main
    loop is then started via the view.
    """
    try:
        app = AppController()
        # The mainloop is now managed inside the AppController's run method,
        # which is called via the view's mainloop.
        app.view.mainloop()
    except Exception as e:
        # In a real production app, you'd want more robust logging here.
        print(f"An unexpected error occurred: {e}")
        # Optionally, show an error dialog to the user.
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw() # Hide the main window
        messagebox.showerror("Application Error", f"""An unexpected error occurred: {e}
Please check the console for details.""")
        root.destroy()


if __name__ == "__main__":
    main()
