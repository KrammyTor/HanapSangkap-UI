import json
import os
import re
from fractions import Fraction
import glob
import tkinter as tk
from PIL import Image, ImageOps, ImageTk
import qrcode

# ============================================================
# DISH SCREEN
# ============================================================

ACCENT_COLOR = "#74B3CE"
PRIMARY = "#0D6791"
PRIMARY_DARK = "#09506F"
BG = "#F6F9FC"
SOFT_SURFACE = "#EEF5F8"
CARD_BG = "#FFFFFF"
CONTENT_BG = "#FBFDFE"
CARD_BORDER = "#DCE7EE"
TEXT_DARK = "#20323F"
TEXT_MUTED = "#637381"
TEXT_LIGHT = "#FFFFFF"
SHADOW = "#D6E0E7"
PLACEHOLDER = "#E8EEF2" 
SUCCESS = "#27AE60"
HEART_ACTIVE = "#FF6B6B"
HEART_IDLE = "#FFFFFF"

LOGO_PATH = "hanapsangkap.png"
DISH_JSON_FILENAME = "dishes.json"

# ============================================================
# SERVING / MEAT WEIGHT SETTINGS
# ============================================================
DEFAULT_BASE_SERVINGS = 4
MIN_SERVINGS = 1
MAX_SERVINGS = 20

# Meat serving guide based on the table reference:
# DOST-FNRI-based practical serving basis used by the system:
# 125g meat = 1 serving/person
# Examples:
# 125g meat -> 1 serving
# 250g meat -> 2 servings
# 500g meat -> 4 servings
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


# ============================================================
# MISSING INGREDIENT DISPLAY SETTINGS
# ============================================================
# Only these are shown as missing because these are the ingredients
# recognized by the vegetable detection model. Condiments, water,
# oil, seasoning cubes, sauces, and meat are not shown here.
SYSTEM_MISSING_INGREDIENTS = {
    "ampalaya": ["ampalaya", "bitter melon", "bitter gourd"],
    "cabbage": ["cabbage", "repolyo", "bok choy", "pechay"],
    "carrot": ["carrot", "carrots"],
    "corn": ["corn", "mais"],
    "eggplant": ["eggplant", "eggplants", "talong", "chinese eggplant"],
    "garlic": ["garlic", "bawang"],
    "ginger": ["ginger", "luya"],
    "okra": ["okra"],
    "onion": ["onion", "onions", "red onion", "white onion", "yellow onion", "sibuyas", "shallot", "shallots"],
    "potato": ["potato", "potatoes", "patatas"],
    "pumpkin": ["pumpkin", "squash", "kalabasa"],
    "radish": ["radish", "labanos", "daikon"],
    "sayote": ["sayote", "chayote"],
    "sitaw": ["sitaw", "string beans", "long beans", "green long beans"],
    "tomato": ["tomato", "tomatoes", "kamatis"],
}

MISSING_INGREDIENT_DISPLAY = {
    "ampalaya": "Ampalaya",
    "cabbage": "Cabbage",
    "carrot": "Carrot",
    "corn": "Corn",
    "eggplant": "Eggplant",
    "garlic": "Garlic",
    "ginger": "Ginger",
    "okra": "Okra",
    "onion": "Onion",
    "potato": "Potato",
    "pumpkin": "Pumpkin",
    "radish": "Radish",
    "sayote": "Sayote",
    "sitaw": "Sitaw",
    "tomato": "Tomato",
}

MEAT_KEYWORDS = {
    "pork": [
        "lechon kawali", "inihaw na liempo", "pork belly", "pork shoulder",
        "pork leg", "pork hock", "pig face", "pig ears", "pig liver",
        "pig lung", "pig intestines", "pig", "pork", "baboy", "liempo",
        "maskara", "belly", "ham", "speck", "etag", "chicharon",
        "pork cube", "pork cubes", "pork broth",
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

# Items that can contain meat words but should NOT receive the measured meat weight.
# They should keep their recipe quantity and scale normally with servings.
# Example: "1/2 cup beef franks or hotdogs" should not become "125 g 1/2 cup beef franks".
MEASURED_MEAT_WEIGHT_EXCLUDE_KEYWORDS = {
    "stock", "broth", "cube", "cubes", "bouillon",
    "hotdog", "hotdogs", "frank", "franks", "beef franks",
    "liver spread", "chicharon", "crackling", "cracklings",
    "ham", "sausage", "sausages",
}

# ============================================================
# DISH RECIPE URLS FROM DOCUMENT HYPERLINKS
# ============================================================
# These links came from the hyperlinks inside "Dishes (LuzViMin).docx".
# They are used to generate QR codes instead of opening a browser.
DISH_RECIPE_URLS = {
    "Dinakdakan": "https://panlasangpinoy.com/dinakdakan-recipe/",
    "Bicol Express": "https://panlasangpinoy.com/bicol-express/",
    "Laing": "https://panlasangpinoy.com/laing-recipe/",
    "Hardinera": "https://panlasangpinoy.com/hardinera/",
    "Bulalo": "https://panlasangpinoy.com/bulalo-stewed-beef-shank/",
    "Sisig": "https://panlasangpinoy.com/sisig-recipe-knr-kls/",
    "Kare – kare": "https://panlasangpinoy.com/kare-kare-recipe/",
    "Kare - kare": "https://panlasangpinoy.com/kare-kare-recipe/",
    "Kare Kare": "https://panlasangpinoy.com/kare-kare-recipe/",
    "Tinolang Isda": "https://panlasangpinoy.com/tinolang-isda/",
    "Ginisang Labanos": "https://panlasangpinoy.com/ginisang-labanos-recipe/",
    "Ensaladang Labanos": "https://www.pinoyrecipe.net/ensaladang-labanos-recipe/",
    "Lumpiang Gulay": "https://panlasangpinoy.com/lumpiang-gulay-vegetable-egg-roll-recipe/",
    "Pinikpikan": "https://www.angsarap.net/2022/03/22/pinikpikan/",
    "Pinakbet Ilocano": "https://theodehlicious.com/pinakbet-ilocano-recipe/",
    "Pinakbet Tagalog": "https://panlasangpinoy.com/pinakbet-tagalog-recipe-knr-sc/",
    "Beef Kaldereta": "https://www.yummy.ph/recipe/beef-kaldereta-recipe",
    "Pork Adobong Tagalog": "https://kusinasecrets.com/pork-adobong-tagalog/",
    "Bulanglang na Gulay": "https://panlasangpinoy.com/bulanglang-na-gulay-batangas_knr_fc/",
    "Sinigang": "https://panlasangpinoy.com/pork-sinigang-na-baboy-recipe/",
    "Pork Menudo": "https://panlasangpinoy.com/pork-menudo-recipe/",
    "Ginataang Kalabasa at Sitaw": "https://panlasangpinoy.com/ginataang-kalabasa-at-sitaw/",

    "Ginisang Okra": "https://panlasangpinoy.com/ginisang-okra-with-fish-flakes-recipe/",
    "Kinilaw Na Isda (Fish with Vinegar and Ginger)": "https://filipinochow.com/recipes/kinilaw-na-isda-fish-vinegar-ginger/",
    "Kinilaw Na Isda": "https://filipinochow.com/recipes/kinilaw-na-isda-fish-vinegar-ginger/",
    "Lansiao": "https://kusinasecrets.com/filipino-soup-number-5-lansiao/",
    "Cansi": "https://panlasangpinoy.com/cansi-recipe-ilonggo-bulalo-and-sinigang-in-one-delicious-soup-dish/",
    "Laswa": "https://panlasangpinoy.com/laswa-recipe/",
    "Kadyos, Baboy at Langka": "https://www.angsarap.net/2012/01/19/kbl-kadios-baboy-at-langka/",
    "Batchoy": "https://www.cookmunitybyajinomoto.com/recipes/batchoy-bisaya/",
    "Humba": "https://panlasangpinoy.com/filipino-food-pork-humba-recipe/",
    "Chicken Binakol": "https://panlasangpinoy.com/chicken-binakol-recipe/",
    "Paksiw na Isda": "https://panlasangpinoy.com/paksiw-na-isda-recipe/",
    "Tinolang Manok": "https://steemit.com/homesteading/@fabio2614/tinulang-manok-a-filipino-food",
    "Linagpang na Bangus": "https://www.angsarap.net/2017/04/12/linagpang-na-bangus/amp/",
    "Pork Adobong Bisaya": "https://kusinasecrets.com/adobong-bisaya/",
    "Utan Bisaya (Law-Uy)": "https://panlasangpinoy.com/easy-utan-bisaya-law-uy/",
    "Utan Bisaya": "https://panlasangpinoy.com/easy-utan-bisaya-law-uy/",
    "Bas – Uy": "https://panlasangpinoy.com/bas-uy-recipe/",
    "Bas-uy": "https://panlasangpinoy.com/bas-uy-recipe/",
    "Bas – Uy ": "https://panlasangpinoy.com/bas-uy-recipe/",
    "Pochero Bisaya": "https://www.yummy.ph/recipe/pochero-recipe",
    "Lutik": "https://www.yummy.ph/recipe/lutik-recipe-a157-20200122",
    "Balbacua": "https://panlasangpinoy.com/balbacua-recipe/",
    "Karne Frita": "https://www.yummy.ph/recipe/ilonggo-style-karne-frita-recipe-a1793-20210411",

    "Tiyula Itum": "https://www.angsarap.net/2020/06/10/tiyula-itum/",
    "Pinayanggang Manok": "https://theodehlicious.com/piyanggang-manok/",
    "Piyanggang Manok": "https://theodehlicious.com/piyanggang-manok/",
    "Sinina": "https://www.angsarap.net/2021/01/25/beef-sinina/",
    "Piaparan": "https://www.angsarap.net/2019/07/03/piaparan/",
    "Tausug Beef Kulma": "https://www.angsarap.net/2018/02/28/tausug-beef-kulma/",
    "Sampayna": "https://www.panlasangpinoymeatrecipes.com/sampayna-dinuguan-from-northern-mindanao.htm",
    "SInuglaw": "https://panlasangpinoy.com/sinuglaw-recipe/",
    "Sinuglaw": "https://panlasangpinoy.com/sinuglaw-recipe/",
    "Piyassak": "https://alltausug.blogspot.com/2009/12/piyassak_07.html",
    "Rendang": "https://www.angsarap.net/2022/12/26/riyandang/",
    "Adobong Pusit": "https://www.yummy.ph/recipe/adobong-pusit-recipe",
    "Beef Hinalang": "https://panlasangpinoy.com/beef-hinalang/",
    "Chicken Pastil": "https://www.angsarap.net/2021/12/13/chicken-pastil/",
    "Satti de Zamboanga": "https://www.foodwithmae.com/recipe-view/beef-bbq-with-spicy-gravy-satti-de-zamboanga/",
}

COUNT_UNITS = {
    "piece", "pieces", "pc", "pcs", "clove", "cloves", "thumb", "thumbs",
    "stalk", "stalks", "bunch", "bunches", "head", "heads", "cube", "cubes",
    "can", "cans", "pack", "packs", "packet", "packets", "leaf", "leaves",
    "onion", "onions", "tomato", "tomatoes", "eggplant", "eggplants", "potato",
    "potatoes", "carrot", "carrots", "banana", "bananas", "plantain", "plantains"
}

NO_SCALE_INGREDIENT_KEYWORDS = {
    "water",
}

UNICODE_FRACTIONS = {
    "¼": Fraction(1, 4),
    "½": Fraction(1, 2),
    "¾": Fraction(3, 4),
    "⅐": Fraction(1, 7),
    "⅑": Fraction(1, 9),
    "⅒": Fraction(1, 10),
    "⅓": Fraction(1, 3),
    "⅔": Fraction(2, 3),
    "⅕": Fraction(1, 5),
    "⅖": Fraction(2, 5),
    "⅗": Fraction(3, 5),
    "⅘": Fraction(4, 5),
    "⅙": Fraction(1, 6),
    "⅚": Fraction(5, 6),
    "⅛": Fraction(1, 8),
    "⅜": Fraction(3, 8),
    "⅝": Fraction(5, 8),
    "⅞": Fraction(7, 8),
}

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 185
TITLE_AREA_HEIGHT = 72
DESC_AREA_HEIGHT = 66

STEP_NUMBER_BOX_WIDTH = 48
STEP_NUMBER_BOX_HEIGHT = 44
STEP_CARD_PAD_Y = 7

STEP_WRAP_MAX = 560
STEP_WRAP_MIN = 170
INGREDIENT_WRAP_MAX = 560
INGREDIENT_WRAP_MIN = 170

def _base_dir():
    return os.path.dirname(os.path.abspath(__file__))

def _strip_json_comments(text):
    result = []
    i = 0
    in_string = False
    escaped = False

    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_string:
            result.append(char)

            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False

            i += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            i += 1
            continue

        if char == "/" and nxt == "/":
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)

def _remove_trailing_commas(text):
    old = None
    cleaned = text

    while old != cleaned:
        old = cleaned
        cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)

    return cleaned

def _count_missing_braces(text):
    opened = 0
    closed = 0
    in_string = False
    escaped = False

    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            opened += 1
        elif char == "}":
            closed += 1

    return max(0, opened - closed)

def _sanitize_json_text(text):
    cleaned = _strip_json_comments(text).strip()
    cleaned = re.sub(r",\s*$", "", cleaned)
    cleaned = _remove_trailing_commas(cleaned)

    missing = _count_missing_braces(cleaned)
    if missing:
        cleaned += "\n" + ("}" * missing)

    return cleaned

def _normalize_record(record):
    if not isinstance(record, dict):
        record = {}

    def list_clean(value):
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    base_servings = record.get("base_servings", record.get("servings", DEFAULT_BASE_SERVINGS))

    try:
        base_servings = int(base_servings)
    except Exception:
        base_servings = DEFAULT_BASE_SERVINGS

    base_servings = max(MIN_SERVINGS, min(MAX_SERVINGS, base_servings))

    return {
        "region": str(record.get("region", "Unknown") or "Unknown").strip(),
        "description": str(record.get("description", "") or "").strip(),
        "ingredients": list_clean(record.get("ingredients", [])),
        "steps": list_clean(record.get("steps", [])),
        "image": str(record.get("image", "") or "").strip(),
        "link": str(record.get("link", "") or "").strip(),
        "base_servings": base_servings,
        "servings": base_servings,
    }

def load_dish_details():
    paths = [
        os.path.join(_base_dir(), DISH_JSON_FILENAME),
        os.path.join(os.getcwd(), DISH_JSON_FILENAME),
        DISH_JSON_FILENAME,
    ]

    json_path = None

    for path in paths:
        path = os.path.abspath(path)
        if os.path.exists(path):
            json_path = path
            break

    if not json_path:
        print("[DISH] dishes.json not found.")
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            raw = file.read()
    except Exception as error:
        print(f"[DISH] Failed to read dishes.json: {error}")
        return {}

    try:
        parsed = json.loads(raw)
    except Exception:
        try:
            parsed = json.loads(_sanitize_json_text(raw))
        except Exception as error:
            print(f"[DISH] Failed to parse dishes.json: {error}")
            return {}

    if not isinstance(parsed, dict):
        print("[DISH] dishes.json must be a JSON object.")
        return {}

    dishes = {}

    for dish_name, record in parsed.items():
        dish_name = str(dish_name).strip()
        if dish_name:
            dishes[dish_name] = _normalize_record(record)

    print(f"[DISH] Loaded {len(dishes)} dish records from {json_path}")
    return dishes

DISH_DETAILS = load_dish_details()

class DishScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)

        self.controller = controller
        self._scroll_job = None
        self.current_image_ref = None
        self.step_labels = []
        self.ingredient_labels = []

        self.active_dish_name = None
        self.base_servings = DEFAULT_BASE_SERVINGS
        self.current_servings = DEFAULT_BASE_SERVINGS
        self.max_servings_from_meat = MAX_SERVINGS
        self.current_recipe_ingredients = []
        self.current_recipe_steps = []
        self.current_recipe_link = ""

        self.done_logo_original = None
        self.done_logo_photo = None
        self.done_logo_cache_size = None

        self._build_header()
        self._build_bottom_bar()
        self._build_content()
        self._bind_events()

    def _build_header(self):
        self.top_bar = tk.Frame(self, bg=PRIMARY)
        self.top_bar.pack(fill="x", side="top")

        header_inner = tk.Frame(self.top_bar, bg=PRIMARY)
        header_inner.pack(fill="x", padx=22, pady=10)
        header_inner.bind("<Configure>", self._update_header_wrap)

        left = tk.Frame(header_inner, bg=PRIMARY)
        left.pack(side="left", fill="both", expand=True)

        self.header_title = tk.Label(
            left,
            text="Recipe Details",
            font=("Helvetica", 22, "bold"),
            fg=TEXT_LIGHT,
            bg=PRIMARY,
            anchor="w",
            justify="left"
        )
        self.header_title.pack(fill="x")

        self.region_badge = tk.Canvas(
            header_inner,
            width=140,
            height=38,
            bg=PRIMARY,
            highlightthickness=0
        )
        self.region_badge.pack(side="right", padx=(12, 0))
        self._draw_pill(self.region_badge, "REGION", 140, 38)

    def _build_bottom_bar(self):
        self.bottom_bar = tk.Frame(self, bg=PRIMARY)
        self.bottom_bar.pack(fill="x", side="bottom")

        button_center_frame = tk.Frame(self.bottom_bar, bg=PRIMARY)
        button_center_frame.pack(expand=True, pady=8)

        self.back_button = tk.Canvas(
            button_center_frame,
            width=165,
            height=46,
            bg=PRIMARY,
            highlightthickness=0,
            cursor="hand2"
        )
        self.back_button.pack(side="left", padx=10)

        self._draw_action_button(
            self.back_button,
            text="BACK",
            fill=ACCENT_COLOR,
            outline=ACCENT_COLOR,
            text_color="#FFFFFF",
            width=165,
            height=46
        )

        self.done_button = tk.Canvas(
            button_center_frame,
            width=220,
            height=46,
            bg=PRIMARY,
            highlightthickness=0,
            cursor="hand2"
        )
        self.done_button.pack(side="left", padx=10)

        self._draw_action_button(
            self.done_button,
            text="DONE COOKING",
            fill=SUCCESS,
            outline=SUCCESS,
            text_color="#FFFFFF",
            width=220,
            height=46
        )

        self.back_card = self.back_button
        self.back_label = self.back_button
        self.scan_card = self.done_button
        self.scan_label = self.done_button

    def _build_content(self):
        self.content_main = tk.Frame(self, bg=BG)
        self.content_main.pack(expand=True, fill="both", padx=10, pady=8)

        left_card_outer = tk.Frame(self.content_main, bg=SHADOW, padx=1, pady=1)
        left_card_outer.pack(side="left", fill="y", padx=(0, 12))

        self.left_side = tk.Frame(left_card_outer, bg=CARD_BG, width=375)
        self.left_side.pack(fill="both", expand=True)
        self.left_side.pack_propagate(False)

        self.image_border = tk.Frame(self.left_side, bg=CARD_BORDER, padx=2, pady=2)
        self.image_border.pack(pady=(10, 5))

        self.image_frame = tk.Frame(
            self.image_border,
            bg=PLACEHOLDER,
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT
        )
        self.image_frame.pack()
        self.image_frame.pack_propagate(False)

        self.image_canvas = tk.Canvas(
            self.image_frame,
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            bg=PLACEHOLDER,
            highlightthickness=0
        )
        self.image_canvas.place(relx=0.5, rely=0.5, anchor="center")

        self.title_box = tk.Frame(self.left_side, bg=CARD_BG, height=TITLE_AREA_HEIGHT)
        self.title_box.pack(fill="x", padx=12, pady=(2, 3))
        self.title_box.pack_propagate(False)

        self.title_label = tk.Label(
            self.title_box,
            text="Dish Name",
            font=("Helvetica", 19, "bold"),
            fg=PRIMARY,
            bg=CARD_BG,
            wraplength=335,
            justify="center",
            anchor="center"
        )
        self.title_label.pack(fill="both", expand=True)

        self.desc_shell = tk.Frame(self.left_side, bg=SOFT_SURFACE, height=DESC_AREA_HEIGHT)
        self.desc_shell.pack(fill="x", padx=12, pady=(0, 10))
        self.desc_shell.pack_propagate(False)

        self.desc_label = tk.Label(
            self.desc_shell,
            text="Description",
            font=("Helvetica", 9),
            fg=TEXT_MUTED,
            bg=SOFT_SURFACE,
            wraplength=320,
            justify="center",
            anchor="center"
        )
        self.desc_label.pack(fill="both", expand=True, padx=10, pady=5)

        recipe_outer = tk.Frame(self.content_main, bg=SHADOW, padx=1, pady=1)
        recipe_outer.pack(side="left", expand=True, fill="both")

        self.recipe_inner = tk.Frame(recipe_outer, bg=CARD_BG)
        self.recipe_inner.pack(expand=True, fill="both")

        card_header = tk.Frame(self.recipe_inner, bg=CARD_BG)
        card_header.pack(fill="x", padx=18, pady=(10, 0))

        title_wrap = tk.Frame(card_header, bg=CARD_BG)
        title_wrap.pack(side="left", fill="x", expand=True)

        self.recipe_title = tk.Label(
            title_wrap,
            text="How to Cook",
            font=("Helvetica", 21, "bold"),
            fg=PRIMARY,
            bg=CARD_BG,
            anchor="w"
        )
        self.recipe_title.pack(fill="x")

        self.recipe_subtitle = tk.Label(
            title_wrap,
            text="Follow the recipe below.",
            font=("Helvetica", 10),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            anchor="w"
        )
        self.recipe_subtitle.pack(fill="x", pady=(2, 0))

        self.serving_control_frame = tk.Frame(title_wrap, bg=CARD_BG)
        self.serving_control_frame.pack(fill="x", pady=(6, 0))

        self.serving_label = tk.Label(
            self.serving_control_frame,
            text="Servings",
            font=("Helvetica", 10, "bold"),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            anchor="w"
        )
        self.serving_label.pack(side="left", padx=(0, 8))

        self.serving_minus_btn = tk.Label(
            self.serving_control_frame,
            text="−",
            font=("Helvetica", 14, "bold"),
            fg=TEXT_LIGHT,
            bg=PRIMARY,
            width=3,
            height=1,
            cursor="hand2"
        )
        self.serving_minus_btn.pack(side="left")

        self.serving_value_label = tk.Label(
            self.serving_control_frame,
            text=str(DEFAULT_BASE_SERVINGS),
            font=("Helvetica", 14, "bold"),
            fg=PRIMARY,
            bg=SOFT_SURFACE,
            width=4,
            height=1
        )
        self.serving_value_label.pack(side="left", padx=5)

        self.serving_plus_btn = tk.Label(
            self.serving_control_frame,
            text="+",
            font=("Helvetica", 14, "bold"),
            fg=TEXT_LIGHT,
            bg=PRIMARY,
            width=3,
            height=1,
            cursor="hand2"
        )
        self.serving_plus_btn.pack(side="left")

        scroll_nav_frame = tk.Frame(card_header, bg=CARD_BG)
        scroll_nav_frame.pack(side="right", padx=(8, 8), anchor="n")

        self.down_canvas = tk.Canvas(
            scroll_nav_frame,
            width=46,
            height=46,
            bg=CARD_BG,
            highlightthickness=0,
            cursor="hand2"
        )
        self.down_canvas.pack(side="left", padx=3)
        self._draw_scroll_button(self.down_canvas, "▼", size=46)

        self.up_canvas = tk.Canvas(
            scroll_nav_frame,
            width=46,
            height=46,
            bg=CARD_BG,
            highlightthickness=0,
            cursor="hand2"
        )
        self.up_canvas.pack(side="left", padx=3)
        self._draw_scroll_button(self.up_canvas, "▲", size=46)

        recipe_body = tk.Frame(self.recipe_inner, bg=CARD_BG)
        recipe_body.pack(fill="both", expand=True, pady=(6, 10))

        self.canvas = tk.Canvas(recipe_body, bg=CARD_BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=18)

        self.scroll_content = tk.Frame(self.canvas, bg=CARD_BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scroll_content,
            anchor="nw"
        )

        self.scroll_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _bind_events(self):
        self.up_canvas.bind("<Button-1>", lambda e: self.start_scroll(-1))
        self.up_canvas.bind("<ButtonRelease-1>", lambda e: self.stop_scroll())
        self.up_canvas.bind("<Leave>", lambda e: self.stop_scroll())

        self.down_canvas.bind("<Button-1>", lambda e: self.start_scroll(1))
        self.down_canvas.bind("<ButtonRelease-1>", lambda e: self.stop_scroll())
        self.down_canvas.bind("<Leave>", lambda e: self.stop_scroll())

        self.back_button.bind("<Button-1>", lambda e: self.go_back())
        self.done_button.bind("<Button-1>", lambda e: self.done_cooking())

        self.serving_minus_btn.bind("<Button-1>", lambda e: self.change_servings(-1))
        self.serving_plus_btn.bind("<Button-1>", lambda e: self.change_servings(1))

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

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

    def _draw_scroll_button(self, canvas, symbol, size=46):
        canvas.delete("all")
        width, height = size, size

        canvas.create_oval(
            5,
            6,
            width - 2,
            height - 1,
            fill="#C9D6DE",
            outline="#C9D6DE"
        )

        canvas.create_oval(
            2,
            2,
            width - 6,
            height - 6,
            fill=PRIMARY,
            outline=PRIMARY_DARK,
            width=1
        )

        canvas.create_text(
            (width - 4) // 2,
            (height - 4) // 2,
            text=symbol,
            fill="white",
            font=("Helvetica", 15, "bold")
        )

    def _draw_pill(self, canvas, text, width, height):
        canvas.delete("all")
        radius = height // 2

        canvas.create_oval(1, 1, radius * 2, height - 1, fill="#FFFFFF", outline="#FFFFFF")
        canvas.create_oval(width - radius * 2, 1, width - 1, height - 1, fill="#FFFFFF", outline="#FFFFFF")
        canvas.create_rectangle(radius, 1, width - radius, height - 1, fill="#FFFFFF", outline="#FFFFFF")

        canvas.create_text(
            width // 2,
            height // 2,
            text=text.upper(),
            fill=PRIMARY,
            font=("Helvetica", 10, "bold")
        )

    def _draw_step_number(self, parent, number):
        number_canvas = tk.Canvas(
            parent,
            width=STEP_NUMBER_BOX_WIDTH,
            height=STEP_NUMBER_BOX_HEIGHT,
            bg=CONTENT_BG,
            highlightthickness=0
        )
        number_canvas.pack()

        number_canvas.create_rectangle(
            5,
            4,
            STEP_NUMBER_BOX_WIDTH - 5,
            STEP_NUMBER_BOX_HEIGHT - 4,
            fill=ACCENT_COLOR,
            outline=ACCENT_COLOR
        )

        number_canvas.create_text(
            STEP_NUMBER_BOX_WIDTH // 2,
            STEP_NUMBER_BOX_HEIGHT // 2,
            text=str(number),
            fill="#FFFFFF",
            font=("Helvetica", 13, "bold")
        )

    def _draw_favorite_icon(self, is_favorite):
        heart_symbol = "♥" if is_favorite else "♡"
        heart_color = HEART_ACTIVE if is_favorite else HEART_IDLE
        circle_radius = 22
        margin = 8
        x_pos = IMAGE_WIDTH - circle_radius - margin
        y_pos = circle_radius + margin

        self.image_canvas.delete("favorite_icon")

        self.image_canvas.create_oval(
            x_pos - circle_radius + 3,
            y_pos - circle_radius + 4,
            x_pos + circle_radius + 3,
            y_pos + circle_radius + 4,
            fill="#B9C9D3",
            outline="#B9C9D3",
            tags=("favorite_icon",)
        )

        self.image_canvas.create_oval(
            x_pos - circle_radius,
            y_pos - circle_radius,
            x_pos + circle_radius,
            y_pos + circle_radius,
            fill=PRIMARY,
            outline=PRIMARY_DARK,
            width=1,
            tags=("favorite_icon",)
        )

        self.image_canvas.create_text(
            x_pos,
            y_pos + 1,
            text=heart_symbol,
            fill=heart_color,
            font=("Helvetica", 24, "bold"),
            tags=("favorite_icon",)
        )

        self.image_canvas.tag_bind(
            "favorite_icon",
            "<Button-1>",
            lambda e: self.toggle_current_favorite()
        )

    def _get_title_font(self, dish_name):
        length = len(str(dish_name))

        if length >= 36:
            return ("Helvetica", 14, "bold")
        if length >= 29:
            return ("Helvetica", 15, "bold")
        if length >= 23:
            return ("Helvetica", 17, "bold")

        return ("Helvetica", 19, "bold")

    def _get_header_font(self, dish_name):
        length = len(str(dish_name))

        if length >= 38:
            return ("Helvetica", 18, "bold")
        if length >= 30:
            return ("Helvetica", 20, "bold")

        return ("Helvetica", 22, "bold")

    def _get_description_font(self, description):
        length = len(str(description))

        if length >= 95:
            return ("Helvetica", 8)
        if length >= 70:
            return ("Helvetica", 8)
        if length >= 55:
            return ("Helvetica", 9)

        return ("Helvetica", 10)

    def _update_header_wrap(self, event=None):
        try:
            available_width = self.top_bar.winfo_width() - 210
            available_width = max(320, available_width)
            self.header_title.config(wraplength=available_width)
        except Exception:
            pass

    def _get_safe_step_wrap(self):
        canvas_width = self.canvas.winfo_width()

        if canvas_width <= 1:
            return STEP_WRAP_MAX

        safe_wrap = canvas_width - (STEP_NUMBER_BOX_WIDTH + 24) - 58
        safe_wrap = max(STEP_WRAP_MIN, safe_wrap)
        safe_wrap = min(STEP_WRAP_MAX, safe_wrap)

        return safe_wrap

    def _get_safe_ingredient_wrap(self):
        canvas_width = self.canvas.winfo_width()

        if canvas_width <= 1:
            return INGREDIENT_WRAP_MAX

        safe_wrap = canvas_width - 76
        safe_wrap = max(INGREDIENT_WRAP_MIN, safe_wrap)
        safe_wrap = min(INGREDIENT_WRAP_MAX, safe_wrap)

        return safe_wrap

    def _refresh_content_wraps(self):
        safe_step_wrap = self._get_safe_step_wrap()
        safe_ingredient_wrap = self._get_safe_ingredient_wrap()

        for label in self.step_labels:
            if label.winfo_exists():
                label.configure(wraplength=safe_step_wrap)

        for label in self.ingredient_labels:
            if label.winfo_exists():
                label.configure(wraplength=safe_ingredient_wrap)

    def _refresh_step_wraps(self):
        self._refresh_content_wraps()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._refresh_content_wraps()

    def _resolve_image_path(self, image_path, region=""):
        if not image_path:
            return ""

        normalized_path = str(image_path).replace("\\", "/").strip()
        basename = os.path.basename(normalized_path)
        region = str(region or "").strip()

        script_dir = _base_dir()
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

        for candidate in candidates:
            candidate = os.path.abspath(candidate) if not os.path.isabs(candidate) else candidate
            if os.path.exists(candidate):
                return candidate

        for root in (script_dir, cwd):
            for pattern in [
                os.path.join(root, "dishes pic", "**", basename),
                os.path.join(root, "dishes_pics", "**", basename),
            ]:
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

            return ImageTk.PhotoImage(background)

        except Exception as error:
            print(f"[DISH] Failed to load image '{image_path}': {error}")
            return None

    def _render_dish_image(self, image):
        self.image_canvas.delete("all")

        if image:
            self.image_canvas.create_image(
                IMAGE_WIDTH // 2,
                IMAGE_HEIGHT // 2,
                image=image,
                anchor="center",
                tags=("dish_image",)
            )
            self.image_canvas.image = image
            self.current_image_ref = image
        else:
            self.image_canvas.image = None
            self.current_image_ref = None

            self.image_canvas.create_rectangle(
                0,
                0,
                IMAGE_WIDTH,
                IMAGE_HEIGHT,
                fill=PLACEHOLDER,
                outline=PLACEHOLDER
            )

            self.image_canvas.create_text(
                IMAGE_WIDTH // 2,
                IMAGE_HEIGHT // 2,
                text="No Image",
                font=("Helvetica", 14, "bold"),
                fill=TEXT_MUTED,
                tags=("dish_image",)
            )

        dish_name = getattr(self.controller, "selected_dish", None)

        try:
            is_favorite = self.controller.is_favorite(dish_name)
        except Exception:
            is_favorite = False

        self._draw_favorite_icon(is_favorite)

    def _bind_mousewheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux_up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux_down)

    def _unbind_mousewheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

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
        self._scroll_job = self.after(50, lambda: self.start_scroll(direction))

    def stop_scroll(self):
        if self._scroll_job:
            self.after_cancel(self._scroll_job)
            self._scroll_job = None

    def _clear_scroll_content(self):
        self.step_labels = []
        self.ingredient_labels = []

        for widget in self.scroll_content.winfo_children():
            widget.destroy()

    def _render_section_title(self, text, count_text=None):
        section_header = tk.Frame(self.scroll_content, bg=CARD_BG)
        section_header.pack(fill="x", pady=(8, 6))

        title = tk.Label(
            section_header,
            text=text,
            font=("Helvetica", 15, "bold"),
            fg=PRIMARY,
            bg=CARD_BG,
            anchor="w"
        )
        title.pack(side="left")

        if count_text:
            badge = tk.Label(
                section_header,
                text=count_text,
                font=("Helvetica", 9, "bold"),
                fg=PRIMARY,
                bg=SOFT_SURFACE,
                padx=10,
                pady=3
            )
            badge.pack(side="left", padx=(8, 0))

    # ============================================================
    # SERVING SCALER HELPERS
    # ============================================================

    def _get_base_servings_from_data(self, data):
        try:
            servings = int(data.get("base_servings", data.get("servings", DEFAULT_BASE_SERVINGS)))
        except Exception:
            servings = DEFAULT_BASE_SERVINGS

        return max(MIN_SERVINGS, min(MAX_SERVINGS, servings))

    def _normalize_text_key(self, value):
        clean = str(value or "").strip().lower()
        clean = clean.replace("_", " ").replace("-", " ").replace("/", " ")
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def _detect_meat_type_from_text(self, text):
        clean = self._normalize_text_key(text)

        candidates = []
        for meat_type, keywords in MEAT_KEYWORDS.items():
            for keyword in keywords:
                candidates.append((len(keyword), meat_type, keyword))

        for _length, meat_type, keyword in sorted(candidates, reverse=True):
            if keyword in clean:
                return meat_type

        return None

    def _is_bone_in_meat_text(self, text):
        clean = self._normalize_text_key(text)

        for keyword in BONE_IN_KEYWORDS:
            if keyword in clean:
                return True

        return False

    def _get_grams_per_serving_for_meat(self, meat_type=None, recipe_text="", source_text=""):
        combined = f"{recipe_text} {source_text}"

        if self._is_bone_in_meat_text(combined):
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
            return MIN_SERVINGS

        # Use floor division so the selected servings will not require
        # more meat than the measured weight.
        # Example: 125g // 125g = 1 serving,
        # 500g // 125g = 4 servings.
        servings = int(weight_g // grams_per_serving)

        if servings < MIN_SERVINGS:
            servings = MIN_SERVINGS

        servings = min(MAX_SERVINGS, servings)
        return servings

    def _extract_meat_grams_from_ingredient(self, ingredient):
        text = self._normalize_meat_units_to_grams(ingredient)
        meat_type = self._detect_meat_type_from_text(text)

        if not meat_type:
            return None

        match = re.search(r"\b(\d+(?:\.\d+)?)\s*g\b", text, flags=re.IGNORECASE)

        if not match:
            return None

        try:
            grams = float(match.group(1))
        except Exception:
            return None

        if grams <= 0:
            return None

        grams_per_serving = self._get_grams_per_serving_for_meat(
            meat_type=meat_type,
            recipe_text=text
        )

        return grams, grams_per_serving, text

    def _estimate_base_servings_from_recipe_ingredients(self, ingredients):
        total_serving_units = 0.0

        for ingredient in ingredients or []:
            parsed = self._extract_meat_grams_from_ingredient(ingredient)

            if not parsed:
                continue

            grams, grams_per_serving, _text = parsed
            total_serving_units += grams / grams_per_serving

        if total_serving_units <= 0:
            return None

        servings = int(total_serving_units + 0.5)
        return max(MIN_SERVINGS, min(MAX_SERVINGS, servings))

    def _format_grams(self, grams):
        try:
            grams = float(grams)
        except Exception:
            return str(grams)

        grams = int(round(grams))

        if grams <= 0:
            grams = 1

        return f"{grams}g"

    def _normalize_meat_units_to_grams(self, ingredient):
        text = str(ingredient or "").strip()
        text = self._convert_oz_to_grams_in_text(text)

        if not text:
            return text

        if not self._detect_meat_type_from_text(text):
            return text

        number_pattern = r"(?:\d+(?:\.\d+)?(?:\s+(?:\d+/\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]))?|\d+/\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])"
        pattern = (
            r"^(?P<qty>" + number_pattern + r")\s*"
            r"(?P<unit>kg|kilo|kilos|kilogram|kilograms|lb|lbs|pound|pounds|g|gram|grams)\.?\s*"
            r"(?P<rest>.*)$"
        )

        match = re.match(pattern, text, flags=re.IGNORECASE)

        if not match:
            return text

        qty = self._parse_quantity_token(match.group("qty"))

        if qty is None:
            return text

        unit = match.group("unit").lower().replace(".", "")
        rest = match.group("rest") or ""

        if unit in ("kg", "kilo", "kilos", "kilogram", "kilograms"):
            grams = float(qty) * 1000
        elif unit in ("lb", "lbs", "pound", "pounds"):
            grams = float(qty) * 453.59237
        else:
            grams = float(qty)

        return f"{self._format_grams(grams)} {rest}".strip()

    def _unit_after_quantity(self, rest):
        rest = str(rest or "").strip()
        match = re.match(r"^([A-Za-z]+)\b", rest)
        if not match:
            return ""
        return match.group(1).lower()

    def _is_count_unit_rest(self, rest):
        return self._unit_after_quantity(rest) in COUNT_UNITS

    def _is_gram_unit_rest(self, rest):
        return self._unit_after_quantity(rest) in {"g", "gram", "grams"}

    def _clean_scaled_unit(self, unit, scaled_qty):
        unit = str(unit or "").strip()
        qty_text = str(scaled_qty or "").strip()

        if qty_text == "1":
            singular = {
                "cups": "cup", "tablespoons": "tablespoon", "tbsp": "tbsp",
                "teaspoons": "teaspoon", "tsp": "tsp", "pieces": "piece",
                "pcs": "pc", "cloves": "clove", "thumbs": "thumb",
                "stalks": "stalk", "heads": "head", "bunches": "bunch",
                "bundles": "bundle", "cans": "can", "packs": "pack",
                "packets": "packet", "ounces": "ounce", "grams": "gram",
                "liters": "liter", "litres": "litre"
            }
            return singular.get(unit.lower(), unit)

        return unit

    def _scale_quantity_for_unit(self, quantity_text, scale_factor, rest):
        quantity = self._parse_quantity_token(quantity_text)

        if quantity is None:
            return quantity_text

        scaled = quantity * Fraction(scale_factor).limit_denominator(100)

        if self._is_count_unit_rest(rest):
            rounded = int(round(float(scaled)))
            if rounded <= 0 and float(scaled) > 0:
                rounded = 1
            return str(rounded)

        if self._is_gram_unit_rest(rest):
            return str(max(1, int(round(float(scaled)))))

        return self._format_scaled_quantity(scaled)

    def _extract_number_from_weight_text(self, value):
        text = str(value or "").strip().lower()

        if not text:
            return None

        match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|kilo|kilos|kilogram|kilograms|g|gram|grams)?", text)
        if not match:
            return None

        try:
            number = float(match.group(1))
        except Exception:
            return None

        unit = (match.group(2) or "").lower()

        if unit in ("kg", "kilo", "kilos", "kilogram", "kilograms"):
            return number * 1000

        if unit in ("g", "gram", "grams"):
            return number

        return self._normalize_weight_to_grams(number)

    def _normalize_weight_to_grams(self, value):
        if value is None:
            return None

        if isinstance(value, dict):
            for key in (
                "grams", "gram", "g", "weight_g", "meat_weight_g",
                "weight_grams", "detected_weight_g", "value"
            ):
                if key in value:
                    parsed = self._normalize_weight_to_grams(value.get(key))
                    if parsed is not None:
                        return parsed

            for key in ("kg", "weight_kg", "meat_weight_kg"):
                if key in value:
                    try:
                        kg_value = float(value.get(key))
                        if kg_value > 0:
                            return kg_value * 1000
                    except Exception:
                        pass

            return None

        if isinstance(value, str):
            parsed = self._extract_number_from_weight_text(value)
            if parsed is not None:
                return parsed
            return None

        try:
            weight_value = float(value)
        except Exception:
            return None

        if weight_value <= 0:
            return None

        # If the value is 5 or below, treat it as kilograms.
        # If it is above 5, treat it as grams.
        if weight_value <= 5:
            return weight_value * 1000

        return weight_value

    def _get_name_from_meat_record(self, record):
        if isinstance(record, dict):
            for key in (
                "name", "meat", "meat_type", "type", "label", "class",
                "detected_meat", "selected_meat", "ingredient"
            ):
                value = record.get(key)
                if value:
                    return str(value)
            return ""

        if isinstance(record, (list, tuple)) and record:
            return str(record[0])

        return str(record or "")

    def _get_weight_from_meat_record(self, record):
        if isinstance(record, dict):
            return self._normalize_weight_to_grams(record)

        if isinstance(record, (list, tuple)) and len(record) >= 2:
            return self._normalize_weight_to_grams(record[1])

        return self._normalize_weight_to_grams(record)

    def _get_saved_meat_weights(self):
        meats = []
        seen = set()

        def add_meat(name, weight):
            meat_type = self._detect_meat_type_from_text(name)

            if not meat_type:
                return

            weight_g = self._normalize_weight_to_grams(weight)

            if weight_g is None:
                return

            key = (meat_type, int(round(weight_g)))
            if key in seen:
                return

            seen.add(key)
            meats.append((meat_type, weight_g, str(name)))

        def add_record(record):
            if isinstance(record, dict):
                name = self._get_name_from_meat_record(record)
                weight = self._get_weight_from_meat_record(record)
                add_meat(name, weight)
                return

            if isinstance(record, (list, tuple)) and len(record) >= 2:
                add_meat(record[0], record[1])
                return

            text = str(record or "")
            meat_type = self._detect_meat_type_from_text(text)
            weight = self._extract_number_from_weight_text(text)

            if meat_type and weight is not None:
                add_meat(text, weight)

        ingredient_weights = getattr(self.controller, "ingredient_weights", None)

        if isinstance(ingredient_weights, dict):
            for name, weight in ingredient_weights.items():
                add_meat(name, weight)
        elif isinstance(ingredient_weights, (list, tuple, set)):
            for record in ingredient_weights:
                add_record(record)

        # Other possible places where scan.py versions may store meat data.
        for attr in (
            "meat_weights", "saved_meat_weights", "scanned_meats",
            "detected_meats", "selected_meats", "meat_detections"
        ):
            value = getattr(self.controller, attr, None)
            if isinstance(value, dict):
                for name, weight in value.items():
                    add_meat(name, weight)
            elif isinstance(value, (list, tuple, set)):
                for record in value:
                    add_record(record)

        possible_meat_names = []
        for attr in (
            "detected_meat", "selected_meat", "meat_type", "last_meat_type",
            "detected_item", "selected_ingredient", "current_meat",
            "latest_meat", "last_detected_meat"
        ):
            value = getattr(self.controller, attr, None)
            if value:
                possible_meat_names.append(str(value))

        detected_items = getattr(self.controller, "detected_items", None)
        if isinstance(detected_items, (list, tuple, set)):
            for item in detected_items:
                item_text = str(item or "")
                possible_meat_names.append(item_text)
                parsed_weight = self._extract_number_from_weight_text(item_text)
                if parsed_weight is not None:
                    add_meat(item_text, parsed_weight)

        possible_weights = []
        for attr in (
            "meat_weight", "detected_meat_weight", "current_meat_weight",
            "last_meat_weight", "meat_weight_g", "detected_weight",
            "latest_meat_weight", "selected_meat_weight", "weight_value",
            "temporary_meat_weight_g", "temporary_meat_weight_grams"
        ):
            value = getattr(self.controller, attr, None)
            if value is not None:
                possible_weights.append(value)

        for attr in (
            "temporary_meat_weight_kg", "meat_weight_kg",
            "detected_meat_weight_kg", "current_meat_weight_kg"
        ):
            value = getattr(self.controller, attr, None)
            if value is not None:
                try:
                    possible_weights.append(float(value) * 1000)
                except Exception:
                    pass

        for name in possible_meat_names:
            for weight in possible_weights:
                add_meat(name, weight)

        return meats

    def _estimate_servings_from_meat(self, ingredients):
        saved_meats = self._get_saved_meat_weights()

        if not saved_meats:
            return None

        recipe_meat_type = None
        recipe_meat_text = ""

        for ingredient in ingredients or []:
            detected_type = self._detect_meat_type_from_text(ingredient)
            if detected_type:
                recipe_meat_type = detected_type
                recipe_meat_text = str(ingredient)
                break

        selected = None

        if recipe_meat_type:
            for meat_type, weight_g, source_name in saved_meats:
                if meat_type == recipe_meat_type:
                    selected = (meat_type, weight_g, source_name)
                    break

        if selected is None:
            selected = saved_meats[0]

        meat_type, weight_g, source_name = selected
        grams_per_serving = self._get_grams_per_serving_for_meat(
            meat_type=meat_type,
            recipe_text=recipe_meat_text,
            source_text=source_name
        )

        return self._round_weight_to_servings(weight_g, grams_per_serving)

    def _update_serving_display(self):
        self.serving_value_label.config(text=str(self.current_servings))

    def change_servings(self, delta):
        try:
            delta = int(delta)
        except Exception:
            delta = 0

        max_allowed_servings = getattr(self, "max_servings_from_meat", MAX_SERVINGS)

        try:
            max_allowed_servings = int(max_allowed_servings)
        except Exception:
            max_allowed_servings = MAX_SERVINGS

        max_allowed_servings = max(MIN_SERVINGS, min(MAX_SERVINGS, max_allowed_servings))

        new_value = self.current_servings + delta
        new_value = max(MIN_SERVINGS, min(max_allowed_servings, new_value))

        if new_value == self.current_servings:
            return

        self.current_servings = new_value
        self._update_serving_display()
        self._render_recipe_content(
            self.current_recipe_ingredients,
            self.current_recipe_steps,
            self.current_recipe_link,
            reset_scroll=False
        )

    def _parse_quantity_token(self, token):
        token = str(token or "").strip()

        if not token:
            return None

        token = token.replace("⁄", "/")
        parts = token.split()

        total = Fraction(0, 1)

        try:
            for part in parts:
                part = part.strip()

                if not part:
                    continue

                if part in UNICODE_FRACTIONS:
                    total += UNICODE_FRACTIONS[part]
                elif "/" in part:
                    numerator, denominator = part.split("/", 1)
                    total += Fraction(int(numerator), int(denominator))
                else:
                    total += Fraction(str(float(part))).limit_denominator(100)

            return total

        except Exception:
            return None

    def _format_scaled_quantity(self, quantity):
        if quantity is None:
            return ""

        try:
            q = Fraction(quantity)
        except Exception:
            return str(quantity)

        if q <= 0:
            return "0"

        # Practical cooking fractions only.
        # This avoids awkward values like 1/11 teaspoon.
        practical = [
            Fraction(1, 16),
            Fraction(1, 8),
            Fraction(1, 4),
            Fraction(1, 3),
            Fraction(1, 2),
            Fraction(2, 3),
            Fraction(3, 4),
        ]

        whole = q.numerator // q.denominator
        rem = q - whole

        if rem == 0:
            return str(whole)

        closest = min(practical, key=lambda f: abs(float(rem - f)))

        # If it is very tiny but still needed, show the smallest practical amount.
        if whole == 0 and q < Fraction(1, 16):
            closest = Fraction(1, 16)

        if abs(float(rem - closest)) <= 0.08 or whole == 0:
            rem = closest
        else:
            rem = rem.limit_denominator(8)

        if rem >= 1:
            whole += int(rem)
            rem = rem - int(rem)

        if rem == 0:
            return str(whole)

        frac_text = f"{rem.numerator}/{rem.denominator}"

        if whole <= 0:
            return frac_text

        return f"{whole} {frac_text}"

    def _scale_quantity_text(self, quantity_text, scale_factor):
        quantity = self._parse_quantity_token(quantity_text)

        if quantity is None:
            return quantity_text

        scaled = quantity * Fraction(scale_factor).limit_denominator(100)
        return self._format_scaled_quantity(scaled)

    def _remove_leading_quantity(self, ingredient):
        text = str(ingredient or "").strip()

        if not text:
            return text

        number_pattern = (
            r"(?:\d+(?:\.\d+)?(?:\s+(?:\d+/\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]))?"
            r"|\d+/\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])"
        )

        unit_pattern = (
            r"kg|kilo|kilos|kilogram|kilograms|g|gram|grams|lb|lbs|pound|pounds|"
            r"cups?|tbsp|tablespoons?|tsp|teaspoons?|pieces?|pcs?|pc|cloves?|clove|"
            r"thumbs?|stalks?|heads?|bunches?|bundles?|cans?|packs?|packets?|"
            r"ounces?|oz|ml|liters?|litres?|tablespoon|teaspoon"
        )

        text = re.sub(
            r"^\s*" + number_pattern + r"\s*(?:" + unit_pattern + r")\.?\s*(?:of\s+)?",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"^\s*" + number_pattern + r"\s+",
            "",
            text,
            flags=re.IGNORECASE
        )

        return text.strip(" ,.-")

    def _is_measured_meat_weight_excluded(self, ingredient):
        """Return True for ingredients that contain meat words but are not the main measured meat."""
        text_key = self._normalize_text_key(ingredient)

        for keyword in MEASURED_MEAT_WEIGHT_EXCLUDE_KEYWORDS:
            if re.search(r"\b" + re.escape(keyword) + r"\b", text_key):
                return True

        return False

    def _get_meat_display_weight(self, ingredient):
        meat_type = self._detect_meat_type_from_text(ingredient)

        if not meat_type:
            return None

        if self._is_measured_meat_weight_excluded(ingredient):
            return None

        saved_meats = self._get_saved_meat_weights()

        # Exact meat-type match only. This prevents chicken weight from being
        # placed on beef recipes, pork weight on chicken recipes, etc.
        for saved_type, weight_g, source_name in saved_meats:
            if self._normalize_text_key(saved_type) == self._normalize_text_key(meat_type):
                return self._format_grams(weight_g)

        return None

    def _get_saved_meat_weight_map(self):
        weight_map = {}

        for saved_type, weight_g, source_name in self._get_saved_meat_weights():
            key = self._normalize_text_key(saved_type)

            if key and key not in weight_map:
                weight_map[key] = weight_g

        return weight_map

    def _get_measured_meat_target_indexes(self, ingredients):
        """
        Choose only one main ingredient line per scanned meat type.
        This prevents the same measured weight from being repeated on secondary
        meat-related ingredients such as beef franks, hotdogs, broth, cubes, or stock.
        """
        targets = {}
        weight_map = self._get_saved_meat_weight_map()

        if not weight_map:
            return targets

        for index, ingredient in enumerate(ingredients or []):
            meat_type = self._detect_meat_type_from_text(ingredient)

            if not meat_type:
                continue

            meat_key = self._normalize_text_key(meat_type)

            if meat_key not in weight_map:
                continue

            if self._is_measured_meat_weight_excluded(ingredient):
                continue

            # Apply the measured meat weight only to the first valid main
            # ingredient for each scanned meat type.
            if meat_key not in targets:
                targets[meat_key] = index

        return targets

    def _should_not_scale_ingredient(self, ingredient):
        text_key = self._normalize_text_key(ingredient)
        for keyword in NO_SCALE_INGREDIENT_KEYWORDS:
            if re.search(r"\b" + re.escape(keyword) + r"\b", text_key):
                return True
        return False

    def _convert_oz_to_grams_in_text(self, text):
        text = str(text or "").strip()

        number_pattern = (
            r"(?:\d+(?:\.\d+)?(?:\s+(?:\d+/\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]))?"
            r"|\d+/\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])"
        )

        pattern = (
            r"^(?P<qty>" + number_pattern + r")\s*"
            r"(?P<unit>oz|ounce|ounces)\.?\s+"
            r"(?P<rest>.*)$"
        )

        match = re.match(pattern, text, flags=re.IGNORECASE)

        if not match:
            return text

        qty = self._parse_quantity_token(match.group("qty"))

        if qty is None:
            return text

        grams = float(qty) * 28.3495
        rest = (match.group("rest") or "").strip()

        return f"{self._format_grams(grams)} {rest}".strip()

    def _scale_non_meat_ingredient_text(self, ingredient):
        text = str(ingredient or "").strip()

        if not text:
            return text

        if self._should_not_scale_ingredient(text):
            return text

        try:
            scale_factor = Fraction(int(self.current_servings), int(self.base_servings))
        except Exception:
            scale_factor = Fraction(1, 1)

        if scale_factor <= 0:
            scale_factor = Fraction(1, 1)

        number_pattern = (
            r"(?:\d+(?:\.\d+)?(?:\s+(?:\d+/\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]))?"
            r"|\d+/\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])"
        )

        unit_pattern = (
            r"kg|kilo|kilos|kilogram|kilograms|g|gram|grams|lb|lbs|pound|pounds|"
            r"cups?|tbsp|tablespoons?|tsp|teaspoons?|pieces?|pcs?|pc|cloves?|clove|"
            r"thumbs?|stalks?|heads?|bunches?|bundles?|cans?|packs?|packets?|"
            r"ounces?|oz|ml|liters?|litres?|tablespoon|tablespoons|teaspoon|teaspoons"
        )

        def fix_bay_leaf(unit, rest, qty_text):
            clean_rest = self._normalize_text_key(rest)
            if "bay leaves" in clean_rest or "bay leaf" in clean_rest:
                try:
                    q = int(str(qty_text).split()[0])
                except Exception:
                    q = 1
                return "bay leaf" if q == 1 else "bay leaves"
            return None

        def clean_unit(unit, qty_text, rest=""):
            special = fix_bay_leaf(unit, rest, qty_text)
            if special:
                return ""
            return self._clean_scaled_unit(unit, qty_text)

        def clean_rest_for_special(unit, rest, qty_text):
            special = fix_bay_leaf(unit, rest, qty_text)
            if special:
                # Remove duplicated bay leaf/leaves from rest.
                r = re.sub(r"^bay\s+leaves?\b", "", rest, flags=re.IGNORECASE).strip()
                return f"{special} {r}".strip()
            return rest

        def convert_small_tablespoon(qty_text, unit, rest):
            unit_l = str(unit or "").lower()
            if unit_l not in ("tablespoon", "tablespoons", "tbsp"):
                return qty_text, unit, rest

            qty = self._parse_quantity_token(qty_text)
            if qty is None:
                return qty_text, unit, rest

            # If less than 1 tablespoon, display as teaspoons.
            if qty < 1:
                tsp_qty = qty * 3
                return self._format_scaled_quantity(tsp_qty), "teaspoon", rest

            return qty_text, unit, rest

        # Case 0: Range quantities like "12 to 15 pieces okra sliced".
        range_match = re.match(
            r"^(?P<qty1>" + number_pattern + r")\s*(?:to|-|–)\s*(?P<qty2>" + number_pattern + r")\s*"
            r"(?P<unit>" + unit_pattern + r")\.?\s*(?:of\s+)?(?P<rest>.*)$",
            text,
            flags=re.IGNORECASE
        )

        if range_match:
            qty1 = range_match.group("qty1")
            qty2 = range_match.group("qty2")
            unit = range_match.group("unit")
            rest = (range_match.group("rest") or "").strip()

            scaled_qty1 = self._scale_quantity_for_unit(qty1, scale_factor, f"{unit} {rest}")
            scaled_qty2 = self._scale_quantity_for_unit(qty2, scale_factor, f"{unit} {rest}")
            unit = self._clean_scaled_unit(unit, scaled_qty2)

            if str(scaled_qty1).strip() == str(scaled_qty2).strip():
                return f"{scaled_qty1} {unit} {rest}".strip()

            return f"{scaled_qty1} to {scaled_qty2} {unit} {rest}".strip()

        # Case 1: "400 ml coconut milk", "2 cups water", "5 cloves garlic"
        match = re.match(
            r"^(?P<qty>" + number_pattern + r")\s*(?P<unit>" + unit_pattern + r")\.?\s*(?:of\s+)?(?P<rest>.*)$",
            text,
            flags=re.IGNORECASE
        )

        if match:
            qty = match.group("qty")
            unit = match.group("unit")
            rest = (match.group("rest") or "").strip()
            scaled_qty = self._scale_quantity_for_unit(qty, scale_factor, f"{unit} {rest}")
            scaled_qty, unit, rest = convert_small_tablespoon(scaled_qty, unit, rest)
            unit_clean = clean_unit(unit, scaled_qty, rest)
            rest = clean_rest_for_special(unit, rest, scaled_qty)

            if unit_clean:
                return f"{scaled_qty} {unit_clean} {rest}".strip()
            return f"{scaled_qty} {rest}".strip()

        # Case 2: "1 onion chopped", "2 tomatoes diced"
        count_match = re.match(
            r"^(?P<qty>" + number_pattern + r")\s+(?P<rest>.*)$",
            text,
            flags=re.IGNORECASE
        )

        if count_match:
            qty = count_match.group("qty")
            rest = (count_match.group("rest") or "").strip()
            first_word = self._unit_after_quantity(rest)

            if first_word in COUNT_UNITS:
                scaled_qty = self._scale_quantity_for_unit(qty, scale_factor, rest)
                first_word_clean = self._clean_scaled_unit(first_word, scaled_qty)

                rest_words = rest.split()
                if rest_words:
                    rest_words[0] = first_word_clean
                    rest = " ".join(rest_words)

                return f"{scaled_qty} {rest}".strip()

        return text

    def _scale_ingredient_text(self, ingredient, apply_measured_meat_weight=False):
        ingredient_text = str(ingredient or "").strip()

        if not ingredient_text:
            return ingredient_text

        meat_type = self._detect_meat_type_from_text(ingredient_text)
        meat_weight = self._get_meat_display_weight(ingredient_text) if (meat_type and apply_measured_meat_weight) else None

        if meat_weight:
            clean_name = self._remove_leading_quantity(ingredient_text)
            return f"{meat_weight} {clean_name}".strip()

        # If this is not the selected main meat line, keep its original recipe
        # quantity and scale it normally. This applies to all dishes.
        return self._scale_non_meat_ingredient_text(ingredient_text)

    def _get_scaled_ingredients(self, ingredients):
        target_indexes_by_meat = self._get_measured_meat_target_indexes(ingredients)
        target_indexes = set(target_indexes_by_meat.values())

        return [
            self._scale_ingredient_text(
                ingredient,
                apply_measured_meat_weight=(index in target_indexes)
            )
            for index, ingredient in enumerate(ingredients or [])
        ]

    def _normalize_missing_text(self, value):
        text = str(value or "").lower().replace("_", " ").replace("-", " ")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(
            r"\b\d+(?:\.\d+)?\b|\b\d+\s*/\s*\d+\b|\bkg\b|\bkilo\b|\bkilos\b|\bg\b|\bgrams?\b|\blb\b|\blbs\b|\bpounds?\b|\bcups?\b|\btbsp\b|\btablespoons?\b|\btsp\b|\bteaspoons?\b|\bpieces?\b|\bpcs?\b|\bpc\b|\bcloves?\b|\bthumbs?\b|\bstalks?\b|\bheads?\b|\bbunch\b|\bbundle\b|\bcans?\b|\bpacks?\b",
            " ",
            text,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", text).strip()

    def _get_system_missing_key_from_text(self, value):
        clean = self._normalize_missing_text(value)

        if not clean:
            return None

        for key, keywords in SYSTEM_MISSING_INGREDIENTS.items():
            for keyword in keywords:
                keyword_clean = self._normalize_missing_text(keyword)
                if keyword_clean and (keyword_clean == clean or keyword_clean in clean):
                    return key

        return None

    def _get_detected_system_ingredient_keys(self):
        detected_keys = set()

        detected_items = getattr(self.controller, "detected_items", None)
        detected_item = getattr(self.controller, "detected_item", "")

        possible_items = []

        if isinstance(detected_items, (list, tuple, set)):
            possible_items.extend(detected_items)

        if detected_item:
            possible_items.append(detected_item)

        for item in possible_items:
            key = self._get_system_missing_key_from_text(item)
            if key:
                detected_keys.add(key)

        return detected_keys

    def _get_missing_recipe_ingredients(self, recipe_ingredients):
        detected_keys = self._get_detected_system_ingredient_keys()
        required_keys = []

        for ingredient in recipe_ingredients or []:
            key = self._get_system_missing_key_from_text(ingredient)
            if key and key not in required_keys:
                required_keys.append(key)

        missing_keys = [key for key in required_keys if key not in detected_keys]

        return [
            MISSING_INGREDIENT_DISPLAY.get(key, key.title())
            for key in missing_keys
        ]

    def _format_missing_recipe_ingredients(self, missing_items):
        cleaned = [str(item).strip() for item in missing_items if str(item).strip()]

        if not cleaned:
            return ""

        max_visible = 5
        visible = cleaned[:max_visible]
        text = ", ".join(visible)

        remaining = len(cleaned) - max_visible
        if remaining > 0:
            text += f" +{remaining} more"

        return text

    def _render_missing_ingredients_note(self, original_ingredients):
        missing_items = self._get_missing_recipe_ingredients(original_ingredients)
        missing_text = self._format_missing_recipe_ingredients(missing_items)

        if not missing_text:
            return

        note_outer = tk.Frame(self.scroll_content, bg=SHADOW, padx=1, pady=1)
        note_outer.pack(fill="x", padx=4, pady=(0, 6))

        note = tk.Frame(note_outer, bg=SOFT_SURFACE)
        note.pack(fill="x")

        label = tk.Label(
            note,
            text=f"You are missing these ingredients: {missing_text}",
            font=("Helvetica", 9, "bold"),
            fg=PRIMARY_DARK,
            bg=SOFT_SURFACE,
            anchor="w",
            justify="left",
            wraplength=self._get_safe_ingredient_wrap()
        )
        label.pack(fill="x", padx=8, pady=5)

    def _render_recipe_content(self, ingredients, steps, link, reset_scroll=True):
        self._clear_scroll_content()
        self._render_ingredients(self._get_scaled_ingredients(ingredients), ingredients)
        self._render_steps(steps)
        self._render_link_button(link)

        self.update_idletasks()
        self._refresh_step_wraps()

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        if reset_scroll:
            self.canvas.yview_moveto(0)

    def _render_ingredients(self, ingredients, original_ingredients=None):
        if not ingredients:
            return

        self._render_section_title("Ingredients", f"{len(ingredients)} ITEMS")
        self._render_missing_ingredients_note(original_ingredients or ingredients)
        ingredient_wrap = self._get_safe_ingredient_wrap()

        ingredient_list = tk.Frame(self.scroll_content, bg=CARD_BG)
        ingredient_list.pack(fill="x", pady=(0, 8))

        for ingredient in ingredients:
            item_outer = tk.Frame(ingredient_list, bg=SHADOW, padx=1, pady=1)
            item_outer.pack(fill="x", padx=4, pady=4)

            item = tk.Frame(item_outer, bg=CONTENT_BG)
            item.pack(fill="both", expand=True)

            bullet = tk.Label(
                item,
                text="•",
                font=("Helvetica", 13, "bold"),
                fg=ACCENT_COLOR,
                bg=CONTENT_BG
            )
            bullet.pack(side="left", padx=(8, 5), pady=5)

            label = tk.Label(
                item,
                text=str(ingredient),
                font=("Helvetica", 10),
                fg=TEXT_DARK,
                bg=CONTENT_BG,
                anchor="w",
                justify="left",
                wraplength=ingredient_wrap
            )
            label.pack(side="left", fill="x", expand=True, pady=5, padx=(0, 10))
            self.ingredient_labels.append(label)

    def _render_steps(self, steps):
        self._render_section_title("Steps", f"{len(steps)} STEPS")

        if not steps:
            empty = tk.Label(
                self.scroll_content,
                text="No steps listed.",
                font=("Helvetica", 11),
                fg=TEXT_MUTED,
                bg=CARD_BG,
                anchor="w"
            )
            empty.pack(fill="x", pady=(0, 6))
            return

        step_wrap = self._get_safe_step_wrap()

        for index, step in enumerate(steps, 1):
            step_outer = tk.Frame(self.scroll_content, bg=SHADOW, padx=1, pady=1)
            step_outer.pack(fill="x", pady=5)

            step_card = tk.Frame(step_outer, bg=CONTENT_BG)
            step_card.pack(fill="x")

            step_card.grid_columnconfigure(0, minsize=STEP_NUMBER_BOX_WIDTH + 24, weight=0)
            step_card.grid_columnconfigure(1, weight=1)

            number_cell = tk.Frame(
                step_card,
                bg=CONTENT_BG,
                width=STEP_NUMBER_BOX_WIDTH + 24,
                height=STEP_NUMBER_BOX_HEIGHT
            )
            number_cell.grid(
                row=0,
                column=0,
                sticky="n",
                padx=(8, 4),
                pady=STEP_CARD_PAD_Y
            )
            number_cell.grid_propagate(False)

            self._draw_step_number(number_cell, index)

            step_label = tk.Label(
                step_card,
                text=str(step),
                font=("Helvetica", 11),
                fg=TEXT_DARK,
                bg=CONTENT_BG,
                wraplength=step_wrap,
                justify="left",
                anchor="w"
            )
            step_label.grid(
                row=0,
                column=1,
                sticky="ew",
                padx=(0, 14),
                pady=STEP_CARD_PAD_Y + 5
            )

            self.step_labels.append(step_label)

    # ============================================================
    # DISH SOURCE LINK / QR CODE HELPERS
    # ============================================================

    def _normalize_dish_name_for_url(self, value):
        text = str(value or "").strip().lower()
        text = text.replace("–", "-").replace("—", "-")
        text = text.replace("_", " ")
        text = " ".join(text.split())
        return text

    def get_dish_recipe_url(self, dish_name):
        if not dish_name:
            return ""

        if dish_name in DISH_RECIPE_URLS:
            return DISH_RECIPE_URLS[dish_name]

        normalized_dish = self._normalize_dish_name_for_url(dish_name)

        for key, url in DISH_RECIPE_URLS.items():
            normalized_key = self._normalize_dish_name_for_url(key)
            if normalized_key == normalized_dish:
                return url

        # Fallback for minor punctuation/name differences.
        for key, url in DISH_RECIPE_URLS.items():
            normalized_key = self._normalize_dish_name_for_url(key)
            if normalized_key in normalized_dish or normalized_dish in normalized_key:
                return url

        return ""

    def _resolve_recipe_link(self, dish_name, json_link=""):
        json_link = str(json_link or "").strip()

        if json_link:
            return json_link

        return self.get_dish_recipe_url(dish_name)

    def _make_qr_photo(self, url, size=220):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_image = qr.make_image(
            fill_color="black",
            back_color="white"
        ).convert("RGB")

        if hasattr(Image, "Resampling"):
            resample_filter = Image.Resampling.NEAREST
        else:
            resample_filter = Image.NEAREST

        qr_image = qr_image.resize((size, size), resample_filter)
        return ImageTk.PhotoImage(qr_image)

    def _render_link_button(self, link):
        link = str(link or "").strip()

        source_outer = tk.Frame(self.scroll_content, bg=SHADOW, padx=1, pady=1)
        source_outer.pack(fill="x", pady=(10, 4))

        source_card = tk.Frame(source_outer, bg=CONTENT_BG, padx=12, pady=12)
        source_card.pack(fill="x")

        button = tk.Canvas(
            source_card,
            width=330,
            height=50,
            bg=CONTENT_BG,
            highlightthickness=0,
            cursor="hand2"
        )
        button.pack(anchor="center")

        self._draw_action_button(
            button,
            text="LINK TO THE DISH",
            fill=PRIMARY,
            outline=PRIMARY,
            text_color="#FFFFFF",
            width=330,
            height=50
        )

        button.bind("<Button-1>", lambda event, url=link: self.show_recipe_link_popup(url))

    def show_recipe_link_popup(self, link):
        link = str(link or "").strip()
        has_valid_link = bool(link)

        popup = tk.Toplevel(self)
        popup.title("Recipe QR")
        popup.configure(bg=BG)
        popup.transient(self.winfo_toplevel())

        popup_width = 560
        popup_height = 470

        try:
            root = self.winfo_toplevel()
            root.update_idletasks()
            x = root.winfo_rootx() + max(0, (root.winfo_width() - popup_width) // 2)
            y = root.winfo_rooty() + max(0, (root.winfo_height() - popup_height) // 2)
            popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        except Exception:
            popup.geometry(f"{popup_width}x{popup_height}")

        popup.resizable(False, False)

        outer = tk.Frame(popup, bg=BG, padx=18, pady=18)
        outer.pack(expand=True, fill="both")

        card = tk.Frame(outer, bg=CARD_BG, padx=20, pady=18)
        card.pack(expand=True, fill="both")

        tk.Label(
            card,
            text="Recipe QR",
            font=("Helvetica", 20, "bold"),
            fg=PRIMARY,
            bg=CARD_BG
        ).pack(fill="x")

        qr_holder = tk.Frame(
            card,
            bg=SOFT_SURFACE,
            width=240,
            height=240
        )
        qr_holder.pack(pady=(12, 10))
        qr_holder.pack_propagate(False)

        if has_valid_link:
            try:
                qr_photo = self._make_qr_photo(link, size=220)
                popup.qr_photo = qr_photo

                tk.Label(
                    qr_holder,
                    image=qr_photo,
                    bg=SOFT_SURFACE
                ).pack(expand=True)

            except Exception as error:
                print(f"[DISH] QR generation failed: {error}")

                tk.Label(
                    qr_holder,
                    text="QR failed to load",
                    font=("Helvetica", 13, "bold"),
                    fg=TEXT_MUTED,
                    bg=SOFT_SURFACE
                ).pack(expand=True)
        else:
            tk.Label(
                qr_holder,
                text="No recipe link available",
                font=("Helvetica", 13, "bold"),
                fg=TEXT_MUTED,
                bg=SOFT_SURFACE,
                wraplength=210,
                justify="center"
            ).pack(expand=True)

        link_text = link if has_valid_link else "No recipe link is available for this dish yet."

        tk.Label(
            card,
            text=link_text,
            font=("Helvetica", 10),
            fg=TEXT_DARK,
            bg=CARD_BG,
            wraplength=500,
            justify="center"
        ).pack(fill="x", pady=(0, 12))

        close_btn = tk.Canvas(
            card,
            width=150,
            height=42,
            bg=CARD_BG,
            highlightthickness=0,
            cursor="hand2"
        )
        close_btn.pack()

        self._draw_action_button(
            close_btn,
            text="CLOSE",
            fill=ACCENT_COLOR,
            outline=ACCENT_COLOR,
            text_color="#FFFFFF",
            width=150,
            height=42
        )

        close_btn.bind("<Button-1>", lambda event: popup.destroy())
        popup.bind("<Escape>", lambda event: popup.destroy())

        popup.update_idletasks()

        try:
            popup.grab_set()
        except tk.TclError:
            pass

    def toggle_current_favorite(self):
        dish_name = getattr(self.controller, "selected_dish", None)

        if not dish_name:
            return

        try:
            self.controller.toggle_favorite(dish_name)
            self._draw_favorite_icon(self.controller.is_favorite(dish_name))
        except Exception as error:
            print(f"[DISH] Favorite toggle failed: {error}")

    def _render_missing_dish(self, dish_name):
        display_name = str(dish_name or "Dish not selected")

        self.header_title.config(text=display_name, font=self._get_header_font(display_name))
        self.title_label.config(text=display_name, font=self._get_title_font(display_name))
        self.desc_label.config(text="Dish details were not found in dishes.json.", font=("Helvetica", 9))
        self.recipe_title.config(text="How to Cook")
        self.recipe_subtitle.config(text="No matching dish record was loaded.")
        self._draw_pill(self.region_badge, "UNKNOWN", 140, 38)
        self._render_dish_image(None)

        self._clear_scroll_content()

        empty = tk.Label(
            self.scroll_content,
            text="Please check that the dish name exists in dishes.json.",
            font=("Helvetica", 12),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            anchor="w",
            justify="left",
            wraplength=460
        )
        empty.pack(fill="x", pady=18)

        self._render_link_button("")

        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        dish_name = getattr(self.controller, "selected_dish", None)

        if not dish_name or dish_name not in DISH_DETAILS:
            self._render_missing_dish(dish_name)
            return

        data = DISH_DETAILS[dish_name]

        region = data.get("region", "Unknown")
        description = data.get("description", "")
        ingredients = data.get("ingredients", [])
        steps = data.get("steps", [])
        link = self._resolve_recipe_link(dish_name, data.get("link", ""))

        self.header_title.config(text=dish_name, font=self._get_header_font(dish_name))
        self.title_label.config(text=dish_name, font=self._get_title_font(dish_name))
        self.desc_label.config(text=description, font=self._get_description_font(description))

        self.recipe_title.config(text="How to Cook")

        if ingredients:
            self.recipe_subtitle.config(text=f"{len(ingredients)} ingredients • {len(steps)} steps")
        else:
            self.recipe_subtitle.config(text=f"{len(steps)} steps")

        self._draw_pill(self.region_badge, region, 140, 38)

        image = self._load_fitted_image(
            data.get("image", ""),
            IMAGE_WIDTH,
            IMAGE_HEIGHT,
            region=region
        )
        self._render_dish_image(image)

        if self.active_dish_name != dish_name:
            self.active_dish_name = dish_name

            recipe_base_servings = self._estimate_base_servings_from_recipe_ingredients(ingredients)

            if recipe_base_servings:
                self.base_servings = recipe_base_servings
            else:
                self.base_servings = self._get_base_servings_from_data(data)

            estimated_servings = self._estimate_servings_from_meat(ingredients)

            if estimated_servings:
                self.max_servings_from_meat = estimated_servings
                self.current_servings = estimated_servings
            else:
                self.max_servings_from_meat = MAX_SERVINGS
                self.current_servings = self.base_servings

            self.current_servings = max(
                MIN_SERVINGS,
                min(self.current_servings, self.max_servings_from_meat, MAX_SERVINGS)
            )

        self.current_recipe_ingredients = list(ingredients)
        self.current_recipe_steps = list(steps)
        self.current_recipe_link = link

        self._update_serving_display()
        self._render_recipe_content(ingredients, steps, link, reset_scroll=True)

        self._update_header_wrap()

    def go_back(self):
        from recipe import RecipeScreen
        self.controller.show_frame(RecipeScreen)

    def scan_again(self):
        self.controller.detected_item = None
        self.controller.detected_items = []
        self.controller.captured_frame = None
        self.controller.scan_more = False
        self.controller.scan_mode = "vegetable"
        self.controller.after_result_target = "choice"

        for name, frame in self.controller.frames.items():
            if "ScanScreen" in str(name):
                if hasattr(frame, "reset_screen"):
                    frame.reset_screen()

                self.controller.show_frame(name)
                break

    def _load_done_logo_photo(self, max_width, max_height):
        max_width = max(1, int(max_width))
        max_height = max(1, int(max_height))
        cache_size = (max_width, max_height)

        if self.done_logo_photo is not None and self.done_logo_cache_size == cache_size:
            return self.done_logo_photo

        if self.done_logo_original is None:
            logo_path = self._resolve_image_path(LOGO_PATH)

            if not logo_path or not os.path.exists(logo_path):
                return None

            try:
                self.done_logo_original = Image.open(logo_path).convert("RGBA")
            except Exception:
                self.done_logo_original = None
                return None

        try:
            if hasattr(Image, "Resampling"):
                resample_filter = Image.Resampling.LANCZOS
            else:
                resample_filter = Image.LANCZOS

            logo = ImageOps.contain(
                self.done_logo_original,
                (max_width, max_height),
                method=resample_filter
            )

            self.done_logo_photo = ImageTk.PhotoImage(logo)
            self.done_logo_cache_size = cache_size

            return self.done_logo_photo

        except Exception:
            return None

    def _draw_done_logo(self, canvas, center_x, center_y, max_width, max_height):
        logo_photo = self._load_done_logo_photo(max_width, max_height)

        if not logo_photo:
            return

        canvas.create_image(center_x, center_y, image=logo_photo, anchor="center")

    def done_cooking(self):
        self.stop_scroll()

        if hasattr(self, "done_overlay") and self.done_overlay.winfo_exists():
            return

        self.done_logo_photo = None
        self.done_logo_cache_size = None

        self.done_overlay = tk.Frame(self, bg=BG)
        self.done_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.done_overlay.lift()

        self.done_top_bar = tk.Frame(self.done_overlay, bg=PRIMARY, height=62)
        self.done_top_bar.pack(fill="x", side="top")
        self.done_top_bar.pack_propagate(False)

        self.done_bottom_bar = tk.Frame(self.done_overlay, bg=PRIMARY, height=62)
        self.done_bottom_bar.pack(fill="x", side="bottom")
        self.done_bottom_bar.pack_propagate(False)

        self.done_canvas = tk.Canvas(self.done_overlay, bg=BG, highlightthickness=0)
        self.done_canvas.pack(fill="both", expand=True)

        self.done_canvas.update_idletasks()
        self._animate_done_check(step=0)

    def _animate_done_check(self, step=0):
        if not hasattr(self, "done_canvas") or not self.done_canvas.winfo_exists():
            return

        canvas = self.done_canvas
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width < 50:
            width = self.winfo_width() or 800

        if height < 50:
            height = self.winfo_height() or 480

        left_cx = int(width * 0.31)
        right_cx = int(width * 0.72)

        center_y = height // 2
        animation_cy = height // 2 - 32

        logo_max_width = int(width * 0.34)
        logo_max_height = int(height * 0.62)

        self._draw_done_logo(
            canvas,
            center_x=left_cx,
            center_y=center_y,
            max_width=logo_max_width,
            max_height=logo_max_height
        )

        max_radius = 72
        circle_steps = 14
        check_first_steps = 10
        check_second_steps = 18

        radius = min(
            max_radius,
            int(max_radius * max(1, min(step, circle_steps)) / circle_steps)
        )

        canvas.create_oval(
            right_cx - radius,
            animation_cy - radius,
            right_cx + radius,
            animation_cy + radius,
            fill=SUCCESS,
            outline=PRIMARY,
            width=5
        )

        p1 = (right_cx - 38, animation_cy + 2)
        p2 = (right_cx - 12, animation_cy + 31)
        p3 = (right_cx + 45, animation_cy - 32)

        if step > circle_steps:
            progress = min(1.0, (step - circle_steps) / check_first_steps)
            x = p1[0] + (p2[0] - p1[0]) * progress
            y = p1[1] + (p2[1] - p1[1]) * progress

            canvas.create_line(
                p1[0],
                p1[1],
                x,
                y,
                fill="white",
                width=12,
                capstyle="round",
                joinstyle="round"
            )

        if step > circle_steps + check_first_steps:
            canvas.create_line(
                p1[0],
                p1[1],
                p2[0],
                p2[1],
                fill="white",
                width=12,
                capstyle="round",
                joinstyle="round"
            )

            progress = min(
                1.0,
                (step - circle_steps - check_first_steps) / check_second_steps
            )

            x = p2[0] + (p3[0] - p2[0]) * progress
            y = p2[1] + (p3[1] - p2[1]) * progress

            canvas.create_line(
                p2[0],
                p2[1],
                x,
                y,
                fill="white",
                width=12,
                capstyle="round",
                joinstyle="round"
            )

        if step >= circle_steps + check_first_steps + check_second_steps:
            canvas.create_text(
                right_cx,
                animation_cy + 125,
                text="Done Cooking!",
                fill=PRIMARY,
                font=("Helvetica", 24, "bold")
            )

            canvas.create_text(
                right_cx,
                animation_cy + 160,
                text="Returning to home...",
                fill=TEXT_MUTED,
                font=("Helvetica", 12)
            )

            self.after(950, self.finish_done_cooking)
            return

        self.after(30, lambda: self._animate_done_check(step + 1))

    def finish_done_cooking(self):
        self.controller.detected_item = None
        self.controller.detected_items = []
        self.controller.captured_frame = None
        self.controller.selected_dish = None
        self.controller.scan_more = False
        self.controller.scan_mode = "vegetable"
        self.controller.after_result_target = "choice"
        self.controller.recipe_mode = "region"

        if hasattr(self.controller, "ingredient_weights"):
            self.controller.ingredient_weights = {}

        if hasattr(self.controller, "ingredient_servings"):
            self.controller.ingredient_servings = {}

        self.done_logo_photo = None
        self.done_logo_cache_size = None

        if hasattr(self, "done_overlay") and self.done_overlay.winfo_exists():
            self.done_overlay.destroy()

        from welcome import WelcomeScreen
        self.controller.show_frame(WelcomeScreen)