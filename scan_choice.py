import io
import threading
import tkinter as tk
from pathlib import Path
from urllib.request import Request, urlopen

from scan import ScanScreen

try:
    from PIL import Image, ImageDraw, ImageOps, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except Exception:
    CAIROSVG_AVAILABLE = False


# ==========================================================
# SAME HANAPSANGKAP THEME COLORS
# ==========================================================
ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
CARD_SHADOW = "#D0D5DA"
BUTTON_COLOR = "#1680e4"
MEAT_BUTTON_COLOR = "#FF6B6B"
TEXT_COLOR = "#333333"

PAGE_BG = "#FFFFFF"
PANEL_BG = "#F7FBFD"
PANEL_BORDER = "#DCEAF0"
MUTED_TEXT = "#6B7280"

MEAT_CARD_BG = "#FFF2F2"
MEAT_CARD_BORDER = "#FFD0D0"
MEAT_ACCENT = "#FF9B55"
MEAT_TEXT = "#D84D35"

VEG_CARD_BG = "#F0FAFD"
VEG_CARD_BORDER = "#CFEAF4"
VEG_ACCENT = "#6CCB7F"
VEG_TEXT = "#2F6F3A"

REMOVE_COLOR = "#E35D5B"
REMOVE_HOVER = "#CF4D4B"
REMOVE_BORDER = "#C94C4C"

REMOVE_PANEL_BG = "#FFF6F6"
REMOVE_PANEL_BORDER = "#F3C1C1"
REMOVE_ITEM_BG = "#FFFFFF"
REMOVE_ITEM_HOVER = "#FFE7E7"
REMOVE_X_BG = "#E35D5B"
REMOVE_X_HOVER = "#CF4D4B"

SCROLL_BUTTON_BG = "#E35D5B"
SCROLL_BUTTON_HOVER = "#CF4D4B"


# ==========================================================
# LOCAL ICON PATHS
# Put your uploaded SVG files here:
# icons/meat.svg
# icons/vege.svg
# icons/trash.svg
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent
MEAT_ICON_SOURCE = BASE_DIR / "icons" / "meat.svg"
VEGETABLE_ICON_SOURCE = BASE_DIR / "icons" / "vege.svg"
TRASH_ICON_SOURCE = BASE_DIR / "icons" / "trash.svg"

MEAT_IMAGE_SOURCE = BASE_DIR / "meatimage.jpg"
VEGETABLE_IMAGE_SOURCE = BASE_DIR / "vegeimage.jpg"

class ScanChoiceScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=PAGE_BG)

        self.controller = controller
        self._image_refs = []
        self.remove_list_open = False

        self.remove_scroll_canvas = None
        self.remove_scroll_inner = None
        self.remove_scroll_window = None

        screen_w = max(640, self.winfo_screenwidth())
        screen_h = max(480, self.winfo_screenheight())

        # 7-inch screen support
        self.compact = screen_h <= 900 or screen_w <= 1100

        self.top_bar_height = 48 if self.compact else 64
        self.bottom_bar_height = 14 if self.compact else 24

        self.outer_pad_x = 16 if self.compact else 36
        self.outer_pad_y = 8 if self.compact else 18

        self.panel_pad_x = 16 if self.compact else 36
        self.panel_pad_y = 10 if self.compact else 28

        self.card_width = (
            min(285, max(245, int(screen_w * 0.25)))
            if self.compact
            else min(340, max(285, int(screen_w * 0.28)))
        )
        self.card_height = 235 if self.compact else 320

        self.image_width = self.card_width - 42
        self.image_height = 118 if self.compact else 165

        self.icon_size = 48 if self.compact else 58
        self.wrap_length = min(760, max(340, int(screen_w * 0.68)))

        self.title_size = 18 if self.compact else 22
        self.detected_size = 12 if self.compact else 15
        self.sub_size = 9 if self.compact else 12
        self.card_title_size = 14 if self.compact else 18
        self.remove_size = 14 if self.compact else 16
        self.remove_item_size = 15 if self.compact else 18
        self.close_size = 18 if self.compact else 20

        # Fixed height for remove list so it will not get cut off on 7-inch LCD.
        self.remove_scroll_max_height = 145 if self.compact else 230
        self.remove_row_estimated_height = 54 if self.compact else 64
        self.remove_scroll_increment = 52 if self.compact else 62

        # -------------------- TOP BAR --------------------
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=self.top_bar_height)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        title_wrap = tk.Frame(top_bar, bg=BAR_COLOR)
        title_wrap.pack(expand=True)

        tk.Label(
            title_wrap,
            text="Add Another Ingredient",
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

        # ==========================================================
        # REMOVE AREA RESERVED AT THE BOTTOM
        # ==========================================================
        self.remove_area = tk.Frame(self.panel, bg=PANEL_BG)
        self.remove_area.pack(side="bottom", fill="x", pady=(6, 0))

        self.remove_list_frame = tk.Frame(
            self.remove_area,
            bg=REMOVE_PANEL_BG,
            highlightthickness=2,
            highlightbackground=REMOVE_PANEL_BORDER,
        )

        self.remove_button, self.remove_button_label = self.create_remove_button(
            self.remove_area,
            text="Remove Ingredients",
            command=self.toggle_remove_list,
        )

        # Main content uses the remaining space above the remove area.
        body = tk.Frame(self.panel, bg=PANEL_BG)
        body.pack(side="top", expand=True, fill="both")

        content = tk.Frame(body, bg=PANEL_BG)
        content.pack(anchor="center", expand=True)

        # Small theme badge
        badge = tk.Frame(
            content,
            bg=ACCENT_COLOR,
            width=36 if self.compact else 48,
            height=36 if self.compact else 48,
        )
        badge.pack(pady=(0, 5 if self.compact else 12))
        badge.pack_propagate(False)

        tk.Label(
            badge,
            text="＋",
            font=("Arial", 17 if self.compact else 24, "bold"),
            fg="white",
            bg=ACCENT_COLOR,
        ).pack(expand=True)

        self.detected_label = tk.Label(
            content,
            text="Detected ingredient added.",
            font=("Arial", self.detected_size, "bold"),
            fg=BAR_COLOR,
            bg=PANEL_BG,
            wraplength=self.wrap_length,
            justify="center",
        )
        self.detected_label.pack(pady=(0, 1))

        self.instruction_label = tk.Label(
            content,
            text="Choose whether to scan and weigh meat or scan more vegetables.",
            font=("Arial", self.sub_size),
            fg=MUTED_TEXT,
            bg=PANEL_BG,
            wraplength=self.wrap_length,
            justify="center",
        )
        self.instruction_label.pack(pady=(0, 8 if self.compact else 18))

        choices_row = tk.Frame(content, bg=PANEL_BG)
        choices_row.pack(pady=(0, 0))

        self.meat_widgets = self.create_scan_card(
            choices_row,
            title="Scan & Weigh Meat",
            image_source=MEAT_IMAGE_SOURCE,
            fallback_text="MEAT\nSCAN + WEIGHT",
            icon_source=MEAT_ICON_SOURCE,
            fallback_icon_text="KG",
            card_bg=MEAT_CARD_BG,
            border_color=MEAT_CARD_BORDER,
            accent_color=MEAT_ACCENT,
            title_color=MEAT_TEXT,
            command=self.go_to_meat_scan_and_weight,
            side="left",
        )

        self.vegetable_widgets = self.create_scan_card(
            choices_row,
            title="Scan More Vegetables",
            image_source=VEGETABLE_IMAGE_SOURCE,
            fallback_text="VEGETABLE\nIMAGE",
            icon_source=VEGETABLE_ICON_SOURCE,
            fallback_icon_text="V",
            card_bg=VEG_CARD_BG,
            border_color=VEG_CARD_BORDER,
            accent_color=VEG_ACCENT,
            title_color=VEG_TEXT,
            command=self.scan_more_vegetables,
            side="left",
        )

    # ==========================================================
    # UI BUILDERS
    # ==========================================================
    def create_scan_card(
        self,
        parent,
        title,
        image_source,
        fallback_text,
        icon_source,
        fallback_icon_text,
        card_bg,
        border_color,
        accent_color,
        title_color,
        command,
        side="left",
    ):
        outer = tk.Frame(parent, bg=PANEL_BG)
        outer.pack(
            side=side,
            padx=12 if self.compact else 24,
            pady=(0, 2 if self.compact else 8),
        )

        shadow = tk.Frame(
            outer,
            bg=CARD_SHADOW,
            width=self.card_width,
            height=self.card_height,
        )
        shadow.pack()
        shadow.pack_propagate(False)

        card = tk.Frame(
            shadow,
            bg=card_bg,
            width=self.card_width,
            height=self.card_height,
            highlightthickness=2,
            highlightbackground=border_color,
            cursor="hand2",
        )
        card.pack(fill="both", expand=True, padx=(0, 4), pady=(0, 4))
        card.pack_propagate(False)

        top_spacer = 12 if self.compact else 18
        image_stack_height = self.image_height + (self.icon_size // 2) + 4

        image_stack = tk.Frame(
            card,
            bg=card_bg,
            width=self.card_width,
            height=image_stack_height,
            cursor="hand2",
        )
        image_stack.pack(pady=(top_spacer, 0))
        image_stack.pack_propagate(False)

        visual_canvas = tk.Canvas(
            image_stack,
            width=self.image_width,
            height=image_stack_height,
            bg=card_bg,
            highlightthickness=0,
            cursor="hand2",
        )
        visual_canvas.place(relx=0.5, y=0, anchor="n")

        self.draw_card_visual(
            visual_canvas,
            photo=None,
            fallback_text=fallback_text,
            icon_source=icon_source,
            fallback_icon_text=fallback_icon_text,
            badge_color=accent_color,
            canvas_bg=card_bg,
        )

        title_label = tk.Label(
            card,
            text=title,
            font=("Arial", self.card_title_size, "bold"),
            fg=title_color,
            bg=card_bg,
            cursor="hand2",
        )
        title_label.pack(pady=(2 if self.compact else 6, 0))

        accent_strip = tk.Frame(
            card,
            bg=accent_color,
            height=7 if self.compact else 9,
            cursor="hand2",
        )
        accent_strip.pack(side="bottom", fill="x")

        widgets = {
            "outer": outer,
            "shadow": shadow,
            "card": card,
            "image_stack": image_stack,
            "visual_canvas": visual_canvas,
            "title_label": title_label,
            "accent_strip": accent_strip,
            "normal_bg": card_bg,
            "normal_shadow": CARD_SHADOW,
            "hover_shadow": "#B9C8D1",
            "title_color": title_color,
            "accent_color": accent_color,
            "icon_source": icon_source,
            "fallback_icon_text": fallback_icon_text,
            "fallback_text": fallback_text,
            "command": command,
        }

        self.bind_card_events(widgets)

        self.load_card_image(
            visual_canvas,
            image_source,
            self.image_width,
            self.image_height,
            fallback_text,
            icon_source,
            fallback_icon_text,
            accent_color,
            card_bg,
        )

        return widgets

    def create_remove_button(self, parent, text, command):
        wrapper = tk.Frame(parent, bg=PANEL_BG)
        wrapper.pack(side="bottom", pady=(5, 0))

        button = tk.Frame(
            wrapper,
            bg=REMOVE_COLOR,
            width=380 if self.compact else 450,
            height=48 if self.compact else 58,
            cursor="hand2",
            highlightthickness=2,
            highlightbackground=REMOVE_BORDER,
            relief="raised",
            bd=3,
        )
        button.pack()
        button.pack_propagate(False)

        inner = tk.Frame(button, bg=REMOVE_COLOR, cursor="hand2")
        inner.pack(expand=True)

        trash_canvas = tk.Canvas(
            inner,
            width=30,
            height=30,
            bg=REMOVE_COLOR,
            highlightthickness=0,
            cursor="hand2",
        )
        trash_canvas.pack(side="left", padx=(0, 10))

        self.draw_plain_icon(
            trash_canvas,
            icon_source=TRASH_ICON_SOURCE,
            fallback_text="X",
            icon_color="#FFFFFF",
            size=24,
        )

        label = tk.Label(
            inner,
            text=text,
            font=("Arial", self.remove_size, "bold"),
            fg="white",
            bg=REMOVE_COLOR,
            cursor="hand2",
        )
        label.pack(side="left")

        def redraw_trash(bg_color):
            trash_canvas.config(bg=bg_color)
            trash_canvas.delete("all")
            self.draw_plain_icon(
                trash_canvas,
                icon_source=TRASH_ICON_SOURCE,
                fallback_text="X",
                icon_color="#FFFFFF",
                size=24,
            )

        def on_enter(event=None):
            button.config(bg=REMOVE_HOVER)
            inner.config(bg=REMOVE_HOVER)
            label.config(bg=REMOVE_HOVER)
            redraw_trash(REMOVE_HOVER)

        def on_leave(event=None):
            button.config(bg=REMOVE_COLOR)
            inner.config(bg=REMOVE_COLOR)
            label.config(bg=REMOVE_COLOR)
            redraw_trash(REMOVE_COLOR)

        for widget in (button, inner, label, trash_canvas):
            widget.bind("<Button-1>", lambda e: command())
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        return button, label

    def create_remove_scroll_button(self, parent, text, command):
        button = tk.Frame(
            parent,
            bg=SCROLL_BUTTON_BG,
            width=48 if self.compact else 56,
            height=48 if self.compact else 58,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=REMOVE_BORDER,
            relief="raised",
            bd=2,
        )
        button.pack(fill="x", expand=True, pady=2)
        button.pack_propagate(False)

        label = tk.Label(
            button,
            text=text,
            font=("Arial", 18 if self.compact else 22, "bold"),
            fg="white",
            bg=SCROLL_BUTTON_BG,
            cursor="hand2",
        )
        label.pack(expand=True)

        def on_enter(event=None):
            button.config(bg=SCROLL_BUTTON_HOVER)
            label.config(bg=SCROLL_BUTTON_HOVER)

        def on_leave(event=None):
            button.config(bg=SCROLL_BUTTON_BG)
            label.config(bg=SCROLL_BUTTON_BG)

        for widget in (button, label):
            widget.bind("<Button-1>", lambda e: command())
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        return button

    # ==========================================================
    # CARD IMAGE + ICON DRAWING
    # ==========================================================
    def draw_card_visual(
        self,
        canvas,
        photo,
        fallback_text,
        icon_source,
        fallback_icon_text,
        badge_color,
        canvas_bg,
    ):
        canvas.delete("all")
        canvas.config(bg=canvas_bg)

        if photo:
            canvas.create_image(
                0,
                0,
                image=photo,
                anchor="nw",
                tags=("dish_image",)
            )
            canvas.image = photo
        else:
            canvas.image = None
            canvas.create_rectangle(
                0,
                0,
                self.image_width,
                self.image_height,
                fill="#EAF4F8",
                outline="#EAF4F8",
                tags=("dish_image",)
            )
            canvas.create_text(
                self.image_width // 2,
                self.image_height // 2,
                text=fallback_text,
                fill=BAR_COLOR,
                font=("Arial", 11 if self.compact else 15, "bold"),
                justify="center",
                tags=("dish_image",)
            )

        badge_center_x = self.image_width // 2
        badge_center_y = self.image_height

        self.draw_icon_badge_on_canvas(
            canvas,
            center_x=badge_center_x,
            center_y=badge_center_y,
            icon_source=icon_source,
            fallback_text=fallback_icon_text,
            badge_color=badge_color,
            icon_color="#FFFFFF",
        )

    def draw_icon_badge_on_canvas(
        self,
        canvas,
        center_x,
        center_y,
        icon_source,
        fallback_text,
        badge_color,
        icon_color="#FFFFFF",
    ):
        radius = self.icon_size // 2

        canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill="#FFFFFF",
            outline="#FFFFFF",
            width=1,
            tags=("icon_badge",)
        )

        inner_pad = 6
        canvas.create_oval(
            center_x - radius + inner_pad,
            center_y - radius + inner_pad,
            center_x + radius - inner_pad,
            center_y + radius - inner_pad,
            fill=badge_color,
            outline="#FFFFFF",
            width=3,
            tags=("icon_badge",)
        )

        icon_img = self.load_icon_image(
            icon_source,
            size=26 if self.compact else 32,
            color=icon_color,
        )

        if icon_img:
            photo = ImageTk.PhotoImage(icon_img)
            self._image_refs.append(photo)
            canvas.badge_image = photo

            canvas.create_image(
                center_x,
                center_y,
                image=photo,
                tags=("icon_badge",)
            )
        else:
            canvas.create_text(
                center_x,
                center_y,
                text=fallback_text,
                fill=icon_color,
                font=("Arial", 13 if self.compact else 16, "bold"),
                tags=("icon_badge",)
            )

    def draw_plain_icon(self, canvas, icon_source, fallback_text, icon_color="#FFFFFF", size=24):
        icon_img = self.load_icon_image(
            icon_source,
            size=size,
            color=icon_color,
        )

        if icon_img:
            photo = ImageTk.PhotoImage(icon_img)
            self._image_refs.append(photo)
            canvas.create_image(15, 15, image=photo)
            canvas.image = photo
        else:
            canvas.create_text(
                15,
                15,
                text=fallback_text,
                fill=icon_color,
                font=("Arial", 15, "bold"),
            )

    def load_icon_image(self, source, size=28, color="#FFFFFF"):
        if not PIL_AVAILABLE:
            return None

        try:
            source = Path(source)

            if not source.exists():
                return None

            if source.suffix.lower() == ".svg":
                if not CAIROSVG_AVAILABLE:
                    return None

                svg_text = source.read_text(encoding="utf-8")
                svg_text = svg_text.replace("currentColor", color)

                png_data = cairosvg.svg2png(
                    bytestring=svg_text.encode("utf-8"),
                    output_width=size,
                    output_height=size,
                )

                image = Image.open(io.BytesIO(png_data)).convert("RGBA")
                return image

            image = Image.open(source).convert("RGBA")

            if hasattr(Image, "Resampling"):
                resample_filter = Image.Resampling.LANCZOS
            else:
                resample_filter = Image.LANCZOS

            image = ImageOps.contain(image, (size, size), method=resample_filter)
            return image

        except Exception:
            return None

    def bind_card_events(self, widgets):
        def on_enter(event=None):
            widgets["shadow"].config(bg=widgets["hover_shadow"])
            widgets["card"].config(bg="#FFFFFF")
            widgets["image_stack"].config(bg="#FFFFFF")
            widgets["visual_canvas"].config(bg="#FFFFFF")
            widgets["title_label"].config(bg="#FFFFFF")

        def on_leave(event=None):
            widgets["shadow"].config(bg=widgets["normal_shadow"])
            widgets["card"].config(bg=widgets["normal_bg"])
            widgets["image_stack"].config(bg=widgets["normal_bg"])
            widgets["visual_canvas"].config(bg=widgets["normal_bg"])
            widgets["title_label"].config(bg=widgets["normal_bg"])

        def on_click(event=None):
            widgets["command"]()

        for widget in (
            widgets["card"],
            widgets["image_stack"],
            widgets["visual_canvas"],
            widgets["title_label"],
            widgets["accent_strip"],
        ):
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    # ==========================================================
    # REMOVE INGREDIENTS PANEL
    # ==========================================================
    def toggle_remove_list(self):
        if self.remove_list_open:
            self.hide_remove_list()
        else:
            self.show_remove_list()

    def show_remove_list(self):
        self.build_remove_list()

        if not self.remove_list_open:
            self.remove_list_frame.pack(
                side="top",
                fill="x",
                padx=0,
                pady=(0, 6),
            )
            self.remove_list_open = True

    def hide_remove_list(self):
        if self.remove_list_open:
            self.remove_list_frame.pack_forget()
            self.remove_list_open = False

    def build_remove_list(self):
        for widget in self.remove_list_frame.winfo_children():
            widget.destroy()

        self.remove_scroll_canvas = None
        self.remove_scroll_inner = None
        self.remove_scroll_window = None

        items = getattr(self.controller, "detected_items", []) or []

        header_row = tk.Frame(self.remove_list_frame, bg=REMOVE_PANEL_BG)
        header_row.pack(fill="x", padx=10, pady=(6, 4))

        tk.Label(
            header_row,
            text="Tap an ingredient to remove:",
            font=("Arial", 13 if self.compact else 15, "bold"),
            fg=TEXT_COLOR,
            bg=REMOVE_PANEL_BG,
        ).pack(side="left")

        close_box = tk.Frame(
            header_row,
            bg=REMOVE_X_BG,
            width=40 if self.compact else 44,
            height=36 if self.compact else 40,
            cursor="hand2",
            relief="raised",
            bd=2,
        )
        close_box.pack(side="right")
        close_box.pack_propagate(False)

        close_label = tk.Label(
            close_box,
            text="X",
            font=("Arial", self.close_size, "bold"),
            fg="white",
            bg=REMOVE_X_BG,
            cursor="hand2",
        )
        close_label.pack(expand=True)

        def close_enter(event=None):
            close_box.config(bg=REMOVE_X_HOVER)
            close_label.config(bg=REMOVE_X_HOVER)

        def close_leave(event=None):
            close_box.config(bg=REMOVE_X_BG)
            close_label.config(bg=REMOVE_X_BG)

        for widget in (close_box, close_label):
            widget.bind("<Button-1>", lambda e: self.hide_remove_list())
            widget.bind("<Enter>", close_enter)
            widget.bind("<Leave>", close_leave)

        if not items:
            tk.Label(
                self.remove_list_frame,
                text="No ingredients added yet.",
                font=("Arial", 13 if self.compact else 15, "bold"),
                fg=MUTED_TEXT,
                bg=REMOVE_PANEL_BG,
            ).pack(anchor="w", padx=12, pady=(2, 10))
            return

        list_height = min(
            self.remove_scroll_max_height,
            max(
                self.remove_row_estimated_height,
                len(items) * self.remove_row_estimated_height,
            ),
        )

        list_area = tk.Frame(self.remove_list_frame, bg=REMOVE_PANEL_BG)
        list_area.pack(fill="x", padx=10, pady=(0, 8))

        scroll_shell = tk.Frame(
            list_area,
            bg=REMOVE_PANEL_BG,
            height=list_height,
        )
        scroll_shell.pack(side="left", fill="x", expand=True)
        scroll_shell.pack_propagate(False)

        self.remove_scroll_canvas = tk.Canvas(
            scroll_shell,
            bg=REMOVE_PANEL_BG,
            highlightthickness=0,
            height=list_height,
            yscrollincrement=self.remove_scroll_increment,
        )
        self.remove_scroll_canvas.pack(side="left", fill="both", expand=True)

        self.remove_scroll_inner = tk.Frame(
            self.remove_scroll_canvas,
            bg=REMOVE_PANEL_BG,
        )

        self.remove_scroll_window = self.remove_scroll_canvas.create_window(
            (0, 0),
            window=self.remove_scroll_inner,
            anchor="nw",
        )

        self.remove_scroll_inner.bind(
            "<Configure>",
            lambda e: self.update_remove_scroll_region(),
        )
        self.remove_scroll_canvas.bind(
            "<Configure>",
            self.resize_remove_scroll_window,
        )

        # Mouse wheel still works if you test on PC, but LCD users can tap the buttons.
        self.remove_scroll_canvas.bind("<MouseWheel>", self.on_remove_mousewheel)
        self.remove_scroll_inner.bind("<MouseWheel>", self.on_remove_mousewheel)
        self.remove_scroll_canvas.bind("<Button-4>", self.on_remove_mousewheel)
        self.remove_scroll_canvas.bind("<Button-5>", self.on_remove_mousewheel)

        for index, item in enumerate(items):
            row = self.create_remove_item_row(
                self.remove_scroll_inner,
                item_text=self.format_ingredient_display(item),
                item_index=index,
            )

            row.bind("<MouseWheel>", self.on_remove_mousewheel)
            row.bind("<Button-4>", self.on_remove_mousewheel)
            row.bind("<Button-5>", self.on_remove_mousewheel)

        needs_scroll_buttons = len(items) * self.remove_row_estimated_height > list_height

        if needs_scroll_buttons:
            controls = tk.Frame(
                list_area,
                bg=REMOVE_PANEL_BG,
                width=52 if self.compact else 60,
                height=list_height,
            )
            controls.pack(side="right", fill="y", padx=(8, 0))
            controls.pack_propagate(False)

            self.create_remove_scroll_button(
                controls,
                text="▲",
                command=lambda: self.scroll_remove_list(-1),
            )

            self.create_remove_scroll_button(
                controls,
                text="▼",
                command=lambda: self.scroll_remove_list(1),
            )

        self.after(50, self.update_remove_scroll_region)

    def resize_remove_scroll_window(self, event=None):
        if self.remove_scroll_canvas and self.remove_scroll_window:
            self.remove_scroll_canvas.itemconfig(
                self.remove_scroll_window,
                width=event.width,
            )

    def update_remove_scroll_region(self):
        if self.remove_scroll_canvas:
            self.remove_scroll_canvas.configure(
                scrollregion=self.remove_scroll_canvas.bbox("all")
            )

    def scroll_remove_list(self, direction):
        if self.remove_scroll_canvas:
            self.remove_scroll_canvas.yview_scroll(direction, "units")

    def on_remove_mousewheel(self, event):
        if not self.remove_scroll_canvas:
            return

        if hasattr(event, "num") and event.num == 4:
            self.scroll_remove_list(-1)
        elif hasattr(event, "num") and event.num == 5:
            self.scroll_remove_list(1)
        elif hasattr(event, "delta"):
            if event.delta > 0:
                self.scroll_remove_list(-1)
            elif event.delta < 0:
                self.scroll_remove_list(1)

    def create_remove_item_row(self, parent, item_text, item_index):
        row = tk.Frame(
            parent,
            bg=REMOVE_ITEM_BG,
            highlightthickness=1,
            highlightbackground=REMOVE_PANEL_BORDER,
            cursor="hand2",
        )
        row.pack(fill="x", pady=4)

        x_label = tk.Label(
            row,
            text="[X]",
            font=("Arial", self.remove_item_size, "bold"),
            fg=REMOVE_COLOR,
            bg=REMOVE_ITEM_BG,
            width=5,
            cursor="hand2",
        )
        x_label.pack(side="left", padx=(10, 4), pady=8)

        name_label = tk.Label(
            row,
            text=item_text.upper(),
            font=("Arial", self.remove_item_size, "bold"),
            fg=TEXT_COLOR,
            bg=REMOVE_ITEM_BG,
            anchor="w",
            cursor="hand2",
            justify="left",
            wraplength=420 if self.compact else 680,
        )
        name_label.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)

        def on_enter(event=None):
            row.config(bg=REMOVE_ITEM_HOVER)
            x_label.config(bg=REMOVE_ITEM_HOVER)
            name_label.config(bg=REMOVE_ITEM_HOVER)

        def on_leave(event=None):
            row.config(bg=REMOVE_ITEM_BG)
            x_label.config(bg=REMOVE_ITEM_BG)
            name_label.config(bg=REMOVE_ITEM_BG)

        def on_click(event=None):
            self.remove_ingredient_by_index(item_index)

        for widget in (row, x_label, name_label):
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<MouseWheel>", self.on_remove_mousewheel)
            widget.bind("<Button-4>", self.on_remove_mousewheel)
            widget.bind("<Button-5>", self.on_remove_mousewheel)

        return row

    def remove_ingredient_by_index(self, item_index):
        items = getattr(self.controller, "detected_items", None)

        if not isinstance(items, list):
            self.instruction_label.config(text="No ingredient list found.")
            self.hide_remove_list()
            return

        if not (0 <= item_index < len(items)):
            self.instruction_label.config(text="Ingredient not found.")
            self.build_remove_list()
            return

        removed_item = items.pop(item_index)

        self.remove_saved_weight_for_item(removed_item)
        self.refresh_detected_label()
        self.instruction_label.config(text=f"Removed: {removed_item}")

        if items:
            self.build_remove_list()
        else:
            self.hide_remove_list()

    def remove_saved_weight_for_item(self, item):
        item_key = str(item).strip().lower()

        ingredient_weights = getattr(self.controller, "ingredient_weights", None)

        if isinstance(ingredient_weights, dict):
            for key in list(ingredient_weights.keys()):
                if str(key).strip().lower() == item_key:
                    del ingredient_weights[key]

        ingredient_servings = getattr(self.controller, "ingredient_servings", None)

        if isinstance(ingredient_servings, dict):
            for key in list(ingredient_servings.keys()):
                if str(key).strip().lower() == item_key:
                    del ingredient_servings[key]

    # ==========================================================
    # IMAGE HANDLING
    # ==========================================================
    def load_card_image(
        self,
        canvas,
        source,
        width,
        height,
        fallback_text,
        icon_source,
        fallback_icon_text,
        badge_color,
        card_bg,
    ):
        self.draw_card_visual(
            canvas,
            photo=None,
            fallback_text="Loading image...",
            icon_source=icon_source,
            fallback_icon_text=fallback_icon_text,
            badge_color=badge_color,
            canvas_bg=card_bg,
        )

        if not PIL_AVAILABLE:
            self.draw_card_visual(
                canvas,
                photo=None,
                fallback_text=fallback_text,
                icon_source=icon_source,
                fallback_icon_text=fallback_icon_text,
                badge_color=badge_color,
                canvas_bg=card_bg,
            )
            return

        def worker():
            try:
                pil_image = self.read_image_source(
                    source,
                    width,
                    height,
                    radius=18 if self.compact else 24,
                )
                self.after(
                    0,
                    lambda: self.apply_card_image(
                        canvas,
                        pil_image,
                        fallback_text,
                        icon_source,
                        fallback_icon_text,
                        badge_color,
                        card_bg,
                    )
                )
            except Exception:
                self.after(
                    0,
                    lambda: self.draw_card_visual(
                        canvas,
                        photo=None,
                        fallback_text=fallback_text,
                        icon_source=icon_source,
                        fallback_icon_text=fallback_icon_text,
                        badge_color=badge_color,
                        canvas_bg=card_bg,
                    )
                )

        threading.Thread(target=worker, daemon=True).start()

    def read_image_source(self, source, width, height, radius=20):
        source_text = str(source)

        if source_text.lower().startswith(("http://", "https://")):
            request = Request(
                source_text,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urlopen(request, timeout=8) as response:
                data = response.read()
            image = Image.open(io.BytesIO(data)).convert("RGBA")
        else:
            image = Image.open(Path(source)).convert("RGBA")

        if hasattr(Image, "Resampling"):
            resample_filter = Image.Resampling.LANCZOS
        else:
            resample_filter = Image.LANCZOS

        image = ImageOps.fit(image, (width, height), method=resample_filter)

        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
        image.putalpha(mask)
        return image

    def apply_card_image(
        self,
        canvas,
        pil_image,
        fallback_text,
        icon_source,
        fallback_icon_text,
        badge_color,
        card_bg,
    ):
        try:
            photo = ImageTk.PhotoImage(pil_image)
            self._image_refs.append(photo)

            self.draw_card_visual(
                canvas,
                photo=photo,
                fallback_text=fallback_text,
                icon_source=icon_source,
                fallback_icon_text=fallback_icon_text,
                badge_color=badge_color,
                canvas_bg=card_bg,
            )

            canvas.image = photo

        except Exception:
            self.draw_card_visual(
                canvas,
                photo=None,
                fallback_text=fallback_text,
                icon_source=icon_source,
                fallback_icon_text=fallback_icon_text,
                badge_color=badge_color,
                canvas_bg=card_bg,
            )

    # ==========================================================
    # APP FUNCTIONS
    # ==========================================================
    def go_to_meat_scan_and_weight(self):
        self.controller.scan_mode = "meat"
        self.controller.scan_more = True
        self.controller.after_result_target = "recipe"

        if not hasattr(self.controller, "ingredient_weights") or not isinstance(
            getattr(self.controller, "ingredient_weights", None), dict
        ):
            self.controller.ingredient_weights = {}

        scan_frame = self.controller.frames.get(ScanScreen)

        if scan_frame and hasattr(scan_frame, "reset_screen"):
            scan_frame.reset_screen()

        self.controller.show_frame(ScanScreen)

    def _go_to_scan(self):
        scan_frame = self.controller.frames.get(ScanScreen)

        if scan_frame and hasattr(scan_frame, "reset_screen"):
            scan_frame.reset_screen()

        self.controller.show_frame(ScanScreen)

    def scan_more_vegetables(self):
        self.controller.scan_mode = "vegetable"
        self.controller.scan_more = True
        self.controller.after_result_target = "recipe"
        self._go_to_scan()

    def format_ingredient_display(self, item):
        item_text = str(item)
        key = item_text.strip().lower()

        ingredient_weights = getattr(self.controller, "ingredient_weights", None)
        ingredient_servings = getattr(self.controller, "ingredient_servings", None)

        weight = None
        servings = None

        if isinstance(ingredient_weights, dict):
            weight = ingredient_weights.get(key)

        if isinstance(ingredient_servings, dict):
            serving_data = ingredient_servings.get(key)

            if isinstance(serving_data, dict):
                servings = serving_data.get("estimated_servings")
            elif serving_data:
                servings = serving_data

        if weight and servings:
            serving_word = "serving" if int(servings) == 1 else "servings"
            return f"{item_text} ({weight}g, {servings} {serving_word})"

        if weight:
            return f"{item_text} ({weight}g)"

        return item_text

    def refresh_detected_label(self):
        items = getattr(self.controller, "detected_items", []) or []

        if items:
            display_items = [self.format_ingredient_display(item) for item in items]
            self.detected_label.config(
                text=f"Added: {', '.join(str(item) for item in display_items)}"
            )
        else:
            self.detected_label.config(text="Detected ingredient added.")

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        self.refresh_detected_label()
        self.instruction_label.config(
            text="Choose whether to scan and weigh meat or scan more vegetables."
        )
        self.hide_remove_list()