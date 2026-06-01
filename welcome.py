import tkinter as tk
from scan import ScanScreen
from PIL import Image, ImageTk

ACCENT_COLOR = "#011118"
BAR_COLOR = "#0D6791"
BUTTON_COLOR = "#1680e4"

class WelcomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # -------------------- TOP BAR --------------------
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=70)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        # -------------------- BOTTOM BAR --------------------
        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=70)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        # -------------------- CENTER FRAME --------------------
        center_frame = tk.Frame(self, bg="white")
        center_frame.pack(expand=True, fill="both")

        # Force layout update
        self.update_idletasks()

        screen_width = controller.winfo_width()
        screen_height = controller.winfo_height()

        available_height = screen_height - 70 - 70 - 120
        available_width = screen_width - 40

        # -------------------- LOGO --------------------
        img = Image.open("hanapsangkap.png")

        w, h = img.size
        scale = min(
            available_width / w,
            available_height / h
        )

        new_size = (int(w * scale), int(h * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        self.hanap_img = ImageTk.PhotoImage(img)
        img_label = tk.Label(center_frame, image=self.hanap_img, bg="white")
        img_label.pack(pady=10)

        tap_card = tk.Frame(
            center_frame,
            bg=BUTTON_COLOR,
            width=420,
            height=60,
            highlightthickness=2,
            highlightbackground="#0A4F7A",
            relief="raised",
            bd=4
        )
        tap_card.pack(pady=10)
        tap_card.pack_propagate(False)

        tap_label = tk.Label(
            tap_card,
            text="TAP TO PROCEED",
            font=("Arial", 22, "bold"),
            fg="white",
            bg=BUTTON_COLOR
        )
        tap_label.pack(expand=True)

        def proceed_to_scan(event=None):
            controller.detected_item = None
            controller.detected_items = []
            controller.captured_frame = None
            controller.scan_more = False
            controller.scan_mode = "vegetable"
            controller.after_result_target = "choice"
            self.after(50, lambda: controller.show_frame(ScanScreen))

        def on_enter(e):
            tap_card.config(bg="#1A8FF0")
            tap_label.config(bg="#1A8FF0")

        def on_leave(e):
            tap_card.config(bg=BUTTON_COLOR)
            tap_label.config(bg=BUTTON_COLOR)

        tap_card.bind("<Button-1>", proceed_to_scan)
        tap_label.bind("<Button-1>", proceed_to_scan)
        tap_card.bind("<Enter>", on_enter)
        tap_card.bind("<Leave>", on_leave)
        tap_label.bind("<Enter>", on_enter)
        tap_label.bind("<Leave>", on_leave)
