# result.py
import tkinter as tk
import cv2
from PIL import Image, ImageTk, ImageDraw
from recipe import RecipeScreen

ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
CARD_SHADOW = "#D0D5DA"
BAR_HEIGHT = 70

class ResultScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # 1. Top Bar
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=BAR_HEIGHT)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)
        tk.Label(top_bar, text="Scan Result", font=("Arial", 22, "bold"),
                 fg="white", bg=BAR_COLOR).pack(expand=True)

        # 2. Bottom Bar
        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=BAR_HEIGHT)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        # 3. Main Content
        center_frame = tk.Frame(self, bg="white")
        center_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # Right Sidebar
        right_frame = tk.Frame(center_frame, bg="white", width=260)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False) 

        right_shadow = tk.Frame(right_frame, bg=CARD_SHADOW)
        right_shadow.pack(fill="both", expand=True)
        self.right_card = tk.Frame(right_shadow, bg=CARD_BG, padx=15, pady=20)
        self.right_card.pack(padx=3, pady=3, fill="both", expand=True)

        # Status Label
        tk.Label(self.right_card, text="STATUS:", font=("Arial", 10, "bold"),
                 fg="#7f8c8d", bg=CARD_BG).pack(anchor="w")
        
        self.status_lbl = tk.Label(self.right_card, text="✅ SUCCESS", 
                                   font=("Arial", 14, "bold"), fg="#27ae60", bg=CARD_BG)
        self.status_lbl.pack(pady=(0, 20), anchor="w")

        # Detected Item Label
        tk.Label(self.right_card, text="INGREDIENT DETECTED:", font=("Arial", 10, "bold"),
                 fg="#7f8c8d", bg=CARD_BG).pack(anchor="w")
        
        self.result_lbl = tk.Label(self.right_card, text="", font=("Arial", 18, "bold"),
                                   fg=BAR_COLOR, bg=CARD_BG, wraplength=200, justify="left")
        self.result_lbl.pack(pady=10, anchor="w")

        # Notice text
        tk.Label(self.right_card, text="Redirecting to recipes...", 
                 font=("Arial", 10, "italic"), fg="#95a5a6", bg=CARD_BG).pack(side="bottom", pady=10)

        # Left: Static Image Feed
        left_frame = tk.Frame(center_frame, bg="white")
        left_frame.pack(side="left", fill="both", expand=True)

        card_shadow = tk.Frame(left_frame, bg=CARD_SHADOW)
        card_shadow.pack(fill="both", expand=True)
        self.img_container = tk.Frame(card_shadow, bg=CARD_BG)
        self.img_container.pack(padx=3, pady=3, fill="both", expand=True)

        self.img_label = tk.Label(self.img_container, bg=CARD_BG)
        self.img_label.pack(expand=True)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.update_idletasks()

        # Get captured frame and item safely
        frame = getattr(self.controller, "captured_frame", None)
        item = getattr(self.controller, "detected_item", "Unknown") or "Unknown"

        # Update label safely
        self.result_lbl.config(text=item.upper())

        # Display captured image
        if frame is not None:
            c_w = self.img_container.winfo_width()
            c_h = self.img_container.winfo_height()
            if c_w < 50: c_w, c_h = 640, 360

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)
            img_pil = img_pil.resize((c_w, c_h), Image.LANCZOS)

            mask = Image.new('L', (c_w, c_h), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, c_w, c_h), radius=20, fill=255)

            rounded_img = Image.new('RGBA', (c_w, c_h), (0, 0, 0, 0))
            rounded_img.paste(img_pil, (0, 0), mask=mask)

            imgtk = ImageTk.PhotoImage(rounded_img)
            self.img_label.configure(image=imgtk)
            self.img_label.image = imgtk
        else:
            self.img_label.config(text="No image captured", image='', font=("Arial", 16), fg="#95a5a6")

        # Wait 2 seconds then go to recipes safely
        self.after(2000, self.go_to_recipe)

    def go_to_recipe(self):
        recipe_frame = self.controller.frames.get(RecipeScreen)
        if recipe_frame:
            self.controller.show_frame(RecipeScreen)
