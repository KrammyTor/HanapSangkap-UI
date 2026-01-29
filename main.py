import tkinter as tk
from welcome import WelcomeScreen
from scan import ScanScreen
from result import ResultScreen
from recipe import RecipeScreen
from dish import DishScreen
from PIL import ImageTk, Image

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480
# TEST TIMER: 10000ms (10 seconds). Change to 120000 for 2 minutes later.
IDLE_LIMIT = 120000 

class HanapSangkapApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # 🔑 Keybind: Ctrl + F to exit app
        self.bind("<Control-f>", self.exit_app)
        self.bind("<Control-F>", self.exit_app)

        self.title("HanapSangkap")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(bg="white")
        
        # Start in fullscreen
        self.attributes("-fullscreen", True)

        # tago mo cursor mo
        self.config(cursor="none")

        # App Icon
        try:
            img_icon = ImageTk.PhotoImage(file="hanapsangkap.png")
            self.iconphoto(True, img_icon)
        except:
            pass 

        # Shared Data
        self.detected_item = None
        self.captured_frame = None

        # --- IDLE LOGIC SETUP ---
        self.idle_after_id = None
        # Listen for any interaction anywhere in the app
        self.bind_all("<Any-KeyPress>", self.reset_idle_timer)
        self.bind_all("<Any-ButtonPress>", self.reset_idle_timer)
        self.bind_all("<Motion>", self.reset_idle_timer)

        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill="both", expand=True)

        # Create and store frames
        self.frames = {}
        for F in (WelcomeScreen, ScanScreen, ResultScreen, RecipeScreen, DishScreen):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)

        # Start on Welcome
        self.show_frame(WelcomeScreen)
        
        # Initialize the timer
        self.reset_idle_timer()

    # -------------------- IDLE MANAGEMENT --------------------
    def reset_idle_timer(self, event=None):
        """Cancels the existing timer and starts a new one."""
        if self.idle_after_id:
            self.after_cancel(self.idle_after_id)
        
        # Set the timer to trigger go_to_welcome
        self.idle_after_id = self.after(IDLE_LIMIT, self.go_to_welcome)

    def go_to_welcome(self):
        """Redirects the app to the Welcome Screen and cleans up hardware."""
        # 1. Don't reset if we are already on the Welcome Screen
        if self._active_frame_class == WelcomeScreen:
            self.reset_idle_timer() # Keep loop alive
            return

        # 2. Cleanup: Stop camera if it's running in ScanScreen
        scan_frame = self.frames.get(ScanScreen)
        if scan_frame and hasattr(scan_frame, 'reset_screen'):
            scan_frame.reset_screen()

        # 3. Cleanup: Reset shared data
        self.detected_item = None
        self.captured_frame = None

        # 4. Switch to Welcome
        print("Idle Timeout Reached: Returning to Home")
        self.show_frame(WelcomeScreen)
        
        # 5. Restart the timer loop
        self.reset_idle_timer()

    # -------------------- NAVIGATION --------------------
    def show_frame(self, screen_class):
        """Raise the frame of the given class"""
        self._active_frame_class = screen_class
        self.frames[screen_class].tkraise()
        # Reset timer on manual navigation too
        self.reset_idle_timer()

    def exit_app(self, event=None):
        self.destroy()


if __name__ == "__main__":
    app = HanapSangkapApp()
    app.mainloop()