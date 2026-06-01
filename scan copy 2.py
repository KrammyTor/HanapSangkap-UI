import os
import glob
import threading
import time
import tkinter as tk
import cv2
from PIL import Image, ImageTk
import numpy as np
from ultralytics import YOLO

try:
    import serial
    SERIAL_AVAILABLE = True
    SERIAL_IMPORT_ERROR = None
except Exception as serial_error:
    serial = None
    SERIAL_AVAILABLE = False
    SERIAL_IMPORT_ERROR = serial_error

# --- UI Constants ---
ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
BUTTON_COLOR = "#1680e4"
TEMP_BUTTON_COLOR = "#27ae60"
DISABLED_BUTTON_COLOR = "#7f8c8d"
ERROR_COLOR = "#C0392B"
SUCCESS_COLOR = "#27ae60"

# --- Redesigned UI Colors ---
PAGE_BG = "#FFFFFF"
PANEL_BG = "#F7FBFD"
PANEL_BORDER = "#DCEAF0"
TEXT_COLOR = "#263238"
MUTED_TEXT = "#6B7280"

VIDEO_BG = "#050B12"
VIDEO_BORDER = BAR_COLOR

SCAN_BUTTON_HOVER = "#126FCC"
TEMP_BUTTON_HOVER = "#219653"

WARNING_BG = "#FFF1F1"
SUCCESS_BG = "#EEFFF4"
NEUTRAL_BG = "#EEF5F8"

# --- Weight Module Colors ---
WEIGHT_BG = "#FFF5F3"
WEIGHT_BORDER = "#FFD0D0"
WEIGHT_ACCENT = "#E35D5B"
WEIGHT_DARK = "#B93E3C"
WEIGHT_BAR_BG = "#FFE1DD"
WEIGHT_BAR_FILL = "#E35D5B"

# --- Detection Settings ---
MIN_BRIGHTNESS = 30

MIN_OBJECT_AREA = 1200
CONFIDENCE_THRESHOLD = 0.45
YOLO_IMAGE_SIZE = 640
MAX_DETECTIONS = 30

# Scan several frames when the user taps SCAN.
# This prevents the scan from saving only 1-2 ingredients because YOLO missed
# smaller items in a single frame.
SCAN_FRAMES = 2
SCAN_FRAME_DELAY = 0.0
MIN_HITS_TO_ACCEPT = 1

# --- Meat scan validation ---
# The normal detection threshold stays balanced for preview and general scanning.
# For meat + weighing, we use stricter confirmation only when the SCAN MEAT button is pressed.
# This helps reduce false meat scans from skin/background when there is no actual meat in frame.
MEAT_SCAN_CONFIRM_CONFIDENCE = 0.55
MIN_MEAT_WEIGHT_KG_FOR_SCAN = 0.02

# --- Real Weight Sensor Settings: Arduino + HX711 -> USB Serial -> Raspberry Pi ---
# The HX711 stays connected to the Arduino, where it already works reliably.
# The Arduino sends weight lines to the Raspberry Pi through USB serial.
# Supported auto-detected ports usually include /dev/ttyACM0 or /dev/ttyUSB0.
USE_REAL_LOAD_CELL = True
ARDUINO_SERIAL_PORT = None  # Auto-detect /dev/ttyACM* or /dev/ttyUSB*
ARDUINO_BAUD_RATE = 9600
ARDUINO_SERIAL_TIMEOUT = 0.05
ARDUINO_RECONNECT_DELAY = 1.0

# Keep this fallback so the UI still opens on a laptop or if GPIO is not available.
LOAD_CELL_MAX_KG = 2.0
TEMP_MEAT_WEIGHT_KG = 0.0
MIN_MEAT_WEIGHT_KG_FOR_SCAN = 0.02

# --- Meat scan bypass for testing/demo ---
# Press Shift + Enter while in Meat Mode to skip camera/scale validation.
# This adds chicken with 125 g as the default measured meat.
BYPASS_MEAT_NAME = "chicken"
BYPASS_MEAT_WEIGHT_G = 125
BYPASS_MEAT_WEIGHT_KG = BYPASS_MEAT_WEIGHT_G / 1000

# 7-inch screen compact bar sizes
BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 10

# --- Model Paths ---
# Make sure both files are beside scan.py
DEFAULT_MODEL_PATH = "esongo.pt"
MEAT_MODEL_PATH = "meatmeat.pt"

VEGETABLE_KEYWORDS = {
    "ampalaya",
    "cabbage",
    "carrot",
    "corn",
    "eggplant",
    "garlic",
    "onion",
    "potato",
    "pumpkin",
    "sayote",
    "sitaw",
    "tomato",
    "radish",
    "okra",
    "ginger",
}

MODE_COPY = {
    "vegetable": {
        "title": "Scan the Vegetables",
        "short_title": "Vegetable Mode",
        "detected": "Ingredient Detected",
        "in_frame": "Vegetable In Frame",
        "requirements": ["Sufficient Light", "Ingredient Detected", "Vegetable In Frame"],
        "none": "NO VEGETABLE!",
        "wrong": "Vegetables only",
        "scan_text": "Scanning vegetables...",
        "ready": "Ready to scan vegetables",
        "instruction": "Place vegetables clearly inside the camera frame.",
        "scan_button": "SCAN VEGETABLE",
        "accent": "#2E9B5F",
        "mode_bg": "#E9F9EF",
        "mode_fg": "#1F6F43",
    },
    "meat": {
        "title": "Scan the Meat",
        "short_title": "Meat Mode",
        "detected": "Meat Detected",
        "in_frame": "Meat In Frame",
        "requirements": ["Sufficient Light", "Meat Detected", "Meat In Frame"],
        "none": "NO MEAT!",
        "wrong": "Meat only",
        "scan_text": "Scanning meat...",
        "ready": "Ready to scan meat",
        "instruction": "Place meat clearly inside the camera frame.",
        "scan_button": "SCAN MEAT",
        "accent": "#E35D5B",
        "mode_bg": "#FFF0F0",
        "mode_fg": "#B93E3C",
    },
}


class ArduinoSerialWeightReader:
    """
    Reads live weight values from an Arduino over USB serial.

    Expected Arduino line formats:
        W,<grams>,<kilograms>,<calibration_factor>
        S,<status text>
        E,<error text>

    This runs in a background thread so the Tkinter UI will not freeze.
    """

    def __init__(
        self,
        port=ARDUINO_SERIAL_PORT,
        baud_rate=ARDUINO_BAUD_RATE,
        timeout=ARDUINO_SERIAL_TIMEOUT,
    ):
        self.requested_port = port
        self.baud_rate = int(baud_rate)
        self.timeout = float(timeout)

        self.serial_port = None
        self.port_in_use = None
        self.latest_weight_g = 0.0
        self.latest_weight_kg = 0.0
        self.latest_calibration_factor = 0.0
        self.status = "Not started"
        self.error_message = ""

        self.running = False
        self.ready = False
        self.lock = threading.Lock()
        self.thread = None
        self.taring = False
        self.last_weight_received_at = 0.0

    def _candidate_ports(self):
        if self.requested_port:
            return [self.requested_port]

        candidates = []
        preferred = [
            "/dev/ttyACM0",
            "/dev/ttyACM1",
            "/dev/ttyUSB0",
            "/dev/ttyUSB1",
        ]

        for port in preferred:
            if port not in candidates:
                candidates.append(port)

        for pattern in ("/dev/ttyACM*", "/dev/ttyUSB*"):
            for port in sorted(glob.glob(pattern)):
                if port not in candidates:
                    candidates.append(port)

        return candidates

    def _open_serial(self):
        if not SERIAL_AVAILABLE:
            with self.lock:
                self.status = "Serial library not available"
                self.error_message = str(SERIAL_IMPORT_ERROR)
                self.ready = False
            print(f"Arduino serial import error: {SERIAL_IMPORT_ERROR}")
            return False

        candidates = self._candidate_ports()
        if not candidates:
            with self.lock:
                self.status = "Arduino serial port not found"
                self.error_message = "No /dev/ttyACM* or /dev/ttyUSB* serial device found."
                self.ready = False
            print("Arduino serial port not found. Connect the Arduino by USB.")
            return False

        last_error = None
        for port in candidates:
            try:
                ser = serial.Serial(port, self.baud_rate, timeout=self.timeout)
                # Arduino commonly resets when serial opens.
                time.sleep(2.0)
                try:
                    ser.reset_input_buffer()
                except Exception:
                    pass
                self.serial_port = ser
                self.port_in_use = port
                with self.lock:
                    self.status = "Connected"
                    self.error_message = ""
                    self.ready = False
                print(f"Arduino weight serial connected: {port} @ {self.baud_rate}")
                return True
            except Exception as e:
                last_error = e

        with self.lock:
            self.status = "Arduino serial open failed"
            self.error_message = str(last_error) if last_error else "Unknown serial error"
            self.ready = False
        print(f"Arduino serial open failed: {self.error_message}")
        return False

    def start(self):
        if not USE_REAL_LOAD_CELL:
            self.status = "Real load cell disabled"
            return False

        if self.running:
            return True

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        return True

    def close(self):
        self.running = False

        try:
            if (
                self.thread
                and self.thread.is_alive()
                and threading.current_thread() is not self.thread
            ):
                self.thread.join(timeout=1.0)
        except Exception:
            pass

        try:
            if self.serial_port is not None:
                self.serial_port.close()
        except Exception:
            pass

        self.serial_port = None
        self.port_in_use = None
        self.thread = None
        self.ready = False
        self.taring = False
        self.status = "Stopped"

    def _handle_serial_line(self, line):
        text = str(line or "").strip()
        if not text:
            return

        if text.startswith("W,"):
            parts = text.split(",")
            if len(parts) >= 3:
                try:
                    weight_g = float(parts[1])
                    weight_kg = float(parts[2])
                    cal = float(parts[3]) if len(parts) >= 4 else self.latest_calibration_factor

                    if -5 < weight_g < 0:
                        weight_g = 0.0
                        weight_kg = 0.0

                    with self.lock:
                        self.latest_weight_g = weight_g
                        self.latest_weight_kg = weight_kg
                        self.latest_calibration_factor = cal
                        self.last_weight_received_at = time.time()
                        if not self.taring:
                            self.status = "Ready"
                        self.ready = True
                        self.error_message = ""
                except Exception as e:
                    with self.lock:
                        self.status = "Weight parse error"
                        self.error_message = f"{e} | line={text}"
                        self.ready = False
                    print(f"Arduino weight parse error: {e} | line={text}")
            return

        if text.startswith("S,"):
            status = text[2:].strip() or "Arduino status"
            normalized = status.upper()

            with self.lock:
                if normalized in ("TARING", "TARE_STARTED"):
                    self.taring = True
                    self.status = "Taring"
                elif normalized in ("TARE_DONE", "TARE_COMPLETE", "TARED"):
                    self.taring = False
                    self.status = "Ready"
                    self.ready = True
                elif normalized in ("HX711_READY", "READY"):
                    if not self.taring:
                        self.status = "Connected"
                else:
                    self.status = status
            print(f"Arduino weight status: {status}")
            return

        if text.startswith("E,"):
            error_text = text[2:].strip() or "Arduino error"
            with self.lock:
                self.status = "Arduino sensor error"
                self.error_message = error_text
                self.ready = False
            print(f"Arduino weight error: {error_text}")
            return

        print(f"Arduino serial: {text}")

    def _run_loop(self):
        while self.running:
            if self.serial_port is None:
                with self.lock:
                    if self.status not in ("Serial library not available", "Arduino serial open failed"):
                        self.status = "Connecting to Arduino"
                if not self._open_serial():
                    time.sleep(ARDUINO_RECONNECT_DELAY)
                    continue

            try:
                raw_line = self.serial_port.readline()
                if not raw_line:
                    time.sleep(0.02)
                    continue

                line = raw_line.decode("utf-8", errors="ignore").strip()
                self._handle_serial_line(line)

            except Exception as e:
                with self.lock:
                    self.status = "Arduino serial disconnected"
                    self.error_message = str(e)
                    self.ready = False
                print(f"Arduino serial read error: {e}")
                try:
                    if self.serial_port is not None:
                        self.serial_port.close()
                except Exception:
                    pass
                self.serial_port = None
                self.port_in_use = None
                time.sleep(ARDUINO_RECONNECT_DELAY)

    def tare_async(self):
        if self.serial_port is None:
            with self.lock:
                self.status = "Arduino not connected"
                self.error_message = "Cannot tare because Arduino serial is not connected."
                self.ready = False
            return

        try:
            with self.lock:
                self.taring = True
                self.status = "Taring"
            self.serial_port.write(b"t")
            self.serial_port.flush()
            print("Sent tare command to Arduino.")
        except Exception as e:
            with self.lock:
                self.taring = False
                self.status = "Tare command failed"
                self.error_message = str(e)
                self.ready = False
            print(f"Failed to send tare command to Arduino: {e}")

    def get_weight_kg(self):
        with self.lock:
            return float(self.latest_weight_kg)

    def get_weight_g(self):
        with self.lock:
            return float(self.latest_weight_g)

    def get_status(self):
        with self.lock:
            return str(self.status)

    def get_error_message(self):
        with self.lock:
            return str(self.error_message)


class ScanScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=PAGE_BG)
        self.controller = controller

        self.model = None
        self.class_names = {}
        self.active_model_path = None
        self.scan_mode = "vegetable"
        self.current_checks = MODE_COPY["vegetable"]["requirements"]
        self.load_model_for_mode("vegetable")

        self.cap = None
        self.running = False
        self.after_id = None
        self.last_frame = None
        self.is_processing = False
        self.frame_count = 0
        self.latest_preview_names = []
        self.latest_preview_count = 0
        self.scan_sequence_after_ids = []
        self.processing_message = None
        self.status_reset_after_id = None
        self.weight_after_id = None
        self.weight_reader = None
        self.weight_reader_started = False

        self.check_widgets = {}
        self.check_labels = {}

        self.setup_ui()
        self.bind_meat_bypass_shortcut()

    # ==========================================================
    # MODE + MODEL HELPERS
    # ==========================================================
    def get_scan_mode(self):
        mode = getattr(self.controller, "scan_mode", "vegetable") or "vegetable"
        if mode not in MODE_COPY:
            mode = "vegetable"
        return mode

    def get_model_path_for_mode(self, mode):
        if mode == "meat":
            return MEAT_MODEL_PATH

        return DEFAULT_MODEL_PATH

    def load_model_for_mode(self, mode):
        model_path = self.get_model_path_for_mode(mode)

        if self.model is not None and self.active_model_path == model_path:
            return

        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            self.model = YOLO(model_path)
            self.class_names = self.model.names
            self.active_model_path = model_path

            print(f"Loaded {mode} model: {model_path}")
            print(f"Model classes: {self.class_names}")

        except Exception as e:
            self.model = None
            self.class_names = {}
            self.active_model_path = None
            print(f"Error loading model '{model_path}': {e}")

    def normalize_name(self, name):
        clean = str(name or "").strip().lower()
        clean = clean.replace("_", " ")
        clean = clean.replace("-", " ")
        clean = clean.replace("/", " ")
        clean = " ".join(clean.split())
        return clean

    def name_matches_keywords(self, name, keywords):
        clean = self.normalize_name(name)
        return clean in keywords

    def is_allowed_for_mode(self, name, mode):
        if mode == "meat":
            # Meat mode uses meatmeat.pt only.
            # Since that model is meat-only, accept every class from it.
            return True

        return self.name_matches_keywords(name, VEGETABLE_KEYWORDS)

    def filter_detections_for_mode(self, detections, mode):
        filtered = [
            detection
            for detection in detections
            if self.is_allowed_for_mode(detection["name"], mode)
        ]

        filtered_names = []
        seen_names = set()

        for detection in filtered:
            clean_name = self.normalize_name(detection["name"])

            if clean_name not in seen_names:
                filtered_names.append(clean_name)
                seen_names.add(clean_name)

        return filtered_names, filtered

    # ==========================================================
    # REAL WEIGHT MODULE - ARDUINO HX711 OVER USB SERIAL
    # ==========================================================
    def start_real_weight_reader(self):
        if not USE_REAL_LOAD_CELL:
            return

        if self.weight_reader is not None:
            return

        self.weight_reader = ArduinoSerialWeightReader(
            port=ARDUINO_SERIAL_PORT,
            baud_rate=ARDUINO_BAUD_RATE,
            timeout=ARDUINO_SERIAL_TIMEOUT,
        )
        self.weight_reader_started = self.weight_reader.start()

    def stop_real_weight_reader(self):
        if self.weight_reader is not None:
            try:
                self.weight_reader.close()
            except Exception:
                pass

        self.weight_reader = None
        self.weight_reader_started = False

    def tare_weight_scale(self):
        if self.weight_reader is not None and self.weight_reader_started:
            self.weight_status_label.config(text="Taring... remove all weight", fg=WEIGHT_DARK)
            self.weight_reader.tare_async()
        else:
            self.weight_status_label.config(text="Load cell not available", fg=ERROR_COLOR)

    def get_current_meat_weight_kg(self):
        """
        Returns the current meat weight from the Arduino scale.

        Normal Meat Mode:
            - Shows 0g until Arduino sends a real W line.
            - Does NOT show fake 350g fallback.

        Secret bypass:
            - Still works separately inside bypass_meat_scan_default().
        """

        weight = 0.0

        if self.weight_reader is not None and self.weight_reader_started:
            try:
                sensor_status = self.weight_reader.get_status()
                sensor_weight = float(self.weight_reader.get_weight_kg())

                if sensor_status in ("Ready", "Connected") and sensor_weight >= 0:
                    weight = sensor_weight
            except Exception:
                weight = 0.0

        if weight < 0:
            weight = 0.0

        return weight

    def get_current_meat_weight_grams(self):
        return int(round(self.get_current_meat_weight_kg() * 1000))

    def get_weight_module_status_text(self, weight_kg):
        """
        Clean UI rule:
        - Do NOT show "Arduino connected" when the Arduino is working.
        - Only show Arduino-related text when there is a connection/problem.
        - Normal working state only talks about the meat/scale.
        """
        if self.weight_reader is not None:
            sensor_status = self.weight_reader.get_status()

            if sensor_status in ("Not started", "Connecting to Arduino"):
                return "Connecting to scale...", MUTED_TEXT

            if sensor_status == "Taring":
                return "Taring... remove all weight", WEIGHT_DARK

            if sensor_status in (
                "Serial library not available",
                "Arduino serial port not found",
                "Arduino serial open failed",
                "Arduino serial disconnected",
                "Arduino sensor error",
                "Weight parse error",
                "Arduino not connected",
                "Tare command failed",
            ):
                if sensor_status == "Serial library not available":
                    return "Install pyserial in venv", ERROR_COLOR
                return sensor_status, ERROR_COLOR

            if not self.weight_reader_started:
                return "Scale not available", ERROR_COLOR

        elif USE_REAL_LOAD_CELL:
            return "Scale not available", ERROR_COLOR

        if weight_kg <= 0:
            return "Waiting for meat on scale", MUTED_TEXT

        if weight_kg >= LOAD_CELL_MAX_KG:
            return "Maximum load reached", ERROR_COLOR

        return "Meat weight detected", WEIGHT_DARK

    def start_weight_module(self):
        if self.get_scan_mode() != "meat":
            self.stop_weight_module()
            return

        self.start_real_weight_reader()
        self.update_weight_module()

    def stop_weight_module(self):
        if self.weight_after_id:
            try:
                self.after_cancel(self.weight_after_id)
            except Exception:
                pass
            self.weight_after_id = None

    def update_weight_module(self):
        self.stop_weight_module()

        if self.get_scan_mode() != "meat":
            return

        weight_kg = self.get_current_meat_weight_kg()
        weight_percent = min(100, max(0, (weight_kg / LOAD_CELL_MAX_KG) * 100))

        weight_grams = self.get_current_meat_weight_grams()

        # Display grams only. No kg display on the UI.
        self.weight_value_label.config(text=f"{weight_grams} g")

        status_text, status_color = self.get_weight_module_status_text(weight_kg)
        self.weight_status_label.config(text=status_text, fg=status_color)

        self.weight_bar_canvas.delete("all")

        bar_w = self.weight_bar_width
        bar_h = 10 if self.compact else 14

        self.rounded_rect(
            self.weight_bar_canvas,
            0,
            0,
            bar_w,
            bar_h,
            radius=10,
            fill=WEIGHT_BAR_BG,
            outline=WEIGHT_BAR_BG,
        )

        fill_w = int(bar_w * (weight_percent / 100))

        if fill_w > 5:
            self.rounded_rect(
                self.weight_bar_canvas,
                0,
                0,
                fill_w,
                bar_h,
                radius=10,
                fill=WEIGHT_BAR_FILL,
                outline=WEIGHT_BAR_FILL,
            )

        self.weight_after_id = self.after(100, self.update_weight_module)

    def save_weight_for_meat(self, names):
        if self.get_scan_mode() != "meat":
            return

        if not hasattr(self.controller, "ingredient_weights"):
            self.controller.ingredient_weights = {}

        if not isinstance(self.controller.ingredient_weights, dict):
            self.controller.ingredient_weights = {}

        weight_grams = self.get_current_meat_weight_grams()

        for name in names:
            clean = self.normalize_name(name)
            if clean:
                self.controller.ingredient_weights[clean] = weight_grams

    # ==========================================================
    # UI HELPERS
    # ==========================================================
    def rounded_rect(self, canvas, x1, y1, x2, y2, radius=12, **kwargs):
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
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    def draw_mode_pill(self, mode):
        copy = MODE_COPY.get(mode, MODE_COPY["vegetable"])
        bg = copy["mode_bg"]
        fg = copy["mode_fg"]
        text = copy["short_title"].upper()

        self.mode_pill_canvas.delete("all")
        self.rounded_rect(
            self.mode_pill_canvas,
            2, 2, 176, 32,
            radius=16,
            fill=bg,
            outline=bg,
        )
        self.mode_pill_canvas.create_text(
            89, 17,
            text=text,
            fill=fg,
            font=("Arial", 9 if self.compact else 11, "bold")
        )

    def draw_mode_icon(self, mode):
        self.scan_icon_canvas.delete("all")

        copy = MODE_COPY.get(mode, MODE_COPY["vegetable"])
        accent = copy["accent"]

        size = 36 if self.compact else 48
        padding = 3

        self.scan_icon_canvas.config(width=size, height=size)

        self.scan_icon_canvas.create_oval(
            padding,
            padding,
            size - padding,
            size - padding,
            fill=accent,
            outline="white",
            width=2,
        )

        if mode == "meat":
            self.scan_icon_canvas.create_oval(
                size * 0.28,
                size * 0.36,
                size * 0.68,
                size * 0.64,
                fill="",
                outline="white",
                width=2,
            )
            self.scan_icon_canvas.create_oval(
                size * 0.42,
                size * 0.43,
                size * 0.54,
                size * 0.55,
                fill="white",
                outline="white",
                width=1,
            )
            self.scan_icon_canvas.create_line(
                size * 0.64,
                size * 0.42,
                size * 0.76,
                size * 0.34,
                fill="white",
                width=2,
            )
        else:
            self.scan_icon_canvas.create_oval(
                size * 0.32,
                size * 0.25,
                size * 0.72,
                size * 0.68,
                outline="white",
                width=2,
            )
            self.scan_icon_canvas.create_line(
                size * 0.34,
                size * 0.72,
                size * 0.72,
                size * 0.28,
                fill="white",
                width=2,
            )
            self.scan_icon_canvas.create_line(
                size * 0.48,
                size * 0.52,
                size * 0.66,
                size * 0.52,
                fill="white",
                width=2,
            )

    def set_detection_status(self, text, color):
        if hasattr(self, "detection_status_label"):
            self.detection_status_label.config(
                text=text,
                fg=color,
                wraplength=self.detection_status_wrap,
            )

    def set_default_status_text(self, mode=None):
        if mode not in MODE_COPY:
            mode = self.get_scan_mode()

        copy = MODE_COPY[mode]

        self.timer_label.config(text=copy["ready"], fg=TEXT_COLOR)
        self.instruction_label.config(
            text=copy["instruction"],
            fg=MUTED_TEXT,
            wraplength=self.status_subtext_wrap,
        )

        self.set_detection_status("WAITING FOR SCAN", MUTED_TEXT)

    def set_status_subtext(self, text, color):
        mode = self.get_scan_mode()
        copy = MODE_COPY[mode]

        self.timer_label.config(text=copy["ready"], fg=TEXT_COLOR)
        self.instruction_label.config(
            text=copy["instruction"],
            fg=MUTED_TEXT,
            wraplength=self.status_subtext_wrap,
        )

        self.set_detection_status(str(text).upper(), color)

    def create_action_button(self, parent, text, color, hover_color, border_color, command):
        button = tk.Frame(
            parent,
            bg=color,
            width=self.button_width,
            height=self.button_height,
            highlightthickness=2,
            highlightbackground=border_color,
            relief="raised",
            bd=3,
            cursor="hand2",
        )
        button.pack_propagate(False)

        label = tk.Label(
            button,
            text=text,
            font=self.button_font,
            fg="white",
            bg=color,
            cursor="hand2",
            justify="center",
            wraplength=self.button_width - 20,
        )
        label.pack(expand=True)

        def on_enter(event=None):
            button.config(bg=hover_color)
            label.config(bg=hover_color)

        def on_leave(event=None):
            button.config(bg=color)
            label.config(bg=color)

        for widget in (button, label):
            widget.bind("<Button-1>", lambda e: command())
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        return button, label

    def bind_meat_bypass_shortcut(self):
        """
        Demo/testing shortcut:
        Shift + Enter bypasses meat camera confirmation and live scale reading.
        It saves default meat as chicken with 125 g, then proceeds to recipe suggestions.
        """
        try:
            self.bind_all("<Shift-Return>", self.handle_meat_bypass_shortcut)
            self.bind_all("<Shift-KP_Enter>", self.handle_meat_bypass_shortcut)
        except Exception:
            pass

    def handle_meat_bypass_shortcut(self, event=None):
        if self.get_scan_mode() != "meat":
            return "break"

        self.bypass_meat_scan_default()
        return "break"

    def bypass_meat_scan_default(self):
        """
        Adds default meat data without requiring YOLO meat detection or HX711 weight.
        This is useful for testing when the camera/scale is not ready.
        """
        if self.get_scan_mode() != "meat":
            self.show_temporary_status("MEAT MODE ONLY", ERROR_COLOR, 1200)
            return

        existing_items = []
        for item in (getattr(self.controller, "detected_items", []) or []):
            clean = self.normalize_name(item)
            if clean and clean not in existing_items:
                existing_items.append(clean)

        default_meat = self.normalize_name(BYPASS_MEAT_NAME)
        if default_meat and default_meat not in existing_items:
            existing_items.append(default_meat)

        if not hasattr(self.controller, "ingredient_weights"):
            self.controller.ingredient_weights = {}

        if not isinstance(self.controller.ingredient_weights, dict):
            self.controller.ingredient_weights = {}

        self.controller.ingredient_weights[default_meat] = int(BYPASS_MEAT_WEIGHT_G)
        self.controller.temporary_meat_weight_kg = float(BYPASS_MEAT_WEIGHT_KG)

        if self.last_frame is not None:
            frame = self.last_frame.copy()
            self.controller.captured_frame = frame
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                f"{default_meat} {BYPASS_MEAT_WEIGHT_G}g",
                (40, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (255, 255, 255),
                3,
                cv2.LINE_AA,
            )
            self.controller.captured_frame = frame

        self.controller.detected_items = existing_items
        self.controller.detected_item = ", ".join(existing_items)
        self.controller.scan_more = False
        self.controller.after_result_target = "recipe"

        self.clear_scan_sequence()
        self.is_processing = True
        self.running = False

        self.set_status_subtext(f"{default_meat} scanned - {BYPASS_MEAT_WEIGHT_G} g", SUCCESS_COLOR)
        self.live_status_label.config(
            text=f"Bypass: {default_meat} {BYPASS_MEAT_WEIGHT_G} g",
            fg=SUCCESS_COLOR,
        )

        self.cleanup_camera()
        self.after(300, self.go_to_recipe_screen)

    # ==========================================================
    # UI
    # ==========================================================
    def setup_ui(self):
        screen_w = max(640, self.winfo_screenwidth())
        screen_h = max(480, self.winfo_screenheight())

        self.compact = screen_h <= 900 or screen_w <= 1100

        self.sidebar_width = 320 if self.compact else 360
        self.button_width = 255 if self.compact else 285
        self.button_height = 44 if self.compact else 58

        self.status_subtext_wrap = 205 if self.compact else 250
        self.detection_status_wrap = 285 if self.compact else 330
        self.weight_bar_width = self.sidebar_width - 52

        self.title_font = ("Arial", 18 if self.compact else 24, "bold")
        self.section_font = ("Arial", 12 if self.compact else 15, "bold")
        self.body_font = ("Arial", 9 if self.compact else 12)
        self.small_font = ("Arial", 8 if self.compact else 10)
        self.button_font = ("Arial", 12 if self.compact else 15, "bold")

        # -------------------- TOP BAR --------------------
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=BAR_HEIGHT)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        top_inner = tk.Frame(top_bar, bg=BAR_COLOR)
        top_inner.pack(expand=True, fill="both", padx=14)

        top_inner.grid_rowconfigure(0, weight=1)
        top_inner.grid_columnconfigure(0, weight=1)
        top_inner.grid_columnconfigure(1, weight=2)
        top_inner.grid_columnconfigure(2, weight=1)

        tk.Frame(top_inner, bg=BAR_COLOR).grid(row=0, column=0, sticky="nsew")

        self.heading_label = tk.Label(
            top_inner,
            text="Scan the Vegetables",
            font=self.title_font,
            fg="white",
            bg=BAR_COLOR,
        )
        self.heading_label.grid(row=0, column=1, sticky="nsew")

        self.mode_pill_canvas = tk.Canvas(
            top_inner,
            width=180,
            height=34,
            bg=BAR_COLOR,
            highlightthickness=0,
            bd=0
        )
        self.mode_pill_canvas.grid(row=0, column=2, sticky="e")
        self.draw_mode_pill("vegetable")

        # -------------------- BOTTOM BAR --------------------
        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=BOTTOM_BAR_HEIGHT)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        # -------------------- MAIN AREA --------------------
        center_frame = tk.Frame(self, bg=PAGE_BG)
        center_frame.pack(expand=True, fill="both", padx=12, pady=7)

        self.main_panel = tk.Frame(
            center_frame,
            bg=PANEL_BG,
            highlightthickness=2,
            highlightbackground=PANEL_BORDER,
        )
        self.main_panel.pack(expand=True, fill="both")

        self.main_panel.grid_rowconfigure(0, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)
        self.main_panel.grid_columnconfigure(1, weight=0)

        # -------------------- LEFT CAMERA AREA --------------------
        left_panel = tk.Frame(self.main_panel, bg=PANEL_BG)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=10)

        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        camera_header = tk.Frame(left_panel, bg=PANEL_BG)
        camera_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        camera_header.grid_columnconfigure(0, weight=1)

        self.video_title_label = tk.Label(
            camera_header,
            text="Live Camera",
            font=("Arial", 14 if self.compact else 18, "bold"),
            fg=TEXT_COLOR,
            bg=PANEL_BG,
            anchor="w",
        )
        self.video_title_label.grid(row=0, column=0, sticky="w")

        self.camera_status_label = tk.Label(
            camera_header,
            text="Camera starting...",
            font=("Arial", 8 if self.compact else 10, "bold"),
            fg=BAR_COLOR,
            bg="#E7F5FA",
            padx=9,
            pady=3,
        )
        self.camera_status_label.grid(row=0, column=1, sticky="e")

        self.video_container = tk.Frame(
            left_panel,
            bg=VIDEO_BG,
            highlightthickness=3,
            highlightbackground=VIDEO_BORDER,
        )
        self.video_container.grid(row=1, column=0, sticky="nsew")

        self.video_label = tk.Label(
            self.video_container,
            bg="black",
            text="Camera Preview",
            fg="#9CA3AF",
            font=("Arial", 13 if self.compact else 17, "bold"),
        )
        self.video_label.pack(expand=True, fill="both", padx=4, pady=4)

        self.video_footer = tk.Frame(left_panel, bg=PANEL_BG)
        self.video_footer.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        self.video_footer.grid_columnconfigure(0, weight=1)

        self.live_status_label = tk.Label(
            self.video_footer,
            text="Make sure the ingredient is well-lit and centered.",
            font=("Arial", 8 if self.compact else 11),
            fg=MUTED_TEXT,
            bg=PANEL_BG,
            anchor="w",
            wraplength=650,
            justify="left",
        )
        self.live_status_label.grid(row=0, column=0, sticky="w")

        # -------------------- RIGHT DASHBOARD AREA --------------------
        right_panel = tk.Frame(self.main_panel, bg=PANEL_BG, width=self.sidebar_width)
        right_panel.grid(row=0, column=1, sticky="ns", padx=(6, 12), pady=(0, 10))
        right_panel.grid_propagate(False)

        right_stack = tk.Frame(right_panel, bg=PANEL_BG)
        right_stack.place(x=0, y=0, width=self.sidebar_width, relheight=1)

        # -------------------- STATUS CARD --------------------
        self.status_card = tk.Frame(
            right_stack,
            bg=CARD_BG,
            padx=10,
            pady=7,
            height=112 if self.compact else 145,
        )
        self.status_card.pack(side="top", fill="x", pady=(0, 4))
        self.status_card.pack_propagate(False)

        self.status_top = tk.Frame(self.status_card, bg=CARD_BG)
        self.status_top.pack(fill="x")

        self.scan_icon_canvas = tk.Canvas(
            self.status_top,
            width=36 if self.compact else 48,
            height=36 if self.compact else 48,
            bg=CARD_BG,
            highlightthickness=0,
        )
        self.scan_icon_canvas.pack(side="left", padx=(0, 8), pady=(2, 0))
        self.draw_mode_icon("vegetable")

        status_text_holder = tk.Frame(self.status_top, bg=CARD_BG)
        status_text_holder.pack(side="left", fill="x", expand=True)

        self.timer_label = tk.Label(
            status_text_holder,
            text="Ready to scan vegetables",
            font=("Arial", 10 if self.compact else 14, "bold"),
            bg=CARD_BG,
            fg=TEXT_COLOR,
            wraplength=self.status_subtext_wrap,
            justify="left",
            anchor="w",
        )
        self.timer_label.pack(fill="x")

        self.instruction_label = tk.Label(
            status_text_holder,
            text="Place one vegetable clearly inside the camera frame.",
            font=("Arial", 8 if self.compact else 10),
            fg=MUTED_TEXT,
            bg=CARD_BG,
            wraplength=self.status_subtext_wrap,
            justify="left",
            anchor="w",
        )
        self.instruction_label.pack(fill="x", pady=(2, 0))

        self.detection_status_label = tk.Label(
            self.status_card,
            text="WAITING FOR SCAN",
            font=("Arial", 13 if self.compact else 17, "bold"),
            fg=MUTED_TEXT,
            bg=CARD_BG,
            anchor="center",
            justify="center",
            wraplength=self.detection_status_wrap,
        )
        self.detection_status_label.pack(fill="both", expand=True, pady=(4, 0))

        # Compatibility label only, not displayed.
        self.message_label = tk.Label(
            self.status_card,
            text="",
            font=("Arial", 1),
            fg=ERROR_COLOR,
            bg=CARD_BG,
            height=0,
        )

        # -------------------- REQUIREMENTS CARD --------------------
        self.requirements_card = tk.Frame(
            right_stack,
            bg=CARD_BG,
            padx=10,
            pady=7,
            height=150 if self.compact else 210,
        )
        self.requirements_card.pack(side="top", fill="x", pady=(0, 4))
        self.requirements_card.pack_propagate(False)

        self.requirements_title_label = tk.Label(
            self.requirements_card,
            text="Before you scan",
            font=("Arial", 10 if self.compact else 13, "bold"),
            bg=CARD_BG,
            fg=BAR_COLOR,
            anchor="w",
            justify="left",
        )
        self.requirements_title_label.pack(fill="x", pady=(0, 4))

        divider = tk.Frame(self.requirements_card, bg=PANEL_BORDER, height=2)
        divider.pack(fill="x", pady=(0, 5))

        self.check_list_holder = tk.Frame(self.requirements_card, bg=CARD_BG)
        self.check_list_holder.pack(fill="both", expand=True)

        self.build_requirement_rows(MODE_COPY["vegetable"]["requirements"])

        # -------------------- CLEAN MEAT WEIGHT CARD --------------------
        # Compact redesign for the 7-inch screen:
        # fewer labels, no clipped elements, but the same LIVE weight + TARE behavior.
        self.weight_card = tk.Frame(
            right_stack,
            bg="#FFF8F7",
            padx=12,
            pady=5,
            height=124 if self.compact else 150,
            highlightthickness=2,
            highlightbackground=WEIGHT_BORDER,
        )
        self.weight_card.pack_propagate(False)

        weight_header = tk.Frame(self.weight_card, bg="#FFF8F7")
        weight_header.pack(fill="x")

        tk.Label(
            weight_header,
            text="SCALE",
            font=("Arial", 12 if self.compact else 15, "bold"),
            fg=WEIGHT_DARK,
            bg="#FFF8F7",
            anchor="center",
        ).pack(fill="x")

        weight_value_row = tk.Frame(self.weight_card, bg="#FFF8F7")
        weight_value_row.pack(fill="x", pady=(1, 0))

        self.weight_value_label = tk.Label(
            weight_value_row,
            text="0 g",
            font=("Arial", 30 if self.compact else 38, "bold"),
            fg=TEXT_COLOR,
            bg="#FFF8F7",
            anchor="center",
        )
        self.weight_value_label.pack(fill="x")

        self.weight_bar_canvas = tk.Canvas(
            self.weight_card,
            width=self.weight_bar_width,
            height=8 if self.compact else 10,
            bg="#FFF8F7",
            highlightthickness=0,
        )
        self.weight_bar_canvas.pack(pady=(0, 1))

        self.weight_status_label = tk.Label(
            self.weight_card,
            text="Waiting for meat on scale",
            font=("Arial", 7 if self.compact else 9),
            fg=MUTED_TEXT,
            bg="#FFF8F7",
            wraplength=self.sidebar_width - 40,
            justify="center",
        )
        self.weight_status_label.pack(fill="x")

        # -------------------- BUTTON CARD --------------------
        # This area expands, then keeps the action buttons at the bottom.
        # TARE stays above SCAN MEAT. SCAN MEAT stays as the larger bottom button.
        self.button_card = tk.Frame(
            right_stack,
            bg=CARD_BG,
            padx=10,
            pady=0,
        )
        # Do not let this card expand to the bottom.
        # Keeping it directly under the scale/requirements card prevents the buttons
        # from being pushed down and cut off on the 7-inch LCD.
        self.button_card.pack(side="top", fill="x", expand=False, pady=(0, 0))

        self.action_area = tk.Frame(self.button_card, bg=CARD_BG)
        self.action_area.pack(side="top", fill="x", pady=(2, 0))

        self.meat_scale_controls = tk.Frame(self.action_area, bg=CARD_BG)

        self.tare_card, self.tare_label = self.create_action_button(
            self.meat_scale_controls,
            text="TARE SCALE",
            color=WEIGHT_ACCENT,
            hover_color=WEIGHT_DARK,
            border_color=WEIGHT_DARK,
            command=self.tare_weight_scale,
        )
        self.tare_button_width = 190 if self.compact else 215
        self.tare_button_height = 48 if self.compact else 54
        self.tare_card.config(width=self.tare_button_width, height=self.tare_button_height)
        self.tare_label.config(
            font=("Arial", 10 if self.compact else 12, "bold"),
            wraplength=self.tare_button_width - 16,
        )
        self.tare_card.pack(anchor="center")

        # Shift + Enter shortcut is still available, but no visible bypass button is shown.

        self.button_stack = tk.Frame(self.action_area, bg=CARD_BG)
        self.button_stack.pack(side="top", fill="x", pady=(0, 0))

        self.tap_card, self.tap_label = self.create_action_button(
            self.button_stack,
            text="SCAN VEGETABLE",
            color=BUTTON_COLOR,
            hover_color=SCAN_BUTTON_HOVER,
            border_color="#0A4F7A",
            command=lambda: self.perform_capture_and_check(manual=True),
        )
        self.tap_card.pack(anchor="center", pady=(0, 0))

        self.temp_proceed_card, self.temp_proceed_label = self.create_action_button(
            self.button_stack,
            text="PROCEED TO RECIPES",
            color=TEMP_BUTTON_COLOR,
            hover_color=TEMP_BUTTON_HOVER,
            border_color="#1F8E4D",
            command=self.temp_proceed_to_recipe,
        )
        self.temp_proceed_card.pack_forget()

    def build_requirement_rows(self, checks):
        for widget in self.check_list_holder.winfo_children():
            widget.destroy()

        self.check_widgets = {}
        self.check_labels = {}

        for check in checks:
            row = tk.Frame(
                self.check_list_holder,
                bg=NEUTRAL_BG,
                highlightthickness=1,
                highlightbackground="#D8E7ED",
                height=30 if self.compact else 45,
            )
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            icon_label = tk.Label(
                row,
                text="•",
                font=("Arial", 10 if self.compact else 14, "bold"),
                fg=DISABLED_BUTTON_COLOR,
                bg=NEUTRAL_BG,
                width=4,
            )
            icon_label.pack(side="left", fill="y")

            title_label = tk.Label(
                row,
                text=check,
                font=("Arial", 9 if self.compact else 11, "bold"),
                fg=TEXT_COLOR,
                bg=NEUTRAL_BG,
                anchor="w",
                justify="left",
                wraplength=self.sidebar_width - 70,
            )
            title_label.pack(side="left", fill="both", expand=True, padx=(0, 5))

            self.check_widgets[check] = {
                "row": row,
                "icon": icon_label,
                "title": title_label,
            }

            self.check_labels[check] = title_label

    def set_check_state(self, check, state, title_text, sub_text):
        widgets = self.check_widgets.get(check)
        if not widgets:
            return

        if state == "success":
            bg = SUCCESS_BG
            fg = SUCCESS_COLOR
            icon = "OK"
            border = "#BFEBCF"
        elif state == "error":
            bg = WARNING_BG
            fg = ERROR_COLOR
            icon = "NO"
            border = "#F3C1C1"
        else:
            bg = NEUTRAL_BG
            fg = DISABLED_BUTTON_COLOR
            icon = "•"
            border = "#D8E7ED"

        widgets["row"].config(bg=bg, highlightbackground=border)
        widgets["icon"].config(text=icon, fg=fg, bg=bg)
        widgets["title"].config(text=title_text, bg=bg, fg=TEXT_COLOR)

    def show_requirements_card(self):
        if not self.requirements_card.winfo_ismapped():
            self.requirements_card.pack(
                side="top",
                fill="x",
                pady=(0, 4),
                before=self.button_card,
            )

    def hide_requirements_card(self):
        if self.requirements_card.winfo_ismapped():
            self.requirements_card.pack_forget()

    def show_weight_card(self):
        if not self.weight_card.winfo_ismapped():
            self.weight_card.pack(
                side="top",
                fill="x",
                pady=(0, 4),
                before=self.button_card,
            )

    def hide_weight_card(self):
        if self.weight_card.winfo_ismapped():
            self.weight_card.pack_forget()

    def apply_scan_mode_ui(self):
        self.scan_mode = self.get_scan_mode()
        self.load_model_for_mode(self.scan_mode)

        copy = MODE_COPY[self.scan_mode]
        self.current_checks = copy["requirements"]

        self.heading_label.config(text=copy["title"])
        self.draw_mode_pill(self.scan_mode)

        self.set_default_status_text(self.scan_mode)
        self.tap_label.config(text=copy["scan_button"])

        if self.scan_mode == "meat":
            scan_w = 300 if self.compact else 330
            scan_h = 64 if self.compact else 76
            self.tap_card.config(width=scan_w, height=scan_h)
            self.tap_label.config(
                font=("Arial", 16 if self.compact else 19, "bold"),
                wraplength=scan_w - 20,
            )
        else:
            veg_w = 300 if self.compact else 330
            veg_h = 58 if self.compact else 68
            self.tap_card.config(width=veg_w, height=veg_h)
            self.tap_label.config(
                font=("Arial", 14 if self.compact else 17, "bold"),
                wraplength=veg_w - 20,
            )

        self.draw_mode_icon(self.scan_mode)

        self.live_status_label.config(
            text="Make sure the ingredient is well-lit and centered.",
            fg=MUTED_TEXT,
        )
        self.camera_status_label.config(text="Camera starting...")

        self.build_requirement_rows(copy["requirements"])

        self.temp_proceed_card.pack_forget()

        if self.scan_mode == "meat":
            self.hide_requirements_card()
            self.show_weight_card()
            if hasattr(self, "meat_scale_controls") and not self.meat_scale_controls.winfo_ismapped():
                self.meat_scale_controls.pack(fill="x", pady=(0, 4), before=self.button_stack)
            self.start_weight_module()
        else:
            self.stop_weight_module()
            self.hide_weight_card()
            if hasattr(self, "meat_scale_controls") and self.meat_scale_controls.winfo_ismapped():
                self.meat_scale_controls.pack_forget()
            self.show_requirements_card()

    # ==========================================================
    # CAMERA
    # ==========================================================
    def cleanup_camera(self):
        self.running = False
        self.clear_scan_sequence()
        self.stop_weight_module()
        # Do not close the Arduino serial reader here.
        # cleanup_camera() runs during screen/camera reloads.
        # Closing serial here can stop the live weight module while it is still needed.
        # self.stop_real_weight_reader()

        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

        if self.status_reset_after_id:
            try:
                self.after_cancel(self.status_reset_after_id)
            except Exception:
                pass
            self.status_reset_after_id = None

        if self.cap:
            self.cap.release()
            self.cap = None

    def tkraise(self, *args, **kwargs):
        self.cleanup_camera()
        super().tkraise(*args, **kwargs)
        self.apply_scan_mode_ui()
        self.reset_checks()
        self.is_processing = False
        self.after(200, self.start_camera)

    def start_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        # Try normal USB camera indexes first, then any detected /dev/video* devices.
        # This fixes Raspberry Pi cases where there is no /dev/video0 and the camera
        # appears as /dev/video19, /dev/video20, etc.
        camera_candidates = [0, 1, 2]

        try:
            video_paths = sorted(
                glob.glob("/dev/video*"),
                key=lambda path: int(path.replace("/dev/video", ""))
            )
            for path in video_paths:
                try:
                    index = int(path.replace("/dev/video", ""))
                    if index not in camera_candidates:
                        camera_candidates.append(index)
                except Exception:
                    pass
        except Exception:
            pass

        opened = False

        for index in camera_candidates:
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            except Exception:
                cap = cv2.VideoCapture(index)

            if cap is not None and cap.isOpened():
                self.cap = cap
                opened = True
                print(f"Camera opened at /dev/video{index}")
                break

            try:
                cap.release()
            except Exception:
                pass

        if not opened:
            self.camera_status_label.config(text="Camera retrying...")
            self.after(500, self.start_camera)
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

        for _ in range(10):
            self.cap.grab()

        self.running = True
        self.camera_status_label.config(text="Camera active")
        self.update_frame()

    def update_frame(self):
        if not self.running or self.cap is None:
            return

        ret, frame = self.cap.read()

        if ret:
            self.last_frame = frame.copy()
            self.frame_count += 1

            v_w = self.video_container.winfo_width()
            v_h = self.video_container.winfo_height()

            if v_w > 10 and v_h > 10:
                framed = self.prepare_display_frame(frame, v_w, v_h)
                frame_rgb = cv2.cvtColor(framed, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)
                img = ImageTk.PhotoImage(img_pil)
                self.video_label.configure(image=img, text="")
                self.video_label.image = img

        self.after_id = self.after(15, self.update_frame)

    def prepare_display_frame(self, frame, target_width, target_height):
        frame_height, frame_width = frame.shape[:2]

        scale = max(target_width / frame_width, target_height / frame_height)

        resized_width = max(1, int(frame_width * scale))
        resized_height = max(1, int(frame_height * scale))

        resized = cv2.resize(
            frame,
            (resized_width, resized_height),
            interpolation=cv2.INTER_LINEAR,
        )

        x_start = max(0, (resized_width - target_width) // 2)
        y_start = max(0, (resized_height - target_height) // 2)

        cropped = resized[
            y_start:y_start + target_height,
            x_start:x_start + target_width
        ]

        if cropped.shape[0] != target_height or cropped.shape[1] != target_width:
            cropped = cv2.resize(
                cropped,
                (target_width, target_height),
                interpolation=cv2.INTER_LINEAR,
            )

        return cropped

    # ==========================================================
    # DETECTION
    # ==========================================================
    def analyze_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        light_pass = np.mean(gray) >= MIN_BRIGHTNESS

        detections = []

        if self.model is None:
            return light_pass, False, False, [], detections

        results = self.model.predict(
            source=frame,
            conf=CONFIDENCE_THRESHOLD,
            imgsz=YOLO_IMAGE_SIZE,
            max_det=MAX_DETECTIONS,
            verbose=False,
        )

        if results and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                area = float(box.xywh[0][2] * box.xywh[0][3])

                if area < MIN_OBJECT_AREA:
                    continue

                name = self.class_names[int(box.cls[0])]
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                center_x = (x1 + x2) / 2

                detections.append({
                    "name": name,
                    "confidence": confidence,
                    "bbox": (x1, y1, x2, y2),
                    "center_x": center_x,
                    "area": area,
                })

        detections.sort(key=lambda item: (item["center_x"], -item["area"]))

        det_names = []
        seen_names = set()

        for item in detections:
            clean_name = self.normalize_name(item["name"])

            if clean_name not in seen_names:
                det_names.append(clean_name)
                seen_names.add(clean_name)

        obj_pass = len(detections) > 0
        close_pass = obj_pass

        return light_pass, obj_pass, close_pass, det_names, detections

    def analyze_stable_scan_frames(self, mode):
        """Analyze several fresh frames, then combine detections.

        This prevents one-frame misses where a large vegetable like cabbage is detected
        but smaller nearby items like onion, garlic, corn, or potato are ignored.
        """
        frames = []

        if self.last_frame is not None:
            frames.append(self.last_frame.copy())

        # Pull a few fresh frames from the camera for a more stable scan result.
        for _ in range(max(0, SCAN_FRAMES - len(frames))):
            frame = None

            try:
                if self.cap is not None:
                    # Drop one buffered frame first so the captured frame is more current.
                    self.cap.grab()
                    ret, fresh_frame = self.cap.read()
                    if ret and fresh_frame is not None:
                        frame = fresh_frame.copy()
            except Exception:
                frame = None

            if frame is None and self.last_frame is not None:
                frame = self.last_frame.copy()

            if frame is not None:
                frames.append(frame)

            time.sleep(SCAN_FRAME_DELAY)

        if not frames:
            return False, False, False, [], [], None, False

        hit_counts = {}
        best_detection_by_name = {}
        raw_object_seen = False
        any_light_pass = False
        display_frame = frames[-1]

        for frame in frames:
            light_pass, raw_obj_pass, _, _, raw_detections = self.analyze_frame(frame)
            any_light_pass = any_light_pass or light_pass
            raw_object_seen = raw_object_seen or raw_obj_pass

            det_names, mode_detections = self.filter_detections_for_mode(raw_detections, mode)

            for detection in mode_detections:
                clean_name = self.normalize_name(detection.get("name", ""))

                if not clean_name:
                    continue

                hit_counts[clean_name] = hit_counts.get(clean_name, 0) + 1

                previous = best_detection_by_name.get(clean_name)
                previous_conf = float(previous.get("confidence", 0.0)) if previous else -1
                current_conf = float(detection.get("confidence", 0.0))

                if previous is None or current_conf > previous_conf:
                    best_detection_by_name[clean_name] = detection

        accepted_names = [
            name for name, hits in sorted(hit_counts.items())
            if hits >= MIN_HITS_TO_ACCEPT
        ]

        accepted_detections = [
            best_detection_by_name[name]
            for name in accepted_names
            if name in best_detection_by_name
        ]

        obj_pass = len(accepted_detections) > 0
        close_pass = obj_pass

        return (
            any_light_pass,
            obj_pass,
            close_pass,
            accepted_names,
            accepted_detections,
            display_frame,
            raw_object_seen,
        )

    def show_temporary_status(self, text, color, reset_after=1200):
        if self.status_reset_after_id:
            try:
                self.after_cancel(self.status_reset_after_id)
            except Exception:
                pass
            self.status_reset_after_id = None

        self.set_status_subtext(text, color)
        self.live_status_label.config(text=text, fg=color)

        if reset_after:
            mode = self.get_scan_mode()
            self.status_reset_after_id = self.after(
                reset_after,
                lambda m=mode: self.reset_status_text(m),
            )

    def reset_status_text(self, mode=None):
        if mode not in MODE_COPY:
            mode = self.get_scan_mode()

        self.set_default_status_text(mode)

        self.live_status_label.config(
            text="Make sure the ingredient is well-lit and centered.",
            fg=MUTED_TEXT,
        )
        self.status_reset_after_id = None

    def perform_capture_and_check(self, manual=False, is_still=False):
        if self.last_frame is None or self.is_processing or not manual:
            return

        self.clear_scan_sequence()

        if self.model is None:
            mode = self.get_scan_mode()
            model_path = self.get_model_path_for_mode(mode)
            self.show_temporary_status(f"MODEL NOT FOUND: {model_path}", ERROR_COLOR, 1500)
            return

        mode = self.get_scan_mode()

        # Use multiple fresh frames instead of only the current preview frame.
        # This fixes scans that randomly save only 1-2 ingredients.
        (
            light_pass,
            obj_pass,
            close_pass,
            det_names,
            detections,
            frame,
            raw_obj_pass,
        ) = self.analyze_stable_scan_frames(mode)

        if frame is None:
            frame = self.last_frame.copy()

        self.update_indicators(light_pass, obj_pass, close_pass, det_names)

        if not light_pass:
            self.show_temporary_status("LOW LIGHT!", ERROR_COLOR, 1200)
            return

        if raw_obj_pass and not obj_pass:
            wrong_text = MODE_COPY[mode]["wrong"]
            self.show_temporary_status(wrong_text.upper(), ERROR_COLOR, 1500)
            return

        if not obj_pass:
            self.show_temporary_status(MODE_COPY[mode]["none"], ERROR_COLOR, 1200)
            return

        if mode == "meat":
            # Meat + scale guard:
            # 1) The Arduino scale must have actual weight.
            # 2) The current captured frame must have a stronger meat detection.
            # 3) The meat weight must not exceed the 2000g max load.
            # This is only checked when SCAN MEAT is pressed, so the live camera preview remains smooth.
            current_weight_kg = self.get_current_meat_weight_kg()

            if current_weight_kg >= LOAD_CELL_MAX_KG:
                self.show_temporary_status("MAX LOAD REACHED", ERROR_COLOR, 1500)
                return

            if current_weight_kg < MIN_MEAT_WEIGHT_KG_FOR_SCAN:
                self.show_temporary_status("NO WEIGHT ON SCALE", ERROR_COLOR, 1500)
                return

            strong_meat_detections = [
                detection
                for detection in detections
                if float(detection.get("confidence", 0.0)) >= MEAT_SCAN_CONFIRM_CONFIDENCE
            ]

            if not strong_meat_detections:
                self.show_temporary_status("NO MEAT CONFIRMED", ERROR_COLOR, 1500)
                return

            # Use only the stronger confirmed meat detections for saving and overlay.
            det_names, detections = self.filter_detections_for_mode(strong_meat_detections, mode)
            self.save_weight_for_meat(det_names)

        self.execute_capture(frame, det_names, detections)

    def clear_scan_sequence(self):
        for after_id in self.scan_sequence_after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass

        self.scan_sequence_after_ids.clear()
        self.processing_message = None

    def execute_capture(self, frame, names, detections):
        if self.is_processing:
            return

        self.is_processing = True
        captured_frame = self.draw_capture_overlay(frame, detections)
        self.run_scan_sequence(captured_frame, names)

    def run_scan_sequence(self, frame, names):
        mode = self.get_scan_mode()

        # Almost instant scan flow:
        # show only one success message, then immediately proceed.
        # This removes the per-ingredient animation delay that made scanning feel slow.
        if mode == "meat" and names:
            message = f"{', '.join(names)} scanned - {self.get_current_meat_weight_grams()} g"
        elif names:
            message = f"{len(names)} ingredient(s) scanned"
        else:
            message = "Captured successfully."

        self.set_status_subtext(message, SUCCESS_COLOR)
        self.live_status_label.config(text=message, fg=SUCCESS_COLOR)

        self.finish_capture(frame, names)

    def draw_capture_overlay(self, frame, detections):
        annotated = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            name = self.normalize_name(detection["name"])

            cv2.rectangle(
                annotated,
                (x1, y1),
                (x2, y2),
                (22, 128, 228),
                3,
            )

            badge_center = (max(x1 + 24, 24), max(y1 + 24, 24))
            cv2.circle(annotated, badge_center, 18, (39, 174, 96), -1)

            cv2.putText(
                annotated,
                "OK",
                (badge_center[0] - 13, badge_center[1] + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            label_y = max(y1 - 12, 28)

            label_text = name
            if self.get_scan_mode() == "meat":
                label_text = f"{name} {self.get_current_meat_weight_grams()}g"

            cv2.rectangle(
                annotated,
                (x1, label_y - 22),
                (min(x1 + 210, annotated.shape[1] - 10), label_y + 8),
                (13, 103, 145),
                -1,
            )

            cv2.putText(
                annotated,
                label_text,
                (x1 + 8, label_y - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        return annotated

    def finish_capture(self, frame, names):
        """
        Correct flow:
        - Vegetable scan -> ResultScreen -> ScanChoiceScreen
        - Meat scan + weight -> ResultScreen -> RecipeScreen
        """
        mode = self.get_scan_mode()
        self.running = False
        self.controller.captured_frame = frame

        if mode == "meat":
            self.save_weight_for_meat(names)

        # Always append to the existing detected_items list.
        # Old behavior sometimes overwrote the previous list when scan_more was False,
        # which made the app look like it was locked to only the latest 1-2 ingredients.
        existing_items = getattr(self.controller, "detected_items", []) or []
        combined = []

        for item in existing_items:
            clean = self.normalize_name(item)
            if clean and clean not in combined:
                combined.append(clean)

        for item in names:
            clean = self.normalize_name(item)
            if clean and clean not in combined:
                combined.append(clean)

        if not combined:
            self.set_status_subtext("No new ingredients found.", ERROR_COLOR)
            self.live_status_label.config(text="No new ingredients found.", fg=ERROR_COLOR)
            self.is_processing = False
            self.start_camera()
            return

        self.controller.detected_items = combined
        self.controller.detected_item = ", ".join(combined)
        self.controller.scan_more = False

        # ResultScreen reads this and chooses the next screen.
        if mode == "meat":
            self.controller.after_result_target = "recipe"
        else:
            self.controller.after_result_target = "choice"

        self.set_status_subtext("Captured successfully.", SUCCESS_COLOR)
        self.live_status_label.config(text="Captured successfully.", fg=SUCCESS_COLOR)
        self.cleanup_camera()
        self.after(400, self.go_to_results)

    def update_indicators(self, light, obj, close, names):
        mode = self.get_scan_mode()
        copy = MODE_COPY[mode]
        requirements = copy["requirements"]

        self.set_check_state(
            requirements[0],
            "success" if light else "error",
            "Sufficient Light" if light else "Low Light",
            "Lighting is okay" if light else "Move closer to a brighter area",
        )

        self.set_check_state(
            requirements[1],
            "success" if obj else "error",
            copy["detected"] if obj else f"No {copy['detected'].replace(' Detected', '')} Found",
            "Object recognized" if obj else "Place the correct ingredient in view",
        )

        self.set_check_state(
            requirements[2],
            "success" if close else "error",
            f"{len(names)} item(s) ready" if close else copy["in_frame"],
            ", ".join(names) if names else "Center the ingredient inside the frame",
        )

    # ==========================================================
    # NAVIGATION
    # ==========================================================
    def temp_proceed_to_recipe(self):
        if self.get_scan_mode() != "meat":
            return

        existing_items = []

        for item in (getattr(self.controller, "detected_items", []) or []):
            clean = self.normalize_name(item)
            if clean and clean not in existing_items:
                existing_items.append(clean)

        if not existing_items:
            self.show_temporary_status("SCAN A VEGETABLE FIRST", ERROR_COLOR, 1500)
            return

        self.clear_scan_sequence()
        self.is_processing = True
        self.running = False

        if self.last_frame is not None:
            self.controller.captured_frame = self.last_frame.copy()

        self.controller.detected_items = existing_items
        self.controller.detected_item = ", ".join(existing_items)
        self.controller.scan_more = False
        self.controller.after_result_target = "recipe"

        self.set_status_subtext("Proceeding to recipes...", SUCCESS_COLOR)
        self.live_status_label.config(text="Proceeding to recipes...", fg=SUCCESS_COLOR)

        self.cleanup_camera()
        self.after(300, self.go_to_recipe_screen)

    def go_to_recipe_screen(self):
        target_name = "RecipeScreen"

        for screen_class, frame in self.controller.frames.items():
            if target_name in str(screen_class):
                self.controller.recipe_mode = "region"

                if hasattr(frame, "current_mode"):
                    frame.current_mode = "region"

                self.controller.show_frame(screen_class)
                break

    def go_to_results(self):
        target_name = "ResultScreen"

        for screen_class in self.controller.frames.keys():
            if target_name in str(screen_class):
                self.controller.show_frame(screen_class)
                break

    # ==========================================================
    # RESET
    # ==========================================================
    def reset_checks(self):
        mode = self.get_scan_mode()

        self.set_default_status_text(mode)

        self.live_status_label.config(
            text="Make sure the ingredient is well-lit and centered.",
            fg=MUTED_TEXT,
        )

        for check in self.current_checks:
            self.set_check_state(
                check,
                "neutral",
                check,
                "Waiting for scan",
            )

        if mode == "meat":
            self.hide_requirements_card()
            self.show_weight_card()
            self.start_weight_module()
        else:
            self.stop_weight_module()
            self.hide_weight_card()
            self.show_requirements_card()

    def reset_screen(self):
        self.clear_scan_sequence()
        self.cleanup_camera()

        self.last_frame = None
        self.is_processing = False
        self.frame_count = 0
        self.latest_preview_names = []
        self.latest_preview_count = 0

        self.reset_checks()