import tkinter as tk
import cv2
from PIL import Image, ImageTk
import numpy as np
from ultralytics import YOLO

# --- UI Constants ---
ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
CARD_SHADOW = "#D0D5DA"
BUTTON_COLOR = "#1680e4"
DISABLED_BUTTON_COLOR = "#7f8c8d"

# --- Detection Settings ---
MIN_BRIGHTNESS = 30
MIN_OBJECT_AREA = 25000 
CONFIDENCE_THRESHOLD = 0.60 
BAR_HEIGHT = 70
BUTTON_W = 140  
BUTTON_H = 60
CHECKS = ["Sufficient Light", "Vegetable Detected", "Vegetable Close Enough"]

class ScanScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        try:
            self.model = YOLO("best.pt")
            self.class_names = self.model.names
        except Exception as e:
            print(f"Error loading model: {e}")

        self.cap = None
        self.running = False
        self.after_id = None
        self.last_frame = None
        self.prev_gray_small = None 
        self.is_processing = False 
        self.frame_count = 0  
        
        self.countdown_val = 2
        self.is_counting = False
        self.timer_after_id = None
        self.stability_threshold = 3000 

        self.setup_ui()

    def setup_ui(self):
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=BAR_HEIGHT)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)
        tk.Label(top_bar, text="Scan the ingredients", font=("Arial", 22, "bold"),
                 fg="white", bg=BAR_COLOR).pack(expand=True)

        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=BAR_HEIGHT)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        center_frame = tk.Frame(self, bg="white")
        center_frame.pack(expand=True, fill="both", padx=20, pady=10)

        right_frame = tk.Frame(center_frame, bg="white", width=260)
        right_frame.pack(side="right", fill="y", padx=(10,0))
        right_frame.pack_propagate(False)

        right_shadow = tk.Frame(right_frame, bg=CARD_SHADOW)
        right_shadow.pack(fill="both", expand=True)
        right_card = tk.Frame(right_shadow, bg=CARD_BG, padx=15, pady=10)
        right_card.pack(padx=3, pady=3, fill="both", expand=True)

        self.timer_label = tk.Label(right_card, text="Ready", font=("Arial", 18, "bold"), 
                                    bg=CARD_BG, fg=BAR_COLOR)
        self.timer_label.pack(pady=(10, 15))

        self.check_labels = {}
        for check in CHECKS:
            lbl = tk.Label(right_card, text=f"⚪ {check}", font=("Arial", 11),
                           fg="#7f8c8d", bg=CARD_BG, anchor="w", wraplength=220)
            lbl.pack(pady=8, fill="x")
            self.check_labels[check] = lbl

        self.tap_card = tk.Frame(right_card, bg=BUTTON_COLOR, width=BUTTON_W, height=BUTTON_H,
                                highlightthickness=2, highlightbackground="#0A4F7A", relief="raised", bd=4)
        self.tap_card.pack(side="bottom", pady=20)
        self.tap_card.pack_propagate(False)

        self.tap_label = tk.Label(self.tap_card, text="MANUAL SCAN", font=("Arial", 11, "bold"),
                                  fg="white", bg=BUTTON_COLOR)
        self.tap_label.pack(expand=True)

        self.tap_card.bind("<Button-1>", lambda e: self.perform_capture_and_check(manual=True))
        self.tap_label.bind("<Button-1>", lambda e: self.perform_capture_and_check(manual=True))

        left_frame = tk.Frame(center_frame, bg="white")
        left_frame.pack(side="left", fill="both", expand=True)

        card_shadow = tk.Frame(left_frame, bg=CARD_SHADOW)
        card_shadow.pack(fill="both", expand=True)
        self.video_container = tk.Frame(card_shadow, bg=CARD_BG)
        self.video_container.pack(padx=3, pady=3, fill="both", expand=True)

        self.video_label = tk.Label(self.video_container, bg="black")
        self.video_label.pack(expand=True, fill="both")

    def cleanup_camera(self):
        self.running = False
        self.stop_timer()
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        if self.cap:
            self.cap.release()
            self.cap = None

    def tkraise(self, *args, **kwargs):
        self.cleanup_camera()
        super().tkraise(*args, **kwargs)
        self.reset_checks()
        self.is_processing = False
        self.after(200, self.start_camera)

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.after(500, self.start_camera)
            return
        self.running = True
        self.update_frame()

    def update_frame(self):
        if not self.running or self.cap is None:
            return
            
        ret, frame = self.cap.read()
        if ret:
            self.last_frame = frame.copy()
            self.frame_count += 1
            
            # Note: We are no longer drawing rectangles on the display_frame
            display_frame = frame.copy()

            if not self.is_processing and self.frame_count % 12 == 0:
                small_gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (160, 120))
                is_still = True
                if self.prev_gray_small is not None:
                    delta = cv2.absdiff(self.prev_gray_small, small_gray)
                    movement = np.sum(delta > 25)
                    if movement > self.stability_threshold:
                        is_still = False
                
                self.perform_capture_and_check(manual=False, is_still=is_still)
                self.prev_gray_small = small_gray

            v_w = self.video_container.winfo_width()
            v_h = self.video_container.winfo_height()
            if v_w > 10 and v_h > 10:
                small_frame = cv2.resize(display_frame, (v_w, v_h), interpolation=cv2.INTER_NEAREST)
                frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)
                img = ImageTk.PhotoImage(img_pil)
                self.video_label.configure(image=img)
                self.video_label.image = img
        
        self.after_id = self.after(15, self.update_frame)

    def perform_capture_and_check(self, manual=False, is_still=False):
        if self.last_frame is None or self.is_processing:
            return
        
        frame = self.last_frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        light_pass = np.mean(gray) >= MIN_BRIGHTNESS
        
        results = self.model.predict(source=frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        
        obj_pass = False
        close_pass = False
        det_name = "None"

        if results and len(results[0].boxes) > 0:
            box = results[0].boxes[0]
            area = float(box.xywh[0][2] * box.xywh[0][3])
            temp_name = self.class_names[int(box.cls[0])]
            
            # We only confirm detection if it meets the area (closeness) threshold
            if area >= MIN_OBJECT_AREA:
                close_pass = True
                obj_pass = True 
                det_name = temp_name

        self.update_indicators(light_pass, obj_pass, close_pass, det_name)

        if manual:
            if obj_pass and close_pass:
                self.execute_capture(frame, det_name)
            else:
                msg = "NO VEGETABLE!" if not obj_pass else "MOVE CLOSER!"
                self.timer_label.config(text=msg, fg="#C0392B")
                self.after(1000, lambda: self.timer_label.config(text="Scanning...", fg=BAR_COLOR))
            return

        # Auto capture only starts if all requirements (including distance) are met
        if light_pass and obj_pass and close_pass:
            if not is_still:
                self.timer_label.config(text="STAY STILL", fg="#C0392B")
            if not self.is_counting:
                self.start_timer(det_name)
        else:
            self.stop_timer()
            self.timer_label.config(text="Scanning...", fg=BAR_COLOR)

    def start_timer(self, name):
        self.is_counting = True
        self.countdown_val = 2
        self.detected_at_start = name
        self.run_timer_tick()

    def run_timer_tick(self):
        if not self.is_counting: return
        if self.countdown_val > 0:
            if self.timer_label.cget("text") != "STAY STILL":
                self.timer_label.config(text=f"Capture in {self.countdown_val}...", fg=BUTTON_COLOR)
            self.countdown_val -= 1
            self.timer_after_id = self.after(1000, self.run_timer_tick)
        else:
            self.execute_capture(self.last_frame, self.detected_at_start)

    def stop_timer(self):
        self.is_counting = False
        if self.timer_after_id:
            self.after_cancel(self.timer_after_id)
            self.timer_after_id = None

    def execute_capture(self, frame, name):
        if self.is_processing: return
        self.is_processing = True
        self.running = False
        self.controller.captured_frame = frame
        self.controller.detected_item = name
        self.timer_label.config(text="CAPTURED!", fg="#27ae60")
        self.cleanup_camera()
        self.after(400, self.go_to_results)

    def update_indicators(self, light, obj, close, name):
        self.check_labels["Sufficient Light"].config(
            text="✅ Sufficient Light" if light else "❌ Low Light",
            fg="#27ae60" if light else "#C0392B"
        )
        self.check_labels["Vegetable Detected"].config(
            text=f"✅ {name}" if obj else "❌ No Vegetable Found",
            fg="#27ae60" if obj else "#C0392B"
        )
        self.check_labels["Vegetable Close Enough"].config(
            text="✅ Distance OK" if close else "❌ Move Closer",
            fg="#27ae60" if close else "#C0392B"
        )

    def go_to_results(self):
        target_name = "ResultScreen"
        for screen_class in self.controller.frames.keys():
            if target_name in str(screen_class):
                self.controller.show_frame(screen_class)
                break

    def reset_checks(self):
        self.timer_label.config(text="Ready", fg=BAR_COLOR)
        for check in CHECKS:
            self.check_labels[check].config(text=f"⚪ {check}", fg="#7f8c8d")