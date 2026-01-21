import tkinter as tk
import cv2
from PIL import Image, ImageTk
from recipe import RecipeScreen

ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
CARD_SHADOW = "#D0D5DA"

class ResultScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        top_bar = tk.Frame(self, bg=BAR_COLOR, height=120)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=120)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        center_frame = tk.Frame(self, bg="white")
        center_frame.pack(expand=True)

        card_shadow = tk.Frame(center_frame, bg=CARD_SHADOW)
        card_shadow.pack(pady=10)

        card = tk.Frame(card_shadow, bg=CARD_BG, padx=25, pady=25)
        card.pack(padx=4, pady=4)

        self.img_label = tk.Label(card, bg=CARD_BG)
        self.img_label.pack(pady=10)

        self.text_label = tk.Label(card, font=("Helvetica", 24),
                                   fg=ACCENT_COLOR, bg=CARD_BG)
        self.text_label.pack(pady=10)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        frame = self.controller.captured_frame
        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (560, 315))
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.img_label.imgtk = imgtk
            self.img_label.configure(image=imgtk)

        self.text_label.config(text=f"Detected: {self.controller.detected_item}")

        # Go to RecipeScreen after 1.5s
        self.after(1500, lambda: self.controller.show_frame(RecipeScreen))
