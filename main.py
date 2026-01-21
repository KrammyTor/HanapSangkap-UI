import tkinter as tk
from welcome import WelcomeScreen
from scan import ScanScreen
from result import ResultScreen
from recipe import RecipeScreen
from dish import DishScreen
from PIL import ImageTk, Image

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

class HanapSangkapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HanapSangkap")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(bg="white")
        self.attributes("-fullscreen", True)
        img_icon = ImageTk.PhotoImage(file="hanapsangkap.png")
        self.iconphoto(True, img_icon)

        self.detected_item = None
        self.captured_frame = None

        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill="both", expand=True)

        # create and store frames
        self.frames = {}
        for F in (WelcomeScreen, ScanScreen, ResultScreen, RecipeScreen, DishScreen):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame(WelcomeScreen)

    def show_frame(self, screen_class):
        """Raise the frame of the given class"""
        self.frames[screen_class].tkraise()


if __name__ == "__main__":
    app = HanapSangkapApp()
    app.mainloop()
