import json
import os
import tkinter as tk

from welcome import WelcomeScreen
from scan import ScanScreen
from result import ResultScreen
from scan_choice import ScanChoiceScreen
from meat import MeatScreen
from recipe import RecipeScreen
from dish import DishScreen

from PIL import ImageTk, Image


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

# 10000ms (10 seconds). 120000 (2 minutes)
IDLE_LIMIT = 120000

FAVORITES_FILE = "favorites.json"


class HanapSangkapApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Ctrl + F to exit app
        self.bind("<Control-f>", self.exit_app)
        self.bind("<Control-F>", self.exit_app)

        self.title("HanapSangkap")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(bg="white")

        self.attributes("-fullscreen", True)
        self.config(cursor="none")

        try:
            img_icon = ImageTk.PhotoImage(file="hanapsangkap.png")
            self.iconphoto(True, img_icon)
        except:
            pass

        # -------------------- SHARED APP DATA --------------------
        self.detected_item = None
        self.detected_items = []
        self.captured_frame = None
        self.selected_dish = None

        self.scan_more = False
        self.scan_mode = "vegetable"
        self.after_result_target = "choice"

        # Meat/loadcell data
        # Used by meat.py and scan_choice.py
        self.ingredient_weights = {}
        self.ingredient_servings = {}

        self.recipe_mode = "region"

        self.favorites_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            FAVORITES_FILE
        )
        self.favorite_dishes = self.load_favorites()

        # Active frame tracker
        self._active_frame_class = None

        # -------------------- IDLE LOGIC SETUP --------------------
        self.idle_after_id = None
        self.bind_all("<Any-KeyPress>", self.reset_idle_timer)
        self.bind_all("<Any-ButtonPress>", self.reset_idle_timer)
        self.bind_all("<Motion>", self.reset_idle_timer)

        # -------------------- MAIN CONTAINER --------------------
        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill="both", expand=True)

        # -------------------- REGISTER SCREENS --------------------
        self.frames = {}

        for F in (
            WelcomeScreen,
            ScanScreen,
            ResultScreen,
            ScanChoiceScreen,
            MeatScreen,
            RecipeScreen,
            DishScreen,
        ):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame(WelcomeScreen)
        self.reset_idle_timer()

    # -------------------- IDLE MANAGEMENT --------------------
    def reset_idle_timer(self, event=None):
        """Cancels the existing timer and starts a new one."""
        if self.idle_after_id:
            self.after_cancel(self.idle_after_id)

        self.idle_after_id = self.after(IDLE_LIMIT, self.go_to_welcome)

    def go_to_welcome(self):
        """Redirects the app to the Welcome Screen and cleans up hardware."""

        # 1. Don't reset if we are already on the Welcome Screen
        if self._active_frame_class == WelcomeScreen:
            self.reset_idle_timer()
            return

        # 2. Cleanup: Stop camera if it's running in ScanScreen
        scan_frame = self.frames.get(ScanScreen)
        if scan_frame and hasattr(scan_frame, "reset_screen"):
            scan_frame.reset_screen()

        # 3. Cleanup: Reset shared data
        self.detected_item = None
        self.detected_items = []
        self.captured_frame = None
        self.selected_dish = None

        self.scan_more = False
        self.scan_mode = "vegetable"
        self.after_result_target = "choice"

        # Reset meat/loadcell data
        self.ingredient_weights = {}
        self.ingredient_servings = {}

        self.recipe_mode = "region"

        # 4. Switch to Welcome
        print("Idle Timeout Reached: Returning to Home")
        self.show_frame(WelcomeScreen)

        # 5. Restart the timer loop
        self.reset_idle_timer()

    # -------------------- NAVIGATION --------------------
    def show_frame(self, screen_class):
        """Raise the frame of the given class."""
        self._active_frame_class = screen_class

        frame = self.frames.get(screen_class)

        if frame is None:
            print(f"Frame not found: {screen_class}")
            return

        frame.tkraise()

        # Reset timer on manual navigation too
        self.reset_idle_timer()

    # -------------------- FAVORITES --------------------
    def is_favorite(self, dish_name):
        return dish_name in self.favorite_dishes

    def toggle_favorite(self, dish_name):
        if not dish_name:
            return False

        if dish_name in self.favorite_dishes:
            self.favorite_dishes.remove(dish_name)
            self.save_favorites()
            return False

        self.favorite_dishes.add(dish_name)
        self.save_favorites()
        return True

    def load_favorites(self):
        if not os.path.exists(self.favorites_path):
            return set()

        try:
            with open(self.favorites_path, "r", encoding="utf-8") as favorites_file:
                stored = json.load(favorites_file)

            if isinstance(stored, list):
                return {
                    dish
                    for dish in stored
                    if isinstance(dish, str) and dish.strip()
                }

        except (OSError, json.JSONDecodeError):
            pass

        return set()

    def save_favorites(self):
        try:
            with open(self.favorites_path, "w", encoding="utf-8") as favorites_file:
                json.dump(sorted(self.favorite_dishes), favorites_file, indent=2)
        except OSError:
            pass

    # -------------------- EXIT --------------------
    def exit_app(self, event=None):
        self.save_favorites()
        self.destroy()


if __name__ == "__main__":
    app = HanapSangkapApp()
    app.mainloop()