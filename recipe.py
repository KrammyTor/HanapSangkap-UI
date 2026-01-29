import tkinter as tk
from PIL import Image, ImageTk
from dish import DishScreen, DISH_DETAILS
import os

# --- UI Constants ---
ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
INNER_CARD = "#FFFFFF"
CARD_SHADOW = "#D0D5DA"
BUTTON_ACTIVE = "#74B3CE"
BUTTON_IDLE = "#E6ECF2"
LINE_COLOR = "#B8C1C9"
NAV_BTN_COLOR = "#0D6791"

IMAGE_WIDTH = 160
IMAGE_HEIGHT = 120
NAV_BTN_SIZE = 70

class RecipeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        self._scroll_job = None

        # -------------------- TOP BAR --------------------
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=70)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)
        self.title_label = tk.Label(
            top_bar, text="", font=("Arial", 22, "bold"),
            fg="white", bg=BAR_COLOR
        )
        self.title_label.pack(expand=True)

        # -------------------- BOTTOM BAR --------------------
        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=70)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        # -------------------- CENTER CONTENT --------------------
        self.center = tk.Frame(self, bg="white")
        self.center.pack(expand=True, fill="both")

        # -------------------- REGION SELECTOR --------------------
        region_frame = tk.Frame(self.center, bg="white")
        region_frame.pack(pady=(15, 10))

        self.region_var = tk.StringVar(value="Luzon")
        self.region_buttons = {}
        for region in ["Luzon", "Visayas", "Mindanao"]:
            btn_canvas = tk.Canvas(region_frame, width=100, height=45, bg="white", highlightthickness=0)
            btn_canvas.pack(side="left", padx=8)
            self._draw_rounded_button(btn_canvas, BUTTON_IDLE, region.upper())
            btn_canvas.bind("<Button-1>", lambda e, r=region: self.set_region(r))
            self.region_buttons[region] = btn_canvas

        # -------------------- MAIN LAYOUT --------------------
        self.main_layout = tk.Frame(self.center, bg="white")
        self.main_layout.pack(expand=True, fill="both", padx=25, pady=5)

        self.list_area = tk.Frame(self.main_layout, bg="white")
        self.list_area.pack(side="left", expand=True, fill="both")

        shadow = tk.Frame(self.list_area, bg=CARD_SHADOW, padx=1, pady=1)
        shadow.pack(expand=True, fill="both")

        card_container = tk.Frame(shadow, bg=CARD_BG)
        card_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(card_container, bg=CARD_BG, highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=CARD_BG)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # -------------------- NAVIGATION STRIP --------------------
        self.control_strip = tk.Frame(self.main_layout, bg="white", width=110)
        self.control_strip.pack(side="right", fill="y", padx=(8, 0))
        self.control_strip.pack_propagate(False)

        btn_cluster = tk.Frame(self.control_strip, bg="white")
        btn_cluster.place(relx=0.5, rely=0.5, anchor="center")

        self.up_canvas = tk.Canvas(btn_cluster, width=NAV_BTN_SIZE, height=NAV_BTN_SIZE, bg="white", highlightthickness=0)
        self.up_canvas.pack(pady=10)
        self._draw_scroll_button(self.up_canvas, "▲")
        self.up_canvas.bind("<Button-1>", lambda e: self.start_scroll(-1))
        self.up_canvas.bind("<ButtonRelease-1>", lambda e: self.stop_scroll())

        self.down_canvas = tk.Canvas(btn_cluster, width=NAV_BTN_SIZE, height=NAV_BTN_SIZE, bg="white", highlightthickness=0)
        self.down_canvas.pack(pady=10)
        self._draw_scroll_button(self.down_canvas, "▼")
        self.down_canvas.bind("<Button-1>", lambda e: self.start_scroll(1))
        self.down_canvas.bind("<ButtonRelease-1>", lambda e: self.stop_scroll())

        # -------------------- SCAN AGAIN BUTTON --------------------
        self.scan_card = tk.Frame(
            bottom_bar, bg=ACCENT_COLOR, width=220, height=46,
            highlightthickness=2, highlightbackground="#0A4F7A",
            relief="raised", bd=4, cursor="hand2"
        )
        self.scan_card.pack(pady=12)
        self.scan_card.pack_propagate(False)

        self.scan_label = tk.Label(
            self.scan_card, text="SCAN AGAIN", font=("Helvetica", 11, "bold"),
            fg="white", bg=ACCENT_COLOR
        )
        self.scan_label.pack(expand=True)

        self.scan_card.bind("<Button-1>", lambda e: self.scan_again())
        self.scan_label.bind("<Button-1>", lambda e: self.scan_again())

    # -------------------- HELPER FUNCTIONS --------------------
    def _draw_rounded_button(self, canvas, color, text):
        w, h = 100, 45
        r = h // 2
        canvas.delete("all")
        canvas.create_oval(0, 0, r*2, h, fill=color, outline=color)
        canvas.create_oval(w-r*2, 0, w, h, fill=color, outline=color)
        canvas.create_rectangle(r, 0, w-r, h, fill=color, outline=color)
        txt_color = "#555" if color == BUTTON_IDLE else "white"
        canvas.create_text(w//2, h//2, text=text, fill=txt_color, font=("Helvetica", 11, "bold"))

    def _draw_scroll_button(self, canvas, symbol):
        s = NAV_BTN_SIZE
        canvas.delete("all")
        canvas.create_oval(5, 5, s-5, s-5, fill=NAV_BTN_COLOR, outline=NAV_BTN_COLOR)
        canvas.create_text(s//2, s//2, text=symbol, fill="white", font=("Arial", 26, "bold"))

    def start_scroll(self, direction):
        if self._scroll_job: self.after_cancel(self._scroll_job)
        self.canvas.yview_scroll(direction, "units")
        self._scroll_job = self.after(50, lambda: self.start_scroll(direction))

    def stop_scroll(self):
        if self._scroll_job:
            self.after_cancel(self._scroll_job)
            self._scroll_job = None

    # -------------------- CORE LOGIC: SHOW DISHES --------------------
    def show_dishes(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        region = self.region_var.get()
        ingredient = (getattr(self.controller, "detected_item", "") or "").strip().upper()

        region_matches = [d for d, det in DISH_DETAILS.items() if det.get("region") == region]
        
        if ingredient:
            dishes = []
            for d in region_matches:
                recipe_ingredients = [i.strip().upper() for i in DISH_DETAILS[d].get("ingredients", [])]
                if ingredient in recipe_ingredients:
                    dishes.append(d)
        else:
            dishes = region_matches

        if not dishes:
            lbl = tk.Label(self.scrollable_frame, text=f"No recipes for {ingredient}\nin {region}",
                          font=("Helvetica", 14, "italic"), fg="#7f8c8d", bg=CARD_BG, pady=50)
            lbl.grid(row=0, column=0, columnspan=2, sticky="nsew")
            return

        for i, dish in enumerate(dishes):
            details = DISH_DETAILS[dish]
            outer_card = tk.Frame(self.scrollable_frame, bg=LINE_COLOR, padx=1, pady=1)
            
            if len(dishes) == 1:
                outer_card.grid(row=0, column=0, columnspan=2, pady=20)
            else:
                outer_card.grid(row=i // 2, column=i % 2, padx=6, pady=8, sticky="nsew")

            dish_card = tk.Frame(outer_card, bg=INNER_CARD, padx=10, pady=10, cursor="hand2")
            dish_card.pack(fill="both", expand=True)

            img_container = tk.Frame(dish_card, bg="#F0F0F0", bd=1, relief="solid", cursor="hand2")
            img_container.pack(side="top", fill="both", expand=True)

            img_path = details.get("image", "")
            lbl_img = None
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path).resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                    imgtk = ImageTk.PhotoImage(img)
                    lbl_img = tk.Label(img_container, image=imgtk, bg="#F0F0F0", cursor="hand2")
                    lbl_img.image = imgtk
                    lbl_img.pack(padx=2, pady=2)
                except Exception:
                    lbl_img = tk.Label(img_container, text="Image Error", bg="#F0F0F0", cursor="hand2")
                    lbl_img.pack(pady=20)
            else:
                lbl_img = tk.Label(img_container, text="No Image", bg="#F0F0F0", cursor="hand2")
                lbl_img.pack(pady=20)

            # --- THE TEXT SPACING FIX ---
            # 1. Removed fixed height=40
            # 2. Set expand=True and fill="both" to allow the area to grow
            # 3. Set wraplength=130 to force multi-line text for long names
            text_backdrop = tk.Frame(dish_card, bg=BUTTON_IDLE, pady=5, cursor="hand2")
            text_backdrop.pack(side="top", fill="both", expand=True, pady=(10, 0))

            lbl_name = tk.Label(text_backdrop, text=dish, font=("Helvetica", 10, "bold"), 
                               bg=BUTTON_IDLE, fg=BAR_COLOR, wraplength=130, cursor="hand2", justify="center")
            lbl_name.pack(expand=True, fill="both")

            # --- THE CLICK FIX ---
            card_parts = [dish_card, img_container, lbl_img, text_backdrop, lbl_name]
            for part in card_parts:
                if part:
                    part.bind("<Button-1>", lambda e, d=dish: self.open_dish(d))

    def set_region(self, region):
        self.region_var.set(region)
        self.canvas.yview_moveto(0)
        self.update_region_buttons()
        self.show_dishes()

    def update_region_buttons(self):
        for r, btn_canvas in self.region_buttons.items():
            color = BUTTON_ACTIVE if r == self.region_var.get() else BUTTON_IDLE
            self._draw_rounded_button(btn_canvas, color, r.upper())

    def open_dish(self, dish):
        self.controller.selected_dish = dish
        for name, frame in self.controller.frames.items():
            if "DishScreen" in str(name):
                self.controller.show_frame(name)
                break

    def scan_again(self):
        for name, frame in self.controller.frames.items():
            if "ScanScreen" in str(name):
                if hasattr(frame, 'reset_screen'): frame.reset_screen()
                self.controller.show_frame(name)
                break

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        ing = getattr(self.controller, 'detected_item', 'Ingredients')
        self.title_label.config(text=f"Recipes with {ing}")
        self.canvas.yview_moveto(0)
        self.update_region_buttons()
        self.show_dishes()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)