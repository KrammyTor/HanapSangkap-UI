import tkinter as tk
from PIL import Image, ImageTk
from dish import DishScreen, DISH_DETAILS
import os

ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
CARD_SHADOW = "#D0D5DA"
BUTTON_ACTIVE = "#74B3CE"
BUTTON_IDLE = "#E6ECF2"
LINE_COLOR = "#D0D5DA"  # subtle line

IMAGE_WIDTH = 100
IMAGE_HEIGHT = 80

class RecipeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # -------------------- TOP & BOTTOM BAR --------------------
        tk.Frame(self, bg=BAR_COLOR, height=120).pack(fill="x", side="top")
        tk.Frame(self, bg=BAR_COLOR, height=120).pack(fill="x", side="bottom")

        center = tk.Frame(self, bg="white")
        center.pack(expand=True)

        self.title_label = tk.Label(
            center,
            font=("Comic Sans MS", 28, "bold"),
            fg=ACCENT_COLOR,
            bg="white"
        )
        self.title_label.pack(pady=20)

        # -------------------- REGION BUTTONS --------------------
        self.region_var = tk.StringVar(value="Luzon")
        region_frame = tk.Frame(center, bg="white")
        region_frame.pack(pady=(0, 10))

        self.region_buttons = {}
        for region in ["Luzon", "Visayas", "Mindanao"]:
            btn = tk.Label(
                region_frame,
                text=region,
                font=("Helvetica", 18, "bold"),
                bg=BUTTON_IDLE,
                fg="#333",
                width=10,
                height=2
            )
            btn.pack(side="left", padx=12)
            btn.bind("<Button-1>", lambda e, r=region: self.set_region(r))
            self.region_buttons[region] = btn

        # -------------------- SCROLLABLE LIST --------------------
        shadow = tk.Frame(center, bg=CARD_SHADOW)
        shadow.pack(pady=10)

        card = tk.Frame(shadow, bg=CARD_BG, padx=10, pady=10)
        card.pack(padx=20, pady=(20, 0), fill="both")

        self.canvas = tk.Canvas(card, bg=CARD_BG, highlightthickness=0, height=300)
        self.scrollbar = tk.Scrollbar(card, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=CARD_BG)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="n")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # -------------------- SCAN AGAIN BUTTON --------------------
        scan_btn = tk.Button(
            shadow,
            text="Scan Again",
            font=("Helvetica", 14, "bold"),
            bg="#FF6B6B",
            fg="white",
            width=20,
            command=self.scan_again
        )
        scan_btn.pack(pady=20, padx=20)

    # -------------------- RAISE --------------------
    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        ingredient = self.controller.detected_item
        self.title_label.config(text=f"Recipes with {ingredient}")
        self.update_region_buttons()
        self.show_dishes()

    # -------------------- REGION --------------------
    def set_region(self, region):
        self.region_var.set(region)
        self.update_region_buttons()
        self.show_dishes()

    def update_region_buttons(self):
        for r, btn in self.region_buttons.items():
            if r == self.region_var.get():
                btn.config(bg=BUTTON_ACTIVE, fg="white")
            else:
                btn.config(bg=BUTTON_IDLE, fg="#333")

    # -------------------- SHOW DISHES --------------------
    def show_dishes(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        region = self.region_var.get()
        dishes = [dish for dish, details in DISH_DETAILS.items() if details["region"] == region]

        for dish in dishes:
            details = DISH_DETAILS[dish]
            row_frame = tk.Frame(self.scrollable_frame, bg=CARD_BG, pady=5)
            row_frame.pack(fill="x", padx=20)

            # Dish image
            img_path = details["image"]
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT))
                imgtk = ImageTk.PhotoImage(img)
                lbl_img = tk.Label(row_frame, image=imgtk, bg=CARD_BG)
                lbl_img.image = imgtk
                lbl_img.pack(side="left", padx=10)
            else:
                lbl_img = tk.Label(row_frame, text="No Image", width=15, height=5, bg=CARD_BG)
                lbl_img.pack(side="left", padx=10)

            # Dish name
            lbl_name = tk.Label(row_frame, text=dish, font=("Helvetica", 14, "bold"), bg=CARD_BG)
            lbl_name.pack(side="left", padx=10, anchor="w")

            # Separator line
            sep = tk.Frame(self.scrollable_frame, height=1, bg=LINE_COLOR)
            sep.pack(fill="x", padx=20, pady=(2, 5))

            # Click event
            row_frame.bind("<Button-1>", lambda e, d=dish: self.open_dish(d))
            lbl_img.bind("<Button-1>", lambda e, d=dish: self.open_dish(d))
            lbl_name.bind("<Button-1>", lambda e, d=dish: self.open_dish(d))

    # -------------------- OPEN DISH --------------------
    def open_dish(self, dish):
        self.controller.selected_dish = dish
        self.controller.show_frame(DishScreen)

    # -------------------- SCAN AGAIN --------------------
    def scan_again(self):
        from scan import ScanScreen
        self.controller.show_frame(ScanScreen)
