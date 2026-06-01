import tkinter as tk
from PIL import Image, ImageOps, ImageTk
from dish import DishScreen, DISH_DETAILS
import os
import glob
import re

# ============================================================
# MODERNIZED RECIPE SCREEN UI
# ============================================================

ACCENT_COLOR = "#74B3CE"
PRIMARY = "#0D6791"
PRIMARY_DARK = "#09506F"
BG = "#F6F9FC"
SOFT_SURFACE = "#EEF5F8"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#DCE7EE"
TEXT_DARK = "#20323F"
TEXT_MUTED = "#637381"
TEXT_LIGHT = "#FFFFFF"
DANGER = "#FF6B6B"
DANGER_SOFT = "#FFE7E7"
BUTTON_IDLE = "#EAF1F5"
BUTTON_ACTIVE = ACCENT_COLOR
SHADOW = "#D6E0E7"
PLACEHOLDER = "#E8EEF2"

IMAGE_WIDTH = 180
IMAGE_HEIGHT = 95

DISH_CARD_WIDTH = 350
DISH_CARD_HEIGHT = 205

DISH_TITLE_AREA_HEIGHT = 28
DISH_INFO_AREA_HEIGHT = 34

FAV_IMAGE_WIDTH = 120
FAV_IMAGE_HEIGHT = 78
FAV_ROW_HEIGHT = 132
FAV_BUTTON_AREA_WIDTH = 150

NAV_BTN_SIZE = 60

SCREEN_PAD_X = 0
SCREEN_PAD_Y = 0

# This is only for displaying the estimated serving note in the recipe list screen.
# Based on the meat table reference:
# DOST-FNRI-based practical serving basis used by the system:
# 125g meat = 1 serving/person
# If measured meat is below 125g, keep the default minimum serving of 1.
BONELESS_GRAMS_PER_SERVING = 125
BONE_IN_GRAMS_PER_SERVING = 125

MEAT_GRAMS_PER_SERVING = {
    "pork": BONELESS_GRAMS_PER_SERVING,
    "baboy": BONELESS_GRAMS_PER_SERVING,
    "beef": BONELESS_GRAMS_PER_SERVING,
    "baka": BONELESS_GRAMS_PER_SERVING,
    "chicken": BONELESS_GRAMS_PER_SERVING,
    "manok": BONELESS_GRAMS_PER_SERVING,
}

BONE_IN_KEYWORDS = [
    "bone-in", "bone in", "with bone", "bones", "bone",
    "shank", "oxtail", "trotter", "trotters", "ribs", "short ribs",
    "pork leg", "hock", "pata", "panga", "jaw",
    "chicken leg", "leg quarter", "drumstick", "wing", "wings",
    "whole chicken", "native chicken", "free-range chicken"
]

# Only these system-recognized scanned ingredients are shown under "Missing".
# This avoids showing condiments/seasonings like salt, pepper, soy sauce, oil, water, cubes, etc.
# Include garlic, onion, and ginger because they are part of the vegetable detection model.
SYSTEM_MISSING_VEGETABLES = {
    "ampalaya": ["ampalaya", "bitter melon", "bitter gourd"],
    "cabbage": ["cabbage", "repolyo"],
    "carrot": ["carrot", "carrots"],
    "corn": ["corn", "mais"],
    "garlic": ["garlic", "bawang"],
    "ginger": ["ginger", "luya"],
    "okra": ["okra"],
    "onion": ["onion", "onions", "red onion", "white onion", "yellow onion", "sibuyas"],
    "potato": ["potato", "potatoes", "patatas"],
    "pumpkin": ["pumpkin", "squash", "kalabasa"],
    "sayote": ["sayote", "chayote"],
    "tomato": ["tomato", "tomatoes", "kamatis"],
}

MISSING_VEGETABLE_DISPLAY = {
    "ampalaya": "Ampalaya",
    "cabbage": "Cabbage",
    "carrot": "Carrot",
    "corn": "Corn",
    "garlic": "Garlic",
    "ginger": "Ginger",
    "okra": "Okra",
    "onion": "Onion",
    "potato": "Potato",
    "pumpkin": "Pumpkin",
    "sayote": "Sayote",
    "tomato": "Tomato",
}

MEAT_KEYWORDS = {
    "pork": [
        "lechon kawali", "inihaw na liempo", "pork belly", "pork shoulder",
        "pork leg", "pork hock", "pig face", "pig ears", "pig liver",
        "pig lung", "pig intestines", "pig", "pork", "baboy", "liempo",
        "maskara", "belly", "ham", "speck", "etag", "chicharon",
        "hotdog", "hotdogs", "pork cube", "pork cubes", "pork broth",
        "pork blood", "pork's blood", "pork's lung", "pork's small intestines"
    ],
    "beef": [
        "beef short ribs", "beef shank", "beef brisket", "stewing beef",
        "sirloin beef", "cow trotters", "bulls' testes", "bulls testes",
        "beef tendons", "beef liver", "beef stock", "beef broth",
        "beef cube", "beef", "baka", "oxtail", "brisket", "sirloin",
        "trotters", "tendon", "tendons", "short ribs", "ribs", "chuck"
    ],
    "chicken": [
        "chicken breast", "chicken thighs", "chicken leg", "chicken liver",
        "chicken stock", "chicken broth", "chicken cube", "chicken cubes",
        "leg quarter", "leg quarters", "chicken", "manok", "drumstick",
        "drumsticks", "thigh", "thighs", "wing", "wings", "breast", "breasts"
    ],
}


# ============================================================
# MEAT MEASUREMENT NORMALIZER
# ============================================================

MEAT_DEFAULT_GRAMS = {
    "pork": 500,
    "baboy": 500,
    "beef": 500,
    "baka": 500,
    "chicken": 500,
    "manok": 500,
}

MEAT_UNIT_TO_GRAMS = {
    "kg": 1000,
    "kgs": 1000,
    "kilogram": 1000,
    "kilograms": 1000,
    "kilo": 1000,
    "kilos": 1000,
    "lb": 454,
    "lbs": 454,
    "pound": 454,
    "pounds": 454,
}

MEAT_UNIT_PATTERN = r"(kg|kgs|kilogram|kilograms|kilo|kilos|lb|lbs|pound|pounds)"
MEAT_AMOUNT_PATTERN = r"(\d+\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+|\d+(?:\.\d+)?)"


def _normalize_spaces(value):
    return " ".join(str(value or "").strip().split())


def _parse_recipe_amount(value):
    text = str(value or "").strip()

    if not text:
        return None

    try:
        if " " in text and "/" in text:
            whole, fraction = text.split(None, 1)
            numerator, denominator = fraction.replace(" ", "").split("/", 1)
            return float(whole) + (float(numerator) / float(denominator))

        if "/" in text:
            numerator, denominator = text.replace(" ", "").split("/", 1)
            return float(numerator) / float(denominator)

        return float(text)
    except Exception:
        return None


def _detect_meat_word_in_ingredient(text):
    clean = _normalize_spaces(text).lower().replace("_", " ").replace("-", " ")

    for meat_type, keywords in MEAT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in clean:
                return meat_type

    return None


def _format_grams(value):
    grams = int(round(float(value)))
    return f"{grams} g"


def _convert_meat_units_to_grams(text):
    import re

    original = str(text or "")
    meat_type = _detect_meat_word_in_ingredient(original)

    if not meat_type:
        return original

    cleaned = original

    # Convert direct meat units like "1 kg pork", "0.5kg beef", "2 lb chicken".
    direct_pattern = re.compile(
        rf"(?P<amount>{MEAT_AMOUNT_PATTERN})\s*(?P<unit>{MEAT_UNIT_PATTERN})\b",
        re.IGNORECASE,
    )

    def direct_repl(match):
        amount = _parse_recipe_amount(match.group("amount"))
        unit = match.group("unit").lower()

        if amount is None:
            return match.group(0)

        grams = amount * MEAT_UNIT_TO_GRAMS.get(unit, 1)
        return _format_grams(grams)

    cleaned = direct_pattern.sub(direct_repl, cleaned)

    # Replace unknown meat quantity wording with a sensible gram value.
    unknown_patterns = [
        r"\bmeat\s+as\s+needed\b",
        r"\bpork\s+as\s+needed\b",
        r"\bbeef\s+as\s+needed\b",
        r"\bchicken\s+as\s+needed\b",
        r"\bbaboy\s+as\s+needed\b",
        r"\bbaka\s+as\s+needed\b",
        r"\bmanok\s+as\s+needed\b",
        r"\bunknown\s+(?:amount|measurement|qty|quantity)\b",
    ]

    default_g = MEAT_DEFAULT_GRAMS.get(meat_type, 500)

    for pattern in unknown_patterns:
        cleaned = re.sub(
            pattern,
            f"{default_g} g {meat_type}",
            cleaned,
            flags=re.IGNORECASE,
        )

    # Clean duplicated spaces and old shorthand like "gms".
    cleaned = re.sub(r"\bgrams\b", "g", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bgram\b", "g", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bgms\b", "g", cleaned, flags=re.IGNORECASE)

    # If it is a meat ingredient but still has no gram amount, give it a clear gram value.
    # Examples: "Lechon kawali" -> "500 g lechon kawali".
    # This also prevents meat ingredients from being missed by the serving system.
    has_gram_amount = re.search(r"\b\d+(?:\.\d+)?\s*g\b", cleaned, flags=re.IGNORECASE)
    if not has_gram_amount:
        lowered = cleaned.lower().strip()
        optional_prefix = ""

        if lowered.startswith("optional protein:"):
            cleaned = re.sub(r"^optional protein:\s*", "", cleaned, flags=re.IGNORECASE).strip()
            optional_prefix = "Optional protein: "

        cleaned = f"{optional_prefix}{default_g} g {cleaned}"

    # Remove accidental duplicated unit leftovers from older converted data.
    # Example: "567 g 1/4 lb lechon" becomes "567 g lechon".
    cleaned = re.sub(
        rf"(\d+(?:\.\d+)?\s*g)\s+{MEAT_AMOUNT_PATTERN}\s*{MEAT_UNIT_PATTERN}\b",
        r"\1",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def _normalize_dish_details_meat_measurements():
    if not isinstance(DISH_DETAILS, dict):
        return

    for dish_name, details in DISH_DETAILS.items():
        if not isinstance(details, dict):
            continue

        ingredients = details.get("ingredients", [])

        if isinstance(ingredients, list):
            details["ingredients"] = [
                _convert_meat_units_to_grams(item)
                for item in ingredients
            ]
        elif isinstance(ingredients, str):
            details["ingredients"] = _convert_meat_units_to_grams(ingredients)


_normalize_dish_details_meat_measurements()


class RecipeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)

        self.controller = controller
        self._scroll_job = None
        self.current_mode = "region"
        self._image_refs = []

        self.empty_state_frame = None

        self._latest_full_ingredients = "Ingredients"
        self._latest_short_ingredients = "Ingredients"

        self.show_all_recipes = getattr(self.controller, "recipe_show_all", False)

        self._build_header()
        self._build_bottom_bar()
        self._build_content()
        self._bind_shortcuts()

    # ============================================================
    # SHORTCUTS / FLOATING NAV SAFETY
    # ============================================================

    def _bind_shortcuts(self):
        self.bind_all("<Control-Shift-KeyPress-S>", self.toggle_show_all_recipes_shortcut)
        self.bind_all("<Control-Shift-KeyPress-s>", self.toggle_show_all_recipes_shortcut)

    def _raise_floating_nav(self):
        try:
            for widget_name in ("up_canvas", "down_canvas"):
                if hasattr(self, widget_name):
                    widget = getattr(self, widget_name)
                    if widget.winfo_exists():
                        widget.master.tk.call("raise", widget._w)
        except Exception:
            pass

    def toggle_show_all_recipes_shortcut(self, event=None):
        active_frame = getattr(self.controller, "_active_frame_class", None)

        if active_frame not in (RecipeScreen, self.__class__):
            return None

        self.show_all_recipes = not self.show_all_recipes
        self.controller.recipe_show_all = self.show_all_recipes

        self.current_mode = "region"
        self.controller.recipe_mode = self.current_mode

        self.canvas.yview_moveto(0)
        self._update_header_text()
        self.update_region_buttons()
        self.show_dishes()
        self._raise_floating_nav()

        return "break"

    # ============================================================
    # UI BUILDERS
    # ============================================================

    def _build_header(self):
        self.header = tk.Frame(self, bg=BG)
        self.header.pack(
            fill="x",
            side="top",
            padx=SCREEN_PAD_X,
            pady=(SCREEN_PAD_Y, 5)
        )

        self.header_card = tk.Frame(self.header, bg=PRIMARY)
        self.header_card.pack(fill="x")

        self.header_inner = tk.Frame(self.header_card, bg=PRIMARY)
        self.header_inner.pack(fill="x", padx=18, pady=10)
        self.header_inner.bind("<Configure>", self._update_header_wrap)

        left = tk.Frame(self.header_inner, bg=PRIMARY)
        left.pack(side="left", fill="both", expand=True)

        self.title_label = tk.Label(
            left,
            text="Recipes",
            font=("Helvetica", 20, "bold"),
            fg=TEXT_LIGHT,
            bg=PRIMARY,
            anchor="w",
            justify="left"
        )
        self.title_label.pack(fill="x")

        self.subtitle_label = tk.Label(
            left,
            text="Select a region, open a recipe, or save your favorite dishes for later.",
            font=("Helvetica", 10),
            fg="#DCEFF7",
            bg=PRIMARY,
            anchor="w",
            justify="left",
            wraplength=700
        )
        self.subtitle_label.pack(fill="x", pady=(3, 0))

        right = tk.Frame(self.header_inner, bg=PRIMARY)
        right.pack(side="right", padx=(14, 0))

        self.result_badge = tk.Canvas(
            right,
            width=140,
            height=38,
            bg=PRIMARY,
            highlightthickness=0
        )
        self.result_badge.pack()

        self._draw_pill(
            self.result_badge,
            color="#FFFFFF",
            text="0 RECIPES",
            text_color=PRIMARY,
            width=140,
            height=38
        )

    def _build_bottom_bar(self):
        self.bottom_bar = tk.Frame(self, bg=BG)
        self.bottom_bar.pack(
            fill="x",
            side="bottom",
            padx=SCREEN_PAD_X,
            pady=(4, SCREEN_PAD_Y)
        )

        self.bottom_card = tk.Frame(self.bottom_bar, bg=PRIMARY)
        self.bottom_card.pack(fill="x")

        button_group = tk.Frame(self.bottom_card, bg=PRIMARY)
        button_group.pack(expand=True, pady=8)

        self.restart_btn = tk.Canvas(
            button_group,
            width=215,
            height=44,
            bg=PRIMARY,
            highlightthickness=0,
            cursor="hand2"
        )
        self.restart_btn.pack(side="left", padx=8)

        self._draw_action_button(
            self.restart_btn,
            text="RESTART SCAN",
            fill=ACCENT_COLOR,
            outline=ACCENT_COLOR,
            text_color="#FFFFFF",
            width=215,
            height=44
        )
        self.restart_btn.bind("<Button-1>", lambda e: self.scan_again())

        self.add_ingredient_btn = tk.Canvas(
            button_group,
            width=225,
            height=44,
            bg=PRIMARY,
            highlightthickness=0,
            cursor="hand2"
        )
        self.add_ingredient_btn.pack(side="left", padx=8)

        self._draw_action_button(
            self.add_ingredient_btn,
            text="+ ADD INGREDIENT",
            fill="#FFFFFF",
            outline="#FFFFFF",
            text_color=PRIMARY,
            width=225,
            height=44
        )
        self.add_ingredient_btn.bind("<Button-1>", lambda e: self.scan_more_ingredients())

    def _build_content(self):
        self.center = tk.Frame(self, bg=BG)
        self.center.pack(
            expand=True,
            fill="both",
            side="top",
            padx=SCREEN_PAD_X,
            pady=(0, 0)
        )

        # ------------------------------------------------------------
        # FILTER PANEL
        # ------------------------------------------------------------
        self.filter_panel = tk.Frame(self.center, bg=BG)
        self.filter_panel.pack(fill="x", padx=8, pady=(3, 6))

        region_wrap = tk.Frame(self.filter_panel, bg=BG)
        region_wrap.pack(side="left", fill="x", expand=True)

        region_label = tk.Label(
            region_wrap,
            text="Choose Region",
            font=("Helvetica", 10, "bold"),
            fg=TEXT_MUTED,
            bg=BG
        )
        region_label.pack(side="left", padx=(2, 10))

        self.region_var = tk.StringVar(value="Luzon")
        self.region_buttons = {}

        for region in ["Luzon", "Visayas", "Mindanao"]:
            btn = tk.Canvas(
                region_wrap,
                width=112,
                height=38,
                bg=BG,
                highlightthickness=0,
                cursor="hand2"
            )
            btn.pack(side="left", padx=(0, 7))
            btn.bind("<Button-1>", lambda e, r=region: self.set_region(r))
            self.region_buttons[region] = btn

        favorite_wrap = tk.Frame(self.filter_panel, bg=BG)
        favorite_wrap.pack(side="right")

        self.favorite_filter_canvas = tk.Canvas(
            favorite_wrap,
            width=150,
            height=38,
            bg=BG,
            highlightthickness=0,
            cursor="hand2"
        )
        self.favorite_filter_canvas.pack()
        self.favorite_filter_canvas.bind("<Button-1>", lambda e: self.show_favorites())

        # ------------------------------------------------------------
        # MAIN LAYOUT
        # ------------------------------------------------------------
        self.main_layout = tk.Frame(self.center, bg=BG)
        self.main_layout.pack(expand=True, fill="both", padx=0, pady=0)

        self.list_area = tk.Frame(self.main_layout, bg=BG)
        self.list_area.pack(side="left", expand=True, fill="both", padx=0, pady=0)

        self.content_shell = tk.Frame(
            self.list_area,
            bg=SHADOW,
            padx=1,
            pady=1
        )
        self.content_shell.pack(expand=True, fill="both", padx=0, pady=0)

        self.content_card = tk.Frame(self.content_shell, bg=SOFT_SURFACE)
        self.content_card.pack(expand=True, fill="both")

        self.canvas = tk.Canvas(
            self.content_card,
            bg=SOFT_SURFACE,
            highlightthickness=0
        )
        self.canvas.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        self.scrollable_frame = tk.Frame(self.canvas, bg=SOFT_SURFACE)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._enable_mousewheel()

        # ------------------------------------------------------------
        # FLOATING RIGHT NAVIGATION BUTTONS ONLY
        # ------------------------------------------------------------
        self.up_canvas = tk.Canvas(
            self.main_layout,
            width=NAV_BTN_SIZE,
            height=NAV_BTN_SIZE,
            bg=BG,
            highlightthickness=0,
            cursor="hand2",
            bd=0
        )

        self.down_canvas = tk.Canvas(
            self.main_layout,
            width=NAV_BTN_SIZE,
            height=NAV_BTN_SIZE,
            bg=BG,
            highlightthickness=0,
            cursor="hand2",
            bd=0
        )

        self.up_canvas.place(relx=0.957, rely=0.38, anchor="e")
        self.down_canvas.place(relx=0.957, rely=0.62, anchor="e")

        self._draw_round_button(self.up_canvas, "▲")
        self._draw_round_button(self.down_canvas, "▼")

        self.up_canvas.bind("<Button-1>", lambda e: self.start_scroll(-1))
        self.up_canvas.bind("<ButtonRelease-1>", lambda e: self.stop_scroll())
        self.up_canvas.bind("<Leave>", lambda e: self.stop_scroll())

        self.down_canvas.bind("<Button-1>", lambda e: self.start_scroll(1))
        self.down_canvas.bind("<ButtonRelease-1>", lambda e: self.stop_scroll())
        self.down_canvas.bind("<Leave>", lambda e: self.stop_scroll())

        self._raise_floating_nav()
        self.update_region_buttons()

    # ============================================================
    # DRAWING HELPERS
    # ============================================================

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, fill, outline=None, width=1):
        if outline is None:
            outline = fill

        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]

        return canvas.create_polygon(
            points,
            smooth=True,
            fill=fill,
            outline=outline,
            width=width
        )

    def _draw_pill(self, canvas, color, text, text_color="white", width=155, height=45):
        canvas.delete("all")

        radius = height // 2

        canvas.create_oval(
            1,
            1,
            radius * 2,
            height - 1,
            fill=color,
            outline=color
        )
        canvas.create_oval(
            width - radius * 2,
            1,
            width - 1,
            height - 1,
            fill=color,
            outline=color
        )
        canvas.create_rectangle(
            radius,
            1,
            width - radius,
            height - 1,
            fill=color,
            outline=color
        )
        canvas.create_text(
            width // 2,
            height // 2,
            text=text,
            fill=text_color,
            font=("Helvetica", 10, "bold")
        )

    def _draw_region_button(self, canvas, text, active=False):
        canvas.delete("all")

        fill = BUTTON_ACTIVE if active else BUTTON_IDLE
        outline = BUTTON_ACTIVE if active else CARD_BORDER
        text_color = "#FFFFFF" if active else PRIMARY

        self._draw_rounded_rect(
            canvas,
            2,
            2,
            110,
            36,
            17,
            fill=fill,
            outline=outline,
            width=1
        )

        canvas.create_text(
            56,
            19,
            text=text.upper(),
            fill=text_color,
            font=("Helvetica", 10, "bold")
        )

    def _draw_favorite_filter_button(self):
        active = self.current_mode == "favorites"

        fill = DANGER if active else BUTTON_IDLE
        outline = DANGER if active else CARD_BORDER
        text_color = "#FFFFFF" if active else PRIMARY

        c = self.favorite_filter_canvas
        c.delete("all")

        self._draw_rounded_rect(
            c,
            2,
            2,
            148,
            36,
            17,
            fill=fill,
            outline=outline,
            width=1
        )

        c.create_text(
            75,
            19,
            text="♥ FAVORITES",
            fill=text_color,
            font=("Helvetica", 10, "bold")
        )

    def _draw_round_button(self, canvas, symbol):
        canvas.delete("all")

        size = NAV_BTN_SIZE

        canvas.create_oval(
            7,
            7,
            size - 2,
            size - 2,
            fill="#C9D6DE",
            outline="#C9D6DE",
            width=1
        )

        canvas.create_oval(
            4,
            4,
            size - 7,
            size - 7,
            fill=PRIMARY,
            outline=PRIMARY_DARK,
            width=1
        )

        canvas.create_text(
            (size - 3) // 2,
            (size - 3) // 2,
            text=symbol,
            fill="#FFFFFF",
            font=("Helvetica", 20, "bold")
        )

    def _draw_action_button(self, canvas, text, fill, outline, text_color, width, height):
        canvas.delete("all")

        self._draw_rounded_rect(
            canvas,
            2,
            2,
            width - 2,
            height - 2,
            18,
            fill=fill,
            outline=outline,
            width=1
        )

        canvas.create_text(
            width // 2,
            height // 2,
            text=text,
            fill=text_color,
            font=("Helvetica", 11, "bold")
        )

    # ============================================================
    # HEADER HELPERS
    # ============================================================

    def _get_detected_ingredients_list(self):
        detected_items = getattr(self.controller, "detected_items", []) or []
        detected_item = getattr(self.controller, "detected_item", "") or ""

        cleaned_items = [
            str(item).strip()
            for item in detected_items
            if item and str(item).strip()
        ]

        if cleaned_items:
            return cleaned_items

        if detected_item and str(detected_item).strip():
            return [str(detected_item).strip()]

        return []


    def _normalize_text_key(self, value):
        return str(value or "").strip().lower().replace("_", " ").replace("-", " ")

    def _detect_meat_type_from_text(self, text):
        clean = self._normalize_text_key(text)

        for meat_type, keywords in MEAT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in clean:
                    return meat_type

        return None

    def _is_bone_in_meat_text(self, text):
        clean = self._normalize_text_key(text)

        for keyword in BONE_IN_KEYWORDS:
            if keyword in clean:
                return True

        return False

    def _get_grams_per_serving_for_meat(self, meat_type=None, text=""):
        if self._is_bone_in_meat_text(text):
            return BONE_IN_GRAMS_PER_SERVING

        return MEAT_GRAMS_PER_SERVING.get(meat_type, BONELESS_GRAMS_PER_SERVING)

    def _round_weight_to_servings(self, weight_g, grams_per_serving):
        try:
            weight_g = float(weight_g)
            grams_per_serving = float(grams_per_serving)
        except Exception:
            return None

        if weight_g <= 0 or grams_per_serving <= 0:
            return None

        # Below 125g, keep the default minimum serving instead of returning 0.
        if weight_g < grams_per_serving:
            return MIN_SERVINGS if 'MIN_SERVINGS' in globals() else 1

        # Use floor division so the estimate does not go above the
        # available measured meat.
        # Example: 125g // 125g = 1 serving, 500g // 125g = 4 servings.
        servings = int(weight_g // grams_per_serving)

        if servings < 1:
            servings = 1

        return max(1, min(20, servings))

    def _get_estimated_serving_note(self):
        ingredient_weights = getattr(self.controller, "ingredient_weights", None)

        if not isinstance(ingredient_weights, dict):
            return ""

        for name, weight in ingredient_weights.items():
            meat_type = self._detect_meat_type_from_text(name)

            if not meat_type:
                continue

            try:
                weight_g = float(weight)
            except Exception:
                continue

            if weight_g <= 0:
                continue

            if weight_g <= 5:
                weight_g = weight_g * 1000

            grams_per_serving = self._get_grams_per_serving_for_meat(
                meat_type=meat_type,
                text=name
            )
            servings = self._round_weight_to_servings(weight_g, grams_per_serving)

            if not servings:
                continue

            meat_format = "bone-in" if grams_per_serving == BONE_IN_GRAMS_PER_SERVING else "boneless"
            return f"Estimated serving from meat: {servings} people ({int(round(weight_g))}g {meat_format} {meat_type})"

        return ""

    def _format_ingredients_for_header(self):
        ingredients = self._get_detected_ingredients_list()

        if not ingredients:
            return "Ingredients", "No scanned ingredients yet."

        cleaned = [item.lower() for item in ingredients]
        full_display = ", ".join(cleaned)

        max_visible = 2

        if len(cleaned) > max_visible:
            short_display = ", ".join(cleaned[:max_visible])
            short_display = f"{short_display} +{len(cleaned) - max_visible} more"
        else:
            short_display = full_display

        return short_display, full_display

    def _update_header_text(self):
        self.show_all_recipes = getattr(self.controller, "recipe_show_all", self.show_all_recipes)

        if self.show_all_recipes and self.current_mode != "favorites":
            self.title_label.config(text=f"All Recipes in {self.region_var.get()}")
            self.subtitle_label.config(
                text="Shortcut mode active: scanned ingredients are ignored. Press Ctrl + Shift + S again to return."
            )
            self._update_header_wrap()
            return

        short_display, full_display = self._format_ingredients_for_header()

        self._latest_short_ingredients = short_display
        self._latest_full_ingredients = full_display

        self.title_label.config(text=f"Recipes with {short_display}")

        serving_note = self._get_estimated_serving_note()

        if full_display == "No scanned ingredients yet.":
            subtitle = "Select a region, open a recipe, or save your favorite dishes for later."
        elif full_display != short_display:
            subtitle = f"Using ingredients: {full_display}"
        else:
            subtitle = "Select a region, open a recipe, or save your favorite dishes for later."

        if serving_note:
            subtitle = f"{subtitle}  •  {serving_note}"

        self.subtitle_label.config(text=subtitle)

        self._update_header_wrap()

    def _update_header_wrap(self, event=None):
        try:
            available_width = self.header_inner.winfo_width() - 185
            available_width = max(320, available_width)

            self.title_label.config(wraplength=available_width)
            self.subtitle_label.config(wraplength=available_width)
        except Exception:
            pass


    # ============================================================
    # IMAGE HELPERS
    # ============================================================

    def _resolve_image_path(self, image_path, region=""):
        if not image_path:
            return ""

        normalized_path = str(image_path).replace("\\", "/").strip()
        basename = os.path.basename(normalized_path)
        region = str(region or "").strip()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        cwd = os.getcwd()

        candidates = []

        if os.path.isabs(normalized_path):
            candidates.append(normalized_path)

        for root in (script_dir, cwd):
            candidates.extend([
                os.path.join(root, normalized_path),
                os.path.join(root, "dishes_pics", basename),
                os.path.join(root, "dishes pic", basename),
            ])

            if region:
                candidates.extend([
                    os.path.join(root, "dishes_pics", region, basename),
                    os.path.join(root, "dishes pic", region, basename),
                ])

        candidates.append(normalized_path)

        for candidate in candidates:
            candidate = os.path.abspath(candidate) if not os.path.isabs(candidate) else candidate
            if os.path.exists(candidate):
                return candidate

        recursive_patterns = []

        for root in (script_dir, cwd):
            recursive_patterns.extend([
                os.path.join(root, "dishes pic", "**", basename),
                os.path.join(root, "dishes_pics", "**", basename),
            ])

        for pattern in recursive_patterns:
            matches = glob.glob(pattern, recursive=True)
            for match in matches:
                if os.path.exists(match):
                    return match

        return normalized_path

    def _load_fitted_image(self, image_path, target_width, target_height, region=""):
        image_path = self._resolve_image_path(image_path, region=region)

        if not image_path or not os.path.exists(image_path):
            return None

        try:
            img = Image.open(image_path)
            img = ImageOps.exif_transpose(img).convert("RGBA")

            if hasattr(Image, "Resampling"):
                resample_filter = Image.Resampling.LANCZOS
            else:
                resample_filter = Image.LANCZOS

            fitted = ImageOps.fit(
                img,
                (target_width, target_height),
                method=resample_filter,
                centering=(0.5, 0.5)
            )

            background = Image.new("RGBA", (target_width, target_height), PLACEHOLDER)
            background.paste(fitted, (0, 0), fitted)

            photo = ImageTk.PhotoImage(background)
            self._image_refs.append(photo)

            return photo

        except Exception:
            return None

    # ============================================================
    # SCROLL HELPERS
    # ============================================================

    def _enable_mousewheel(self):
        def _bind(_event):
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux_up)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux_down)

        def _unbind(_event):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

        self.canvas.bind("<Enter>", _bind)
        self.canvas.bind("<Leave>", _unbind)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux_up(self, event):
        self.canvas.yview_scroll(-1, "units")

    def _on_mousewheel_linux_down(self, event):
        self.canvas.yview_scroll(1, "units")

    def start_scroll(self, direction):
        if self._scroll_job:
            self.after_cancel(self._scroll_job)

        self.canvas.yview_scroll(direction, "units")
        self._scroll_job = self.after(45, lambda: self.start_scroll(direction))

    def stop_scroll(self):
        if self._scroll_job:
            self.after_cancel(self._scroll_job)
            self._scroll_job = None

    # ============================================================
    # CORE LOGIC
    # ============================================================

    def get_ingredients_text(self):
        detected_items = getattr(self.controller, "detected_items", []) or []
        ingredient = getattr(self.controller, "detected_item", "") or ""

        cleaned_items = [
            str(item).strip().upper()
            for item in detected_items
            if item and str(item).strip()
        ]

        if cleaned_items:
            return ", ".join(cleaned_items)

        ingredient = str(ingredient).strip().upper()
        return ingredient or "YOUR INGREDIENTS"

    def _get_detected_items_for_matching(self):
        detected_items = getattr(self.controller, "detected_items", []) or []
        detected_item = getattr(self.controller, "detected_item", "") or ""

        cleaned_items = []
        for item in detected_items:
            item = str(item or "").strip()
            if item and item.lower() not in [x.lower() for x in cleaned_items]:
                cleaned_items.append(item)

        detected_item = str(detected_item or "").strip()
        if detected_item and detected_item.lower() not in [x.lower() for x in cleaned_items]:
            cleaned_items.append(detected_item)

        return cleaned_items

    def _strip_measurement_words(self, text):
        text = str(text or "").lower()
        text = text.replace("_", " ").replace("-", " ")

        # Remove common recipe measurements so matching focuses on the actual ingredient name.
        text = re.sub(r"\b\d+(?:\.\d+)?\s*g\b", " ", text)
        text = re.sub(r"\b\d+(?:\.\d+)?\s*(?:kg|kgs|lb|lbs|cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|ml|liter|litre|liters|litres|oz|ounces|piece|pieces|pc|pcs|clove|cloves|thumb|thumbs|bunch|bundle|stalk|stalks|head|medium|large|small)\b", " ", text)
        text = re.sub(r"\b(?:optional|sliced|chopped|minced|crushed|peeled|wedged|cubed|diced|thinly|finely|grated|ground|fresh|freshly|to|taste|and|or|of|the|a|an|with|without|cut|into|parts|pieces|see|notes|any|whole)\b", " ", text)
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return " ".join(text.split())

    def _meat_type_from_text(self, value):
        clean = str(value or "").strip().lower().replace("_", " ").replace("-", " ")

        candidates = []
        for meat_type, keywords in MEAT_KEYWORDS.items():
            for keyword in keywords:
                candidates.append((len(keyword), meat_type, keyword))

        for _length, meat_type, keyword in sorted(candidates, reverse=True):
            if keyword in clean:
                return meat_type

        return None

    def _ingredient_matches_text(self, recipe_ingredient, detected_name):
        recipe_text = str(recipe_ingredient or "").strip()
        detected_text = str(detected_name or "").strip()

        if not recipe_text or not detected_text:
            return False

        recipe_clean = self._strip_measurement_words(recipe_text)
        detected_clean = self._strip_measurement_words(detected_text)

        if not recipe_clean or not detected_clean:
            return False

        if recipe_clean == detected_clean:
            return True

        if detected_clean in recipe_clean or recipe_clean in detected_clean:
            return True

        detected_meat_type = self._meat_type_from_text(detected_text)
        if detected_meat_type and self._meat_type_from_text(recipe_text) == detected_meat_type:
            return True

        return False

    def _get_system_vegetable_key_from_text(self, text):
        clean = self._strip_measurement_words(text)

        if not clean:
            return None

        for vegetable_key, keywords in SYSTEM_MISSING_VEGETABLES.items():
            for keyword in keywords:
                keyword_clean = self._strip_measurement_words(keyword)
                if keyword_clean and (keyword_clean == clean or keyword_clean in clean):
                    return vegetable_key

        return None

    def _get_detected_system_vegetable_keys(self):
        detected_keys = set()

        for item in self._get_detected_items_for_matching():
            vegetable_key = self._get_system_vegetable_key_from_text(item)
            if vegetable_key:
                detected_keys.add(vegetable_key)

        return detected_keys

    def _get_missing_system_vegetables(self, dish_name):
        details = DISH_DETAILS.get(dish_name, {})
        recipe_ingredients = details.get("ingredients", []) or []
        detected_keys = self._get_detected_system_vegetable_keys()

        required_keys = []

        for ingredient in recipe_ingredients:
            vegetable_key = self._get_system_vegetable_key_from_text(ingredient)

            if vegetable_key and vegetable_key not in required_keys:
                required_keys.append(vegetable_key)

        missing_keys = [
            key
            for key in required_keys
            if key not in detected_keys
        ]

        return [
            MISSING_VEGETABLE_DISPLAY.get(key, key.title())
            for key in missing_keys
        ]

    def _format_missing_vegetables_preview(self, items):
        cleaned = [str(item).strip() for item in items if str(item).strip()]

        if not cleaned:
            return "None"

        preview = ", ".join(cleaned[:4])
        remaining = len(cleaned) - 4

        if remaining > 0:
            preview += f" +{remaining}"

        return preview

    def get_filtered_dishes(self):
        region = self.region_var.get()

        detected_items = [
            str(item).strip().upper()
            for item in (getattr(self.controller, "detected_items", []) or [])
            if item and str(item).strip()
        ]

        ingredient = str(getattr(self.controller, "detected_item", "") or "").strip().upper()

        region_matches = [
            dish_name
            for dish_name, details in DISH_DETAILS.items()
            if details.get("region") == region
        ]

        if self.show_all_recipes and self.current_mode != "favorites":
            return region_matches

        if detected_items:
            dishes = []

            for dish_name in region_matches:
                recipe_ingredients = [
                    str(item).strip().upper()
                    for item in DISH_DETAILS[dish_name].get("ingredients", [])
                ]

                if all(any(self._ingredient_matches_text(recipe_ingredient, item) for recipe_ingredient in recipe_ingredients) for item in detected_items):
                    dishes.append(dish_name)

        elif ingredient:
            dishes = []

            for dish_name in region_matches:
                recipe_ingredients = [
                    str(item).strip().upper()
                    for item in DISH_DETAILS[dish_name].get("ingredients", [])
                ]

                if any(self._ingredient_matches_text(recipe_ingredient, ingredient) for recipe_ingredient in recipe_ingredients):
                    dishes.append(dish_name)

        else:
            dishes = region_matches

        if self.current_mode == "favorites":
            favorites = getattr(self.controller, "favorite_dishes", set())
            dishes = [
                dish_name
                for dish_name in DISH_DETAILS
                if dish_name in favorites
            ]

        return dishes

    def show_dishes(self):
        self.stop_scroll()
        self._image_refs = []
        self.empty_state_frame = None

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        dishes = self.get_filtered_dishes()
        self._update_result_badge(len(dishes))

        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        if self.current_mode == "favorites":
            self.render_favorites_list(dishes)
            self._raise_floating_nav()
            return

        if not dishes:
            if self.show_all_recipes:
                message = f"No recipes available in {self.region_var.get()}."
            else:
                message = f"No recipes for {self.get_ingredients_text()} in {self.region_var.get()}."

            self._render_empty_state(
                title="No matching recipes found",
                message=message
            )
            self._raise_floating_nav()
            return

        cards_grid = tk.Frame(self.scrollable_frame, bg=SOFT_SURFACE)
        cards_grid.grid(row=0, column=0, sticky="n", pady=(4, 4))

        cards_grid.grid_columnconfigure(0, weight=0)
        cards_grid.grid_columnconfigure(1, weight=0)

        for index, dish_name in enumerate(dishes):
            card = self._create_dish_card(cards_grid, dish_name)

            if len(dishes) == 1:
                card.grid(
                    row=0,
                    column=0,
                    sticky="n",
                    padx=8,
                    pady=4
                )
            else:
                card.grid(
                    row=index // 2,
                    column=index % 2,
                    sticky="n",
                    padx=10,
                    pady=6
                )

        self._raise_floating_nav()

    def _truncate_text(self, text, max_chars=52):
        text = str(text).strip()

        if len(text) <= max_chars:
            return text

        return text[:max_chars - 3].rstrip() + "..."

    def _make_dish_info_preview(self, description):
        description = str(description or "").strip()

        if not description:
            return "Tap to view dish information"

        return self._truncate_text(description, max_chars=68)

    def _create_dish_card(self, parent, dish_name):
        details = DISH_DETAILS[dish_name]

        outer = tk.Frame(
            parent,
            bg=SHADOW,
            width=DISH_CARD_WIDTH,
            height=DISH_CARD_HEIGHT,
            padx=1,
            pady=1
        )
        outer.grid_propagate(False)
        outer.pack_propagate(False)

        card = tk.Frame(
            outer,
            bg=CARD_BG,
            width=DISH_CARD_WIDTH - 2,
            height=DISH_CARD_HEIGHT - 2,
            cursor="hand2"
        )
        card.pack(fill="both", expand=True)
        card.pack_propagate(False)

        image_holder = tk.Frame(
            card,
            bg=PLACEHOLDER,
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            cursor="hand2"
        )
        image_holder.pack(anchor="center", padx=8, pady=(5, 2))
        image_holder.pack_propagate(False)

        image = self._load_fitted_image(
            details.get("image", ""),
            IMAGE_WIDTH,
            IMAGE_HEIGHT,
            region=details.get("region", "")
        )

        if image:
            image_label = tk.Label(
                image_holder,
                image=image,
                bg=PLACEHOLDER,
                cursor="hand2"
            )
            image_label.place(
                x=0,
                y=0,
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT
            )
        else:
            image_label = tk.Label(
                image_holder,
                text="No Image",
                font=("Helvetica", 10, "bold"),
                fg=TEXT_MUTED,
                bg=PLACEHOLDER,
                cursor="hand2"
            )
            image_label.place(relx=0.5, rely=0.5, anchor="center")

        info = tk.Frame(card, bg=CARD_BG, cursor="hand2")
        info.pack(fill="x", expand=False, padx=8, pady=(0, 3))

        region_badge = tk.Label(
            info,
            text=str(details.get("region", "Unknown")).upper(),
            font=("Helvetica", 8, "bold"),
            fg=PRIMARY,
            bg=SOFT_SURFACE,
            padx=8,
            pady=0,
            cursor="hand2"
        )
        region_badge.pack(anchor="center", pady=(0, 1))

        display_name = self._truncate_text(dish_name, max_chars=36)

        title_box = tk.Frame(
            info,
            bg=CARD_BG,
            height=DISH_TITLE_AREA_HEIGHT,
            cursor="hand2"
        )
        title_box.pack(fill="x")
        title_box.pack_propagate(False)

        name_label = tk.Label(
            title_box,
            text=display_name,
            font=("Helvetica", 10, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG,
            wraplength=DISH_CARD_WIDTH - 34,
            justify="center",
            anchor="center",
            cursor="hand2"
        )
        name_label.pack(fill="both", expand=True)

        dish_info_preview = self._make_dish_info_preview(details.get("description", ""))

        info_box = tk.Frame(
            info,
            bg=CARD_BG,
            height=DISH_INFO_AREA_HEIGHT,
            cursor="hand2"
        )
        info_box.pack(fill="x", pady=(1, 0))
        info_box.pack_propagate(False)

        info_label = tk.Label(
            info_box,
            text=dish_info_preview,
            font=("Helvetica", 8),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            wraplength=DISH_CARD_WIDTH - 42,
            justify="center",
            anchor="center",
            cursor="hand2"
        )
        info_label.pack(fill="both", expand=True)

        click_widgets = [
            outer,
            card,
            image_holder,
            image_label,
            info,
            region_badge,
            title_box,
            name_label,
            info_box,
            info_label
        ]

        for widget in click_widgets:
            widget.bind("<Button-1>", lambda e, d=dish_name: self.open_dish(d))

        return outer

    # ============================================================
    # FAVORITES FULL-WIDTH LIST
    # ============================================================

    def render_favorites_list(self, dishes):
        if not dishes:
            self._render_empty_state(
                title="No favorite dishes yet",
                message="Open a recipe and tap the favorite button to save it here."
            )
            return

        list_frame = tk.Frame(self.scrollable_frame, bg=SOFT_SURFACE)
        list_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=6,
            pady=6
        )
        list_frame.grid_columnconfigure(0, weight=1)

        for dish_name in dishes:
            row = self._create_favorite_row(list_frame, dish_name)
            row.pack(fill="x", expand=True, pady=(0, 7))

    def _create_favorite_row(self, parent, dish_name):
        details = DISH_DETAILS[dish_name]

        outer = tk.Frame(parent, bg=SHADOW, padx=1, pady=1)

        row_card = tk.Frame(
            outer,
            bg=CARD_BG,
            height=FAV_ROW_HEIGHT,
            cursor="hand2"
        )
        row_card.pack(fill="x", expand=True)
        row_card.pack_propagate(False)

        unfavorite_holder = tk.Frame(
            row_card,
            bg=CARD_BG,
            width=FAV_BUTTON_AREA_WIDTH,
            height=FAV_ROW_HEIGHT
        )
        unfavorite_holder.pack(side="left", fill="y", padx=(9, 8), pady=0)
        unfavorite_holder.pack_propagate(False)

        unfavorite_btn = tk.Canvas(
            unfavorite_holder,
            width=118,
            height=36,
            bg=CARD_BG,
            highlightthickness=0,
            cursor="hand2"
        )
        unfavorite_btn.place(relx=0.5, rely=0.5, anchor="center")

        self._draw_action_button(
            unfavorite_btn,
            text="UNFAVORITE",
            fill=DANGER_SOFT,
            outline=DANGER_SOFT,
            text_color=DANGER,
            width=118,
            height=36
        )

        unfavorite_btn.bind("<Button-1>", lambda e, d=dish_name: self.remove_favorite(d))

        image_border = tk.Frame(
            row_card,
            bg=CARD_BORDER,
            padx=2,
            pady=2,
            cursor="hand2"
        )
        image_border.pack(side="left", padx=(0, 12), pady=11)

        image_holder = tk.Frame(
            image_border,
            bg=PLACEHOLDER,
            width=FAV_IMAGE_WIDTH,
            height=FAV_IMAGE_HEIGHT,
            cursor="hand2"
        )
        image_holder.pack()
        image_holder.pack_propagate(False)

        image = self._load_fitted_image(
            details.get("image", ""),
            FAV_IMAGE_WIDTH,
            FAV_IMAGE_HEIGHT,
            region=details.get("region", "")
        )

        if image:
            image_label = tk.Label(
                image_holder,
                image=image,
                bg=PLACEHOLDER,
                cursor="hand2"
            )
            image_label.place(
                x=0,
                y=0,
                width=FAV_IMAGE_WIDTH,
                height=FAV_IMAGE_HEIGHT
            )
        else:
            image_label = tk.Label(
                image_holder,
                text="No Image",
                font=("Helvetica", 8, "bold"),
                fg=TEXT_MUTED,
                bg=PLACEHOLDER,
                cursor="hand2"
            )
            image_label.place(relx=0.5, rely=0.5, anchor="center")

        info_frame = tk.Frame(row_card, bg=CARD_BG, cursor="hand2")
        info_frame.pack(side="left", fill="both", expand=True, padx=(0, 18), pady=12)

        name_label = tk.Label(
            info_frame,
            text=dish_name,
            font=("Helvetica", 12, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG,
            anchor="w",
            cursor="hand2"
        )
        name_label.pack(fill="x")

        region_label = tk.Label(
            info_frame,
            text=f"Originated from: {details.get('region', 'Unknown')}",
            font=("Helvetica", 9),
            fg=PRIMARY,
            bg=CARD_BG,
            anchor="w",
            cursor="hand2"
        )
        region_label.pack(fill="x", pady=(3, 0))

        description_preview = self._make_dish_info_preview(details.get("description", ""))

        description_label = tk.Label(
            info_frame,
            text=description_preview,
            font=("Helvetica", 9),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            anchor="w",
            wraplength=760,
            justify="left",
            cursor="hand2"
        )
        description_label.pack(fill="x", pady=(4, 0))

        click_widgets = [
            outer,
            row_card,
            image_border,
            image_holder,
            image_label,
            info_frame,
            name_label,
            region_label,
            description_label
        ]

        for widget in click_widgets:
            widget.bind("<Button-1>", lambda e, d=dish_name: self.open_dish(d))

        return outer

    # ============================================================
    # EMPTY STATE
    # ============================================================

    def _render_empty_state(self, title, message):
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_rowconfigure(0, weight=1)

        canvas_height = self.canvas.winfo_height()

        if canvas_height <= 1:
            canvas_height = self.content_card.winfo_height()

        if canvas_height <= 1:
            canvas_height = 360

        empty_height = max(canvas_height - 12, 260)

        empty_card = tk.Frame(self.scrollable_frame, bg=SOFT_SURFACE, height=empty_height)
        empty_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=0
        )
        empty_card.grid_propagate(False)
        empty_card.grid_columnconfigure(0, weight=1)
        empty_card.grid_rowconfigure(0, weight=1)

        self.empty_state_frame = empty_card

        empty_content = tk.Frame(empty_card, bg=SOFT_SURFACE)
        empty_content.grid(row=0, column=0, sticky="nsew")
        empty_content.grid_columnconfigure(0, weight=1)
        empty_content.grid_rowconfigure(0, weight=1)

        text_group = tk.Frame(empty_content, bg=SOFT_SURFACE)
        text_group.place(relx=0.5, rely=0.5, anchor="center")

        title_label = tk.Label(
            text_group,
            text=title,
            font=("Helvetica", 16, "bold"),
            fg=TEXT_DARK,
            bg=SOFT_SURFACE,
            anchor="center",
            justify="center"
        )
        title_label.pack(fill="x", pady=(0, 8))

        message_label = tk.Label(
            text_group,
            text=message,
            font=("Helvetica", 10),
            fg=TEXT_MUTED,
            bg=SOFT_SURFACE,
            wraplength=620,
            justify="center",
            anchor="center"
        )
        message_label.pack(fill="x")

    # ============================================================
    # UI STATE
    # ============================================================

    def _update_result_badge(self, count):
        label = "1 RECIPE" if count == 1 else f"{count} RECIPES"

        if self.current_mode == "favorites":
            label = "1 FAVORITE" if count == 1 else f"{count} FAVORITES"

        self._draw_pill(
            self.result_badge,
            color="#FFFFFF",
            text=label,
            text_color=PRIMARY,
            width=140,
            height=38
        )

    def update_region_buttons(self):
        for region, canvas in self.region_buttons.items():
            active = self.current_mode != "favorites" and region == self.region_var.get()
            self._draw_region_button(canvas, region, active=active)

        self._draw_favorite_filter_button()

    def show_favorites(self):
        self.show_all_recipes = False
        self.controller.recipe_show_all = False

        self.current_mode = "favorites"
        self.controller.recipe_mode = self.current_mode
        self.canvas.yview_moveto(0)
        self._update_header_text()
        self.update_region_buttons()
        self.show_dishes()
        self._raise_floating_nav()

    def set_region(self, region):
        self.region_var.set(region)
        self.current_mode = "region"
        self.controller.recipe_mode = self.current_mode
        self.canvas.yview_moveto(0)
        self._update_header_text()
        self.update_region_buttons()
        self.show_dishes()
        self._raise_floating_nav()

    # ============================================================
    # FAVORITES
    # ============================================================

    def remove_favorite(self, dish):
        if hasattr(self.controller, "is_favorite") and self.controller.is_favorite(dish):
            self.controller.toggle_favorite(dish)

        self.show_dishes()
        self._raise_floating_nav()

    # ============================================================
    # NAVIGATION
    # ============================================================

    def open_dish(self, dish):
        self.controller.selected_dish = dish

        frames = getattr(self.controller, "frames", {})

        if DishScreen in frames:
            self.controller.show_frame(DishScreen)
            return

        for name, frame in frames.items():
            if "DishScreen" in str(name):
                self.controller.show_frame(name)
                return

    def _go_to_scan_screen(self):
        frames = getattr(self.controller, "frames", {})

        for name, frame in frames.items():
            if "ScanScreen" in str(name):
                if hasattr(frame, "reset_screen"):
                    frame.reset_screen()

                self.controller.show_frame(name)
                return

    def scan_again(self):
        self.show_all_recipes = False
        self.controller.recipe_show_all = False

        self.controller.detected_item = None
        self.controller.detected_items = []
        self.controller.captured_frame = None
        self.controller.scan_more = False
        self.controller.scan_mode = "vegetable"
        self.controller.after_result_target = "choice"

        if hasattr(self.controller, "ingredient_weights"):
            self.controller.ingredient_weights = {}

        if hasattr(self.controller, "ingredient_servings"):
            self.controller.ingredient_servings = {}

        self._go_to_scan_screen()

    def scan_more_ingredients(self):
        from scan_choice import ScanChoiceScreen

        self.show_all_recipes = False
        self.controller.recipe_show_all = False

        self.controller.after_result_target = "recipe"

        choice_frame = self.controller.frames.get(ScanChoiceScreen)

        if choice_frame:
            self.controller.show_frame(ScanChoiceScreen)
            return

        self.controller.scan_mode = "vegetable"
        self.controller.scan_more = True
        self._go_to_scan_screen()

    # ============================================================
    # TKINTER OVERRIDES
    # ============================================================

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        self.current_mode = getattr(self.controller, "recipe_mode", "region")
        self.show_all_recipes = getattr(self.controller, "recipe_show_all", False)

        self._update_header_text()

        self.canvas.yview_moveto(0)
        self.update_region_buttons()
        self.show_dishes()
        self._raise_floating_nav()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

        if self.empty_state_frame is not None and self.empty_state_frame.winfo_exists():
            self.empty_state_frame.configure(height=max(event.height - 12, 260))

        self._raise_floating_nav()
