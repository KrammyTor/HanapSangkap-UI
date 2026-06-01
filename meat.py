import math
import tkinter as tk


# ==========================================================
# HANAPSANGKAP THEME COLORS
# ==========================================================
ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_SHADOW = "#D0D5DA"
TEXT_COLOR = "#333333"

PAGE_BG = "#FFFFFF"
PANEL_BG = "#F7FBFD"
PANEL_BORDER = "#DCEAF0"
MUTED_TEXT = "#6B7280"

WEIGHT_PANEL_BG = "#FFF7F2"
WEIGHT_PANEL_BORDER = "#FFD6BA"
WEIGHT_DISPLAY_BG = "#FFFFFF"
WEIGHT_DISPLAY_BORDER = "#FFD0A5"
WEIGHT_PRIMARY = "#FF8A3D"
WEIGHT_PRIMARY_DARK = "#D7641E"
WEIGHT_SOFT = "#FFF0E6"

DANGER = "#E35D5B"
DANGER_HOVER = "#CF4D4B"

# Temporary serving rule.
# Change this later depending on your final serving computation.
GRAMS_PER_SERVING = 100


class MeatScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=PAGE_BG)

        self.controller = controller

        self.selected_meat_type = "Pork"
        self.demo_weight_grams = 0
        self.grams_per_serving = GRAMS_PER_SERVING
        self.meat_type_buttons = {}

        screen_w = max(640, self.winfo_screenwidth())
        screen_h = max(480, self.winfo_screenheight())

        self.compact = screen_h <= 900 or screen_w <= 1100

        self.top_bar_height = 48 if self.compact else 64
        self.bottom_bar_height = 14 if self.compact else 24

        self.outer_pad_x = 16 if self.compact else 36
        self.outer_pad_y = 8 if self.compact else 18

        self.panel_pad_x = 16 if self.compact else 36
        self.panel_pad_y = 10 if self.compact else 28

        self.title_size = 18 if self.compact else 22
        self.main_title_size = 19 if self.compact else 26
        self.sub_size = 9 if self.compact else 12

        # -------------------- TOP BAR --------------------
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=self.top_bar_height)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        title_wrap = tk.Frame(top_bar, bg=BAR_COLOR)
        title_wrap.pack(expand=True)

        tk.Label(
            title_wrap,
            text="Meat Weight",
            font=("Arial", self.title_size, "bold"),
            fg="white",
            bg=BAR_COLOR,
        ).pack()

        # -------------------- BOTTOM BAR --------------------
        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=self.bottom_bar_height)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        # -------------------- CENTER CONTENT --------------------
        center_frame = tk.Frame(self, bg=PAGE_BG)
        center_frame.pack(
            expand=True,
            fill="both",
            padx=self.outer_pad_x,
            pady=self.outer_pad_y,
        )

        panel_shadow = tk.Frame(center_frame, bg=CARD_SHADOW)
        panel_shadow.pack(expand=True, fill="both")

        self.panel = tk.Frame(
            panel_shadow,
            bg=PANEL_BG,
            padx=self.panel_pad_x,
            pady=self.panel_pad_y,
            highlightthickness=1,
            highlightbackground=PANEL_BORDER,
        )
        self.panel.pack(expand=True, fill="both", padx=3, pady=3)

        self.build_ui()

    # ==========================================================
    # UI
    # ==========================================================
    def build_ui(self):
        wrapper = tk.Frame(self.panel, bg=PANEL_BG)
        wrapper.pack(anchor="center", expand=True)

        weight_panel = tk.Frame(
            wrapper,
            bg=WEIGHT_PANEL_BG,
            highlightthickness=2,
            highlightbackground=WEIGHT_PANEL_BORDER,
            padx=18 if self.compact else 30,
            pady=12 if self.compact else 24,
        )
        weight_panel.pack()

        tk.Label(
            weight_panel,
            text="Weigh the Meat",
            font=("Arial", self.main_title_size, "bold"),
            fg=WEIGHT_PRIMARY_DARK,
            bg=WEIGHT_PANEL_BG,
        ).pack(pady=(0, 4))

        tk.Label(
            weight_panel,
            text=(
                "Temporary mode: use the buttons below to simulate the loadcell.\n"
                "Later, this page can read the value directly from the Raspberry Pi loadcell."
            ),
            font=("Arial", self.sub_size),
            fg=MUTED_TEXT,
            bg=WEIGHT_PANEL_BG,
            justify="center",
            wraplength=540 if self.compact else 680,
        ).pack(pady=(0, 10 if self.compact else 18))

        # -------------------- MEAT TYPE --------------------
        tk.Label(
            weight_panel,
            text="Select meat type",
            font=("Arial", 11 if self.compact else 13, "bold"),
            fg=TEXT_COLOR,
            bg=WEIGHT_PANEL_BG,
        ).pack(pady=(0, 6))

        type_row = tk.Frame(weight_panel, bg=WEIGHT_PANEL_BG)
        type_row.pack(pady=(0, 10))

        for meat_type in ["Pork", "Chicken", "Beef", "Meat"]:
            btn = tk.Canvas(
                type_row,
                width=105 if self.compact else 120,
                height=38 if self.compact else 42,
                bg=WEIGHT_PANEL_BG,
                highlightthickness=0,
                cursor="hand2",
            )
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>", lambda e, m=meat_type: self.set_meat_type(m))
            self.meat_type_buttons[meat_type] = btn

        # -------------------- WEIGHT DISPLAY --------------------
        display_outer = tk.Frame(
            weight_panel,
            bg=WEIGHT_DISPLAY_BORDER,
            padx=2,
            pady=2,
        )
        display_outer.pack(pady=(0, 10), fill="x")

        display_inner = tk.Frame(
            display_outer,
            bg=WEIGHT_DISPLAY_BG,
            height=72 if self.compact else 92,
        )
        display_inner.pack(fill="x")
        display_inner.pack_propagate(False)

        self.weight_value_label = tk.Label(
            display_inner,
            text="0 g",
            font=("Arial", 30 if self.compact else 38, "bold"),
            fg=WEIGHT_PRIMARY_DARK,
            bg=WEIGHT_DISPLAY_BG,
        )
        self.weight_value_label.pack(expand=True)

        self.serving_label = tk.Label(
            weight_panel,
            text="Estimated serving: 0 servings",
            font=("Arial", 12 if self.compact else 15, "bold"),
            fg=BAR_COLOR,
            bg=WEIGHT_PANEL_BG,
        )
        self.serving_label.pack(pady=(0, 10))

        # -------------------- SIMULATION CONTROLS ONLY --------------------
        step_row = tk.Frame(weight_panel, bg=WEIGHT_PANEL_BG)
        step_row.pack(pady=(0, 10))

        self.create_small_weight_button(step_row, "-50g", lambda: self.adjust_demo_weight(-50))
        self.create_small_weight_button(step_row, "-10g", lambda: self.adjust_demo_weight(-10))
        self.create_small_weight_button(step_row, "TARE", self.tare_demo_weight)
        self.create_small_weight_button(step_row, "+10g", lambda: self.adjust_demo_weight(10))
        self.create_small_weight_button(step_row, "+50g", lambda: self.adjust_demo_weight(50))

        self.status_label = tk.Label(
            weight_panel,
            text="Use the buttons to set the meat weight, then press ENTER.",
            font=("Arial", 9 if self.compact else 11),
            fg=MUTED_TEXT,
            bg=WEIGHT_PANEL_BG,
            wraplength=540 if self.compact else 680,
            justify="center",
        )
        self.status_label.pack(pady=(0, 10))

        # -------------------- ACTION BUTTONS --------------------
        action_row = tk.Frame(weight_panel, bg=WEIGHT_PANEL_BG)
        action_row.pack()

        self.create_large_button(
            action_row,
            text="BACK",
            command=self.go_back_to_choice,
            bg_color="#E9EEF2",
            fg_color=BAR_COLOR,
            width=150 if self.compact else 175,
        )

        self.create_large_button(
            action_row,
            text="ENTER",
            command=self.add_weighted_meat,
            bg_color=WEIGHT_PRIMARY,
            fg_color="white",
            width=180 if self.compact else 220,
        )

        self.update_meat_type_buttons()
        self.update_weight_display()

    # ==========================================================
    # BUTTON HELPERS
    # ==========================================================
    def create_small_weight_button(self, parent, text, command):
        btn = tk.Frame(
            parent,
            bg="#FFFFFF",
            width=70 if self.compact else 82,
            height=35 if self.compact else 40,
            highlightthickness=1,
            highlightbackground=WEIGHT_DISPLAY_BORDER,
            cursor="hand2",
        )
        btn.pack(side="left", padx=3)
        btn.pack_propagate(False)

        label = tk.Label(
            btn,
            text=text,
            font=("Arial", 9 if self.compact else 10, "bold"),
            fg=BAR_COLOR,
            bg="#FFFFFF",
            cursor="hand2",
        )
        label.pack(expand=True)

        def on_enter(event=None):
            btn.config(bg=WEIGHT_SOFT)
            label.config(bg=WEIGHT_SOFT)

        def on_leave(event=None):
            btn.config(bg="#FFFFFF")
            label.config(bg="#FFFFFF")

        for widget in (btn, label):
            widget.bind("<Button-1>", lambda e: command())
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        return btn

    def create_large_button(self, parent, text, command, bg_color, fg_color, width=220):
        btn = tk.Frame(
            parent,
            bg=bg_color,
            width=width,
            height=44 if self.compact else 50,
            cursor="hand2",
            relief="raised",
            bd=2,
        )
        btn.pack(side="left", padx=6)
        btn.pack_propagate(False)

        label = tk.Label(
            btn,
            text=text,
            font=("Arial", 11 if self.compact else 13, "bold"),
            fg=fg_color,
            bg=bg_color,
            cursor="hand2",
        )
        label.pack(expand=True)

        for widget in (btn, label):
            widget.bind("<Button-1>", lambda e: command())

        return btn

    # ==========================================================
    # MEAT + WEIGHT LOGIC
    # ==========================================================
    def set_meat_type(self, meat_type):
        self.selected_meat_type = meat_type
        self.update_meat_type_buttons()
        self.status_label.config(text=f"Selected meat type: {meat_type}")

    def update_meat_type_buttons(self):
        for meat_type, canvas in self.meat_type_buttons.items():
            canvas.delete("all")

            active = meat_type == self.selected_meat_type
            fill = WEIGHT_PRIMARY if active else "#FFFFFF"
            outline = WEIGHT_PRIMARY if active else WEIGHT_DISPLAY_BORDER
            text_color = "#FFFFFF" if active else BAR_COLOR

            width = int(canvas["width"])
            height = int(canvas["height"])

            canvas.create_rectangle(
                2,
                2,
                width - 2,
                height - 2,
                fill=fill,
                outline=outline,
                width=2,
            )
            canvas.create_text(
                width // 2,
                height // 2,
                text=meat_type.upper(),
                fill=text_color,
                font=("Arial", 9 if self.compact else 10, "bold"),
            )

    def calculate_servings(self, grams):
        if grams <= 0:
            return 0

        return max(1, math.ceil(grams / self.grams_per_serving))

    def update_weight_display(self):
        servings = self.calculate_servings(self.demo_weight_grams)

        self.weight_value_label.config(text=f"{self.demo_weight_grams} g")

        serving_word = "serving" if servings == 1 else "servings"
        self.serving_label.config(text=f"Estimated serving: {servings} {serving_word}")

    def adjust_demo_weight(self, amount):
        self.demo_weight_grams = max(0, self.demo_weight_grams + amount)
        self.update_weight_display()
        self.status_label.config(text="Temporary weight adjusted manually.")

    def tare_demo_weight(self):
        self.demo_weight_grams = 0
        self.update_weight_display()
        self.status_label.config(text="Scale tared to 0 g.")

    def add_weighted_meat(self):
        weight = self.demo_weight_grams

        if weight <= 0:
            self.status_label.config(text="Please set a valid meat weight first.")
            return

        meat_type = self.selected_meat_type.strip()

        if not meat_type:
            self.status_label.config(text="Please select a meat type first.")
            return

        servings = self.calculate_servings(weight)

        items = getattr(self.controller, "detected_items", None)

        if not isinstance(items, list):
            items = []
            self.controller.detected_items = items

        existing_lower = [str(item).strip().lower() for item in items]

        if meat_type.lower() not in existing_lower:
            items.append(meat_type)

        ingredient_weights = getattr(self.controller, "ingredient_weights", None)

        if not isinstance(ingredient_weights, dict):
            ingredient_weights = {}
            self.controller.ingredient_weights = ingredient_weights

        ingredient_servings = getattr(self.controller, "ingredient_servings", None)

        if not isinstance(ingredient_servings, dict):
            ingredient_servings = {}
            self.controller.ingredient_servings = ingredient_servings

        key = meat_type.lower()

        ingredient_weights[key] = weight
        ingredient_servings[key] = {
            "grams": weight,
            "grams_per_serving": self.grams_per_serving,
            "estimated_servings": servings,
            "exact_servings": round(weight / self.grams_per_serving, 2),
        }

        self.controller.detected_item = meat_type
        self.controller.scan_more = True
        self.controller.after_result_target = "recipe"

        serving_word = "serving" if servings == 1 else "servings"
        self.status_label.config(
            text=f"Added: {meat_type} - {weight} g, about {servings} {serving_word}."
        )

        self.after(150, self.go_to_recipe_screen)

    # ==========================================================
    # NAVIGATION
    # ==========================================================
    def go_back_to_choice(self):
        frames = getattr(self.controller, "frames", {})

        for name, frame in frames.items():
            if "ScanChoiceScreen" in str(name):
                self.controller.show_frame(name)
                return

        self.status_label.config(text="ScanChoiceScreen was not found.")

    def go_to_recipe_screen(self):
        frames = getattr(self.controller, "frames", {})

        for name, frame in frames.items():
            if "RecipeScreen" in str(name):
                self.controller.show_frame(name)
                return

        self.status_label.config(text="Meat added, but RecipeScreen was not found.")

    def reset_screen(self):
        self.selected_meat_type = "Pork"
        self.demo_weight_grams = 0

        if hasattr(self, "status_label"):
            self.status_label.config(
                text="Use the buttons to set the meat weight, then press ENTER."
            )

        if hasattr(self, "weight_value_label"):
            self.update_weight_display()

        if hasattr(self, "meat_type_buttons"):
            self.update_meat_type_buttons()

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        self.focus_set()
        self.bind("<Return>", lambda event: self.add_weighted_meat())
        self.bind("<KP_Enter>", lambda event: self.add_weighted_meat())

        self.update_meat_type_buttons()
        self.update_weight_display()
        self.status_label.config(
            text="Use the buttons to set the meat weight, then press ENTER."
        )