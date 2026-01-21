import tkinter as tk
import cv2
from PIL import Image, ImageTk
from result import ResultScreen
import numpy as np

ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
CARD_SHADOW = "#D0D5DA"
BUTTON_COLOR = "#1680e4"

VIDEO_WIDTH = 560
VIDEO_HEIGHT = 315
MIN_BRIGHTNESS = 15        # minimum average brightness allowed
MIN_OBJECT_AREA = 4000     # minimum contour area to consider object "close enough"

class ScanScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # Top & bottom bars
        tk.Frame(self, bg=BAR_COLOR, height=120).pack(fill="x", side="top")
        tk.Frame(self, bg=BAR_COLOR, height=120).pack(fill="x", side="bottom")

        center_frame = tk.Frame(self, bg="white")
        center_frame.pack(expand=True)

        # Title
        tk.Label(center_frame, text="Scan the ingredients",
                 font=("Comic Sans MS", 28, "bold"),
                 fg=ACCENT_COLOR, bg="white").pack(pady=10)

        # Card
        card_shadow = tk.Frame(center_frame, bg=CARD_SHADOW)
        card_shadow.pack(pady=10)
        card = tk.Frame(card_shadow, bg=CARD_BG, padx=20, pady=20)
        card.pack(padx=4, pady=4)

        # Blank white placeholder
        blank_image = np.ones((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8) * 255
        self.blank_imgtk = ImageTk.PhotoImage(Image.fromarray(blank_image))

        self.video_label = tk.Label(card, image=self.blank_imgtk, bg=CARD_BG)
        self.video_label.image = self.blank_imgtk
        self.video_label.pack()

        # Loading text
        self.loading_label = tk.Label(card, text="Loading...", font=("Helvetica", 20),
                                      fg=ACCENT_COLOR, bg=CARD_BG)
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- Warning above capture button ---
        self.warning_label = tk.Label(center_frame, text="",
                                      font=("Helvetica", 18),
                                      fg="red", bg="white")
        self.warning_label.pack(pady=(0, 10))  # stays above the button

        # Capture button
        self.capture_btn = tk.Label(center_frame, text="CAPTURE",
                                    font=("Helvetica", 20, "bold"),
                                    bg=BUTTON_COLOR, fg="white",
                                    width=14, height=2)
        self.capture_btn.pack(pady=10)
        self.capture_btn.bind("<Button-1>", self.capture_image)
        self.capture_btn.bind("<Enter>", lambda e: self.capture_btn.config(bg="#0f6dc2"))
        self.capture_btn.bind("<Leave>", lambda e: self.capture_btn.config(bg=BUTTON_COLOR))

        # Camera vars
        self.cap = None
        self.running = False
        self.last_frame = None
        self.after_id = None

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        self.warning_label.config(text="")

        # ------------------- FIX -------------------
        # Reset previous frame so captured image doesn't show
        self.last_frame = None
        blank_image = np.ones((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8) * 255
        self.blank_imgtk = ImageTk.PhotoImage(Image.fromarray(blank_image))
        self.video_label.configure(image=self.blank_imgtk)
        self.video_label.image = self.blank_imgtk

        # Stop any previous capture session
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        # -------------------------------------------

        # Start fresh camera session
        self.after(100, self.start_camera)

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.update_frame()

    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if ret:
            self.last_frame = frame.copy()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (VIDEO_WIDTH, VIDEO_HEIGHT))
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            # Hide loading text
            self.loading_label.place_forget()

            # --- LIVE DETECTION ---
            self.check_light_and_distance(frame)

        self.after_id = self.after(30, self.update_frame)

    def check_light_and_distance(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)

        if avg_brightness < MIN_BRIGHTNESS:
            self.warning_label.config(text="Too dark! Please add more light.")
            return False

        _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) == 0:
            self.warning_label.config(text="No object detected!")
            return False

        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) < MIN_OBJECT_AREA:
            self.warning_label.config(text="Object not centered! Move it closer to center.")
            return False

        x, y, w, h = cv2.boundingRect(largest_contour)
        center_x = x + w / 2
        center_y = y + h / 2
        if abs(center_x - VIDEO_WIDTH/2) > VIDEO_WIDTH*0.4 or abs(center_y - VIDEO_HEIGHT/2) > VIDEO_HEIGHT*0.4:
            self.warning_label.config(text="Object too far! Move closer.")
            return False

        # Clear warning if all checks passed
        self.warning_label.config(text="")
        return True

    def capture_image(self, event=None):
        if self.last_frame is None:
            return

        # Only capture if live check passes
        if not self.check_light_and_distance(self.last_frame):
            return

        # Passed all checks → capture
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

        self.controller.captured_frame = self.last_frame
        self.controller.detected_item = "Garlic"
        self.after(50, lambda: self.controller.show_frame(ResultScreen))
