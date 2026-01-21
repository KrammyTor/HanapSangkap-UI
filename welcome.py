import tkinter as tk
from scan import ScanScreen
from PIL import Image, ImageTk

ACCENT_COLOR = "#011118"
BAR_COLOR = "#0D6791"
BUTTON_COLOR = "#1680e4"

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

class WelcomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # Top Bar
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=120)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        # Bottom Bar
        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=120)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        # Center Frame
        center_frame = tk.Frame(self, bg="white")
        center_frame.pack(expand=True)

        # -------------------- HANAPSANGKAP IMAGE --------------------
        img = Image.open("hanapsangkap.png")

        # Scale proportionally to window
        max_width = int(WINDOW_WIDTH * 1)
        max_height = int(WINDOW_HEIGHT * 1)

        w, h = img.size
        ratio = min(max_width / w, max_height / h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        self.hanap_img = ImageTk.PhotoImage(img)
        img_label = tk.Label(center_frame, image=self.hanap_img, bg="white")
        img_label.pack(pady=20)

        # -------------------- TAP TO PROCEED BUTTON --------------------
        tap_card = tk.Frame(center_frame, width=500, height=60,
                            bg=BUTTON_COLOR, bd=0, highlightthickness=0)
        tap_card.pack(pady=20)
        tap_card.pack_propagate(False)

        tap_label = tk.Label(tap_card, text="TAP TO PROCEED!",
                             font=("Arial", 24, "bold"),
                             fg="white", bg=BUTTON_COLOR)
        tap_label.pack(expand=True)

        # Smooth transition to ScanScreen
        def proceed_to_scan(event=None):
            self.after(50, lambda: controller.show_frame(ScanScreen))

        tap_card.bind("<Button-1>", proceed_to_scan)
        tap_label.bind("<Button-1>", proceed_to_scan)
