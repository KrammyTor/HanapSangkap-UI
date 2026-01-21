import tkinter as tk
from PIL import Image, ImageTk
import os

ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
CARD_SHADOW = "#D0D5DA"
TEXT_COLOR = "#333"

IMAGE_WIDTH = 420
IMAGE_HEIGHT = 240

# -------------------- DISH DATA --------------------
DISH_DETAILS = {

    # ===================== LUZON =====================
    "Pinakbet Ilocano": {
        "region": "Luzon",
        "description": "Simmered vegetables cooked with bagoong, popular in Ilocos.",
        "steps": [
            "Boil water with bagoong.",
            "Add eggplant, ampalaya, sitaw, and pumpkin.",
            "Add onion, garlic, and tomato.",
            "Simmer for 10–15 minutes until tender."
        ],
        "image": "dishes_pics/pinakbet_ilocano.jpg"
    },

    "Pinakbet Tagalog": {
        "region": "Luzon",
        "description": "Tagalog-style pinakbet cooked by sautéing before stewing.",
        "steps": [
            "Sauté garlic, onion, and tomato.",
            "Add bagoong.",
            "Add pumpkin, eggplant, and sitaw.",
            "Cover and stew for 10 minutes."
        ],
        "image": "dishes_pics/pinakbet_tagalog.jpg"
    },

    "Ginisang Gulay": {
        "region": "Luzon",
        "description": "Mixed vegetables sautéed with garlic and onion.",
        "steps": [
            "Sauté garlic, onion, and tomato.",
            "Add pumpkin and eggplant.",
            "Add sitaw and ampalaya.",
            "Pour broth and simmer for 7 minutes."
        ],
        "image": "dishes_pics/ginisang_gulay.jpg"
    },

    "Ginisang Ampalaya": {
        "region": "Luzon",
        "description": "Sautéed bitter melon dish with tomatoes and onion.",
        "steps": [
            "Salt-soak sliced ampalaya for 5–10 minutes.",
            "Squeeze out water.",
            "Sauté garlic, onion, and tomato.",
            "Add ampalaya and cook for 5 minutes."
        ],
        "image": "dishes_pics/ginisang_ampalaya.jpg"
    },

    "Bulanglang Batangas": {
        "region": "Luzon",
        "description": "Clear vegetable soup from Batangas.",
        "steps": [
            "Boil rice wash with garlic and onion.",
            "Add tomato.",
            "Add pumpkin and sayote.",
            "Simmer until vegetables are tender."
        ],
        "image": "dishes_pics/bulanglang_batangas.jpg"
    },

    "Ginataang Gulay Bicol": {
        "region": "Luzon",
        "description": "Vegetables cooked in coconut milk, Bicol style.",
        "steps": [
            "Sauté onion and garlic.",
            "Add sitaw, eggplant, and pumpkin.",
            "Pour coconut milk.",
            "Simmer for 10 minutes."
        ],
        "image": "dishes_pics/ginataang_gulay_bicol.jpg"
    },

    "Ginisang Sayote": {
        "region": "Luzon",
        "description": "Stir-fried sayote with vegetables.",
        "steps": [
            "Sauté garlic and onion.",
            "Add sayote and carrot.",
            "Add cabbage.",
            "Stir-fry for 5–7 minutes."
        ],
        "image": "dishes_pics/ginisang_sayote.jpg"
    },

    # ===================== VISAYAS =====================
    "Utan Bisaya": {
        "region": "Visayas",
        "description": "Simple boiled vegetable soup from the Visayas.",
        "steps": [
            "Boil water with ginger and onion.",
            "Add pumpkin and eggplant.",
            "Add sitaw and tomato.",
            "Cook for 10 minutes."
        ],
        "image": "dishes_pics/utan_bisaya.jpg"
    },

    "Laswa Ilonggo": {
        "region": "Visayas",
        "description": "Mixed boiled vegetables with bagoong.",
        "steps": [
            "Boil onion and tomato.",
            "Add pumpkin and eggplant.",
            "Add sitaw and sayote.",
            "Simmer for 10 minutes."
        ],
        "image": "dishes_pics/laswa_ilonggo.jpg"
    },

    "Law-Uy": {
        "region": "Visayas",
        "description": "Light vegetable broth dish.",
        "steps": [
            "Boil water.",
            "Add onion and garlic.",
            "Add carrot, potato, and sayote.",
            "Cook until tender."
        ],
        "image": "dishes_pics/law_uy.jpg"
    },

    "Ginisang Gulay Visayas": {
        "region": "Visayas",
        "description": "Stir-fried vegetables with garlic and onion.",
        "steps": [
            "Sauté garlic and onion.",
            "Add cabbage and carrot.",
            "Add sitaw.",
            "Cook for 5 minutes."
        ],
        "image": "dishes_pics/ginisang_gulay_visayas.jpg"
    },

    "Ampalaya Soup": {
        "region": "Visayas",
        "description": "Clear soup made with bitter melon.",
        "steps": [
            "Boil tomato, onion, and garlic.",
            "Add ampalaya and eggplant.",
            "Simmer for 7 minutes."
        ],
        "image": "dishes_pics/ampalaya_soup.jpg"
    },

    "Sitaw at Kalabasa": {
        "region": "Visayas",
        "description": "Boiled sitaw and pumpkin dish.",
        "steps": [
            "Boil onion and tomato.",
            "Add pumpkin.",
            "Add sitaw.",
            "Cook for 10 minutes."
        ],
        "image": "dishes_pics/sitaw_kalabasa.jpg"
    },

    # ===================== MINDANAO =====================
    "Tinuto": {
        "region": "Mindanao",
        "description": "Vegetable stew cooked in coconut milk.",
        "steps": [
            "Sauté garlic and onion.",
            "Add eggplant, pumpkin, and sitaw.",
            "Pour coconut milk.",
            "Simmer for 15 minutes."
        ],
        "image": "dishes_pics/tinuto.jpg"
    },

    "Ginisang Gulay Mindanao": {
        "region": "Mindanao",
        "description": "Sautéed vegetables from Mindanao.",
        "steps": [
            "Sauté garlic and onion.",
            "Add cabbage, carrot, and potato.",
            "Add tomato.",
            "Cook for 7 minutes."
        ],
        "image": "dishes_pics/ginisang_gulay_mindanao.jpg"
    },

    "Ginataang Sitaw": {
        "region": "Mindanao",
        "description": "Sitaw cooked in coconut milk.",
        "steps": [
            "Sauté onion and garlic.",
            "Add sitaw, sayote, and eggplant.",
            "Pour coconut milk.",
            "Simmer until cooked."
        ],
        "image": "dishes_pics/ginataang_sitaw.jpg"
    },

    "Bulanglang Variant": {
        "region": "Mindanao",
        "description": "Adapted boiled vegetable dish.",
        "steps": [
            "Boil water.",
            "Add potato and carrot.",
            "Add pumpkin and tomato.",
            "Cook for 10 minutes."
        ],
        "image": "dishes_pics/bulanglang_variant.jpg"
    },

    "Ampalaya with Gulay": {
        "region": "Mindanao",
        "description": "Sautéed ampalaya with vegetables.",
        "steps": [
            "Sauté garlic and tomato.",
            "Add ampalaya.",
            "Add cabbage.",
            "Cook for 5 minutes."
        ],
        "image": "dishes_pics/ampalaya_with_gulay.jpg"
    },

    "Sayote Tomato Stew": {
        "region": "Mindanao",
        "description": "Stewed sayote with tomato.",
        "steps": [
            "Add sayote and tomato to pot.",
            "Add onion and garlic.",
            "Add carrot.",
            "Stew for 10 minutes."
        ],
        "image": "dishes_pics/sayote_tomato_stew.jpg"
    },

    "Mixed Utan": {
        "region": "Mindanao",
        "description": "Mixed boiled vegetable dish.",
        "steps": [
            "Boil water.",
            "Add eggplant and pumpkin.",
            "Add sitaw and ampalaya.",
            "Cook for 12 minutes."
        ],
        "image": "dishes_pics/mixed_utan.jpg"
    }
}

class DishScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # -------------------- TOP & BOTTOM BAR --------------------
        tk.Frame(self, bg=BAR_COLOR, height=120).pack(fill="x", side="top")
        tk.Frame(self, bg=BAR_COLOR, height=120).pack(fill="x", side="bottom")

        # -------------------- CENTER --------------------
        center = tk.Frame(self, bg="white")
        center.pack(expand=True, fill="both")

        shadow = tk.Frame(center, bg=CARD_SHADOW)
        shadow.pack(pady=20)

        card = tk.Frame(shadow, bg=CARD_BG, padx=30, pady=25)
        card.pack(padx=4, pady=4)

        # -------------------- IMAGE --------------------
        self.image_label = tk.Label(card, bg=CARD_BG)
        self.image_label.pack(pady=10)

        # -------------------- TITLE --------------------
        self.title_label = tk.Label(
            card,
            font=("Comic Sans MS", 26, "bold"),
            fg=ACCENT_COLOR,
            bg=CARD_BG
        )
        self.title_label.pack(pady=(10, 5))

        # -------------------- REGION --------------------
        self.region_label = tk.Label(
            card,
            font=("Helvetica", 16, "italic"),
            fg=TEXT_COLOR,
            bg=CARD_BG
        )
        self.region_label.pack(pady=(0, 10))

        # -------------------- DESCRIPTION --------------------
        self.desc_label = tk.Label(
            card,
            font=("Helvetica", 15),
            fg=TEXT_COLOR,
            bg=CARD_BG,
            wraplength=520,
            justify="center"
        )
        self.desc_label.pack(pady=10)

        # -------------------- STEPS --------------------
        steps_title = tk.Label(
            card,
            text="How to Cook",
            font=("Helvetica", 20, "bold"),
            fg=ACCENT_COLOR,
            bg=CARD_BG
        )
        steps_title.pack(pady=(20, 10))

        self.steps_frame = tk.Frame(card, bg=CARD_BG)
        self.steps_frame.pack()

        # -------------------- ACTION BUTTONS --------------------
        button_frame = tk.Frame(card, bg=CARD_BG)
        button_frame.pack(pady=20)

        # Back button
        back_btn = tk.Button(
            button_frame,
            text="Back",
            font=("Helvetica", 14, "bold"),
            bg=ACCENT_COLOR,
            fg="white",
            width=12,
            command=self.go_back
        )
        back_btn.pack(side="left", padx=10)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        dish = self.controller.selected_dish
        data = DISH_DETAILS.get(dish)

        if not data:
            return

        # ---- Title & Region ----
        self.title_label.config(text=dish)
        self.region_label.config(text=f"Origin: {data['region']}")
        self.desc_label.config(text=data["description"])

        # ---- Image ----
        img_path = data["image"]
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT))
            imgtk = ImageTk.PhotoImage(img)
            self.image_label.imgtk = imgtk
            self.image_label.config(image=imgtk)
        else:
            self.image_label.config(image="", text="Image not available")

        # ---- Steps ----
        for widget in self.steps_frame.winfo_children():
            widget.destroy()

        for i, step in enumerate(data["steps"], start=1):
            tk.Label(
                self.steps_frame,
                text=f"{i}. {step}",
                font=("Helvetica", 15),
                fg=TEXT_COLOR,
                bg=CARD_BG,
                wraplength=520,
                justify="left",
                anchor="w"
            ).pack(anchor="w", pady=4)

    # -------------------- BUTTON CALLBACKS WITH LATE IMPORT --------------------
    def go_back(self):
        from recipe import RecipeScreen   # late import avoids circular import
        self.controller.show_frame(RecipeScreen)

    def scan_again(self):
        from scan import ScanScreen       # late import avoids circular import
        self.controller.show_frame(ScanScreen)