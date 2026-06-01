# result.py
import tkinter as tk
import cv2
from PIL import Image, ImageTk, ImageDraw

from recipe import RecipeScreen
from scan_choice import ScanChoiceScreen


ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"

PAGE_BG = "#FFFFFF"
PANEL_BG = "#F7FBFD"
PANEL_BORDER = "#DCEAF0"
TEXT_COLOR = "#263238"
MUTED_TEXT = "#6B7280"

SUCCESS_COLOR = "#27AE60"
SUCCESS_BG = "#EEFFF4"
SUCCESS_BORDER = "#BFEBCF"

WARNING_COLOR = "#E67E22"

BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 10


class ResultScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=PAGE_BG)
        self.controller = controller

        self.redirect_after_id = None

        self.setup_ui()

    # ==========================================================
    # UI HELPERS
    # ==========================================================
    def crop_to_fill(self, img_pil, target_w, target_h):
        img_w, img_h = img_pil.size

        if img_w <= 0 or img_h <= 0 or target_w <= 0 or target_h <= 0:
            return img_pil

        scale = max(target_w / img_w, target_h / img_h)
        resized_w = max(1, int(img_w * scale))
        resized_h = max(1, int(img_h * scale))

        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS

        resized = img_pil.resize((resized_w, resized_h), resample)

        left = max(0, (resized_w - target_w) // 2)
        top = max(0, (resized_h - target_h) // 2)
        right = left + target_w
        bottom = top + target_h

        return resized.crop((left, top, right, bottom))

    def make_rounded_image(self, img_pil, radius=18):
        width, height = img_pil.size

        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)

        rounded_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        rounded_img.paste(img_pil.convert("RGBA"), (0, 0), mask=mask)

        return rounded_img

    def draw_success_icon(self):
        self.success_icon.delete("all")

        size = 42 if self.compact else 48
        self.success_icon.config(width=size, height=size)

        self.success_icon.create_oval(
            4,
            4,
            size - 4,
            size - 4,
            fill=SUCCESS_COLOR,
            outline="white",
            width=3,
        )

        self.success_icon.create_line(
            size * 0.28,
            size * 0.52,
            size * 0.43,
            size * 0.67,
            fill="white",
            width=4,
            capstyle="round",
        )

        self.success_icon.create_line(
            size * 0.43,
            size * 0.67,
            size * 0.74,
            size * 0.32,
            fill="white",
            width=4,
            capstyle="round",
        )

    # ==========================================================
    # UI SETUP
    # ==========================================================
    def setup_ui(self):
        screen_w = max(640, self.winfo_screenwidth())
        screen_h = max(480, self.winfo_screenheight())

        self.compact = screen_h <= 900 or screen_w <= 1100

        self.sidebar_width = 300 if self.compact else 350
        self.title_font = ("Arial", 20 if self.compact else 24, "bold")
        self.section_font = ("Arial", 12 if self.compact else 15, "bold")
        self.big_result_font = ("Arial", 18 if self.compact else 22, "bold")
        self.small_font = ("Arial", 8 if self.compact else 10)

        # -------------------- TOP BAR --------------------
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=BAR_HEIGHT)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        tk.Label(
            top_bar,
            text="Scan Result",
            font=self.title_font,
            fg="white",
            bg=BAR_COLOR,
        ).pack(expand=True)

        # -------------------- BOTTOM BAR --------------------
        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=BOTTOM_BAR_HEIGHT)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        # -------------------- MAIN AREA --------------------
        center_frame = tk.Frame(self, bg=PAGE_BG)
        center_frame.pack(expand=True, fill="both", padx=12, pady=7)

        main_panel = tk.Frame(
            center_frame,
            bg=PANEL_BG,
            highlightthickness=2,
            highlightbackground=PANEL_BORDER,
        )
        main_panel.pack(expand=True, fill="both")

        main_panel.grid_rowconfigure(0, weight=1)
        main_panel.grid_columnconfigure(0, weight=1)
        main_panel.grid_columnconfigure(1, weight=0)

        # -------------------- LEFT IMAGE AREA --------------------
        left_panel = tk.Frame(main_panel, bg=PANEL_BG)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=10)

        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        image_header = tk.Frame(left_panel, bg=PANEL_BG)
        image_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        image_header.grid_columnconfigure(0, weight=1)

        tk.Label(
            image_header,
            text="Captured Ingredient",
            font=("Arial", 14 if self.compact else 18, "bold"),
            fg=TEXT_COLOR,
            bg=PANEL_BG,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.image_status_label = tk.Label(
            image_header,
            text="Image captured",
            font=("Arial", 8 if self.compact else 10, "bold"),
            fg=BAR_COLOR,
            bg="#E7F5FA",
            padx=9,
            pady=3,
        )
        self.image_status_label.grid(row=0, column=1, sticky="e")

        self.img_outer = tk.Frame(
            left_panel,
            bg=BAR_COLOR,
            highlightthickness=0,
        )
        self.img_outer.grid(row=1, column=0, sticky="nsew")

        self.img_container = tk.Frame(
            self.img_outer,
            bg="#050B12",
        )
        self.img_container.pack(expand=True, fill="both", padx=4, pady=4)

        self.img_label = tk.Label(
            self.img_container,
            bg="#050B12",
            fg="#9CA3AF",
            font=("Arial", 14 if self.compact else 16, "bold"),
            text="No image captured",
        )
        self.img_label.pack(expand=True, fill="both")

        self.image_footer = tk.Frame(left_panel, bg=PANEL_BG)
        self.image_footer.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        self.image_footer.grid_columnconfigure(0, weight=1)

        self.footer_lbl = tk.Label(
            self.image_footer,
            text="Reviewing captured ingredient...",
            font=("Arial", 8 if self.compact else 11),
            fg=MUTED_TEXT,
            bg=PANEL_BG,
            anchor="w",
        )
        self.footer_lbl.grid(row=0, column=0, sticky="w")

        # -------------------- RIGHT DASHBOARD --------------------
        right_panel = tk.Frame(main_panel, bg=PANEL_BG, width=self.sidebar_width)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=(0, 10))
        right_panel.grid_propagate(False)

        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=0)
        right_panel.grid_rowconfigure(1, weight=1)

        # -------------------- SUCCESS CARD --------------------
        self.status_card = tk.Frame(
            right_panel,
            bg=CARD_BG,
            padx=12,
            pady=10,
            height=110 if self.compact else 125,
        )
        self.status_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.status_card.grid_propagate(False)

        self.status_card.grid_columnconfigure(0, weight=0)
        self.status_card.grid_columnconfigure(1, weight=1)

        self.success_icon = tk.Canvas(
            self.status_card,
            width=42,
            height=42,
            bg=CARD_BG,
            highlightthickness=0,
        )
        self.success_icon.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 10), pady=(0, 0))
        self.draw_success_icon()

        self.status_title_lbl = tk.Label(
            self.status_card,
            text="Scan Completed",
            font=("Arial", 12 if self.compact else 15, "bold"),
            fg=TEXT_COLOR,
            bg=CARD_BG,
            anchor="w",
        )
        self.status_title_lbl.grid(row=0, column=1, sticky="ew")

        self.status_sub_lbl = tk.Label(
            self.status_card,
            text="Ingredient successfully recognized.",
            font=self.small_font,
            fg=MUTED_TEXT,
            bg=CARD_BG,
            anchor="w",
            justify="left",
            wraplength=self.sidebar_width - 76,
        )
        self.status_sub_lbl.grid(row=1, column=1, sticky="ew", pady=(4, 0))

        # Compatibility
        self.status_lbl = self.status_title_lbl

        # -------------------- INGREDIENT CARD --------------------
        self.ingredient_card = tk.Frame(
            right_panel,
            bg=CARD_BG,
            padx=12,
            pady=10,
        )
        self.ingredient_card.grid(row=1, column=0, sticky="nsew")
        self.ingredient_card.grid_propagate(False)

        self.ingredient_card.grid_columnconfigure(0, weight=1)
        self.ingredient_card.grid_rowconfigure(0, weight=0)
        self.ingredient_card.grid_rowconfigure(1, weight=0)
        self.ingredient_card.grid_rowconfigure(2, weight=0)
        self.ingredient_card.grid_rowconfigure(3, weight=1)

        tk.Label(
            self.ingredient_card,
            text="Detected Ingredient",
            font=("Arial", 12 if self.compact else 15, "bold"),
            fg=BAR_COLOR,
            bg=CARD_BG,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        divider = tk.Frame(self.ingredient_card, bg=PANEL_BORDER, height=2)
        divider.grid(row=1, column=0, sticky="ew", pady=(6, 8))

        self.result_count_lbl = tk.Label(
            self.ingredient_card,
            text="1 item detected",
            font=self.small_font,
            fg=MUTED_TEXT,
            bg=CARD_BG,
            anchor="w",
        )
        self.result_count_lbl.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        self.result_box = tk.Frame(
            self.ingredient_card,
            bg=SUCCESS_BG,
            highlightthickness=1,
            highlightbackground=SUCCESS_BORDER,
            bd=0,
        )
        self.result_box.grid(row=3, column=0, sticky="nsew")

        self.result_lbl = tk.Label(
            self.result_box,
            text="",
            font=self.big_result_font,
            fg=SUCCESS_COLOR,
            bg=SUCCESS_BG,
            wraplength=self.sidebar_width - 56,
            justify="center",
            anchor="center",
            padx=12,
            pady=10,
        )
        self.result_lbl.pack(fill="both", expand=True)

    # ==========================================================
    # SCREEN LIFECYCLE
    # ==========================================================
    def tkraise(self, *args, **kwargs):
        self.cancel_pending_redirects()

        super().tkraise(*args, **kwargs)
        self.update_idletasks()

        frame = getattr(self.controller, "captured_frame", None)
        items = getattr(self.controller, "detected_items", []) or []
        item = getattr(self.controller, "detected_item", "Unknown") or "Unknown"

        if isinstance(items, str):
            items = [items]

        cleaned_items = []
        for value in items:
            clean = str(value).strip()
            if clean and clean not in cleaned_items:
                cleaned_items.append(clean)

        if cleaned_items:
            display_text = "\n".join(name.upper() for name in cleaned_items)
            count_text = f"{len(cleaned_items)} item detected" if len(cleaned_items) == 1 else f"{len(cleaned_items)} items detected"
            footer_text = f"Captured: {', '.join(cleaned_items)}"
        else:
            display_text = str(item).upper()
            count_text = "1 item detected"
            footer_text = f"Captured: {item}"

        self.result_lbl.config(text=display_text)
        self.result_count_lbl.config(text=count_text)
        self.footer_lbl.config(text=footer_text)

        if frame is not None:
            self.image_status_label.config(text="Image captured", fg=BAR_COLOR)
            self.after(80, lambda selected_frame=frame: self.render_captured_image(selected_frame))
        else:
            self.show_no_image()

        self.redirect_after_id = self.after(2000, self.go_to_next_screen)

    def cancel_pending_redirects(self):
        if self.redirect_after_id:
            try:
                self.after_cancel(self.redirect_after_id)
            except Exception:
                pass
            self.redirect_after_id = None

    def show_no_image(self):
        self.img_label.configure(
            image="",
            text="No image captured",
            font=("Arial", 15 if self.compact else 17, "bold"),
            fg="#9CA3AF",
            bg="#050B12",
        )
        self.img_label.image = None
        self.image_status_label.config(text="No image", fg=WARNING_COLOR)

    def render_captured_image(self, frame):
        if frame is None:
            self.show_no_image()
            return

        c_w = self.img_container.winfo_width()
        c_h = self.img_container.winfo_height()

        if c_w < 80 or c_h < 80:
            c_w = 620 if self.compact else 760
            c_h = 360 if self.compact else 460

        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)

            img_pil = self.crop_to_fill(img_pil, c_w, c_h)
            rounded_img = self.make_rounded_image(img_pil, radius=16)

            imgtk = ImageTk.PhotoImage(rounded_img)
            self.img_label.configure(image=imgtk, text="")
            self.img_label.image = imgtk

        except Exception as error:
            self.img_label.configure(
                image="",
                text=f"Unable to display image\n{error}",
                font=("Arial", 11, "bold"),
                fg="#9CA3AF",
                bg="#050B12",
                justify="center",
            )
            self.img_label.image = None

    # ==========================================================
    # NAVIGATION
    # ==========================================================
    def go_to_next_screen(self):
        self.cancel_pending_redirects()

        target = getattr(self.controller, "after_result_target", "recipe")

        if target == "choice" and self.controller.frames.get(ScanChoiceScreen):
            self.controller.after_result_target = "recipe"
            self.controller.show_frame(ScanChoiceScreen)
            return

        recipe_frame = self.controller.frames.get(RecipeScreen)

        if recipe_frame:
            self.controller.recipe_mode = "region"
            recipe_frame.current_mode = "region"
            self.controller.after_result_target = "recipe"
            self.controller.show_frame(RecipeScreen)

    def go_to_recipe(self):
        self.go_to_next_screen()