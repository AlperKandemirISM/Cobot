import tkinter as tk
import math


class AngleKnob(tk.Canvas):
    """Interactive 360-degree knob widget for servo control"""

    def __init__(self, parent, size=250, **kwargs):
        super().__init__(parent, width=size, height=size, bg="#f0f0f0", highlightthickness=0, **kwargs)

        self.size = size
        self.center = size // 2
        self.radius = (size - 40) // 2
        self.current_angle = 0
        self.dragging = False
        self.last_update_time = 0
        self.on_angle_change = None  # Callback for angle changes

        self.draw_knob()

        # Mouse bindings
        self.bind("<Button-1>", self.on_mouse_down)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<ButtonRelease-1>", self.on_mouse_up)

    def set_angle_change_callback(self, callback):
        """Set callback for when angle changes"""
        self.on_angle_change = callback

    def draw_knob(self):
        """Draw the knob interface"""
        self.delete("all")

        # Outer circle
        self.create_oval(
            self.center - self.radius - 10,
            self.center - self.radius - 10,
            self.center + self.radius + 10,
            self.center + self.radius + 10,
            outline="#333", width=3, fill="#e0e0e0"
        )

        # Inner circle
        self.create_oval(
            self.center - self.radius,
            self.center - self.radius,
            self.center + self.radius,
            self.center + self.radius,
            outline="#666", width=2, fill="#ffffff"
        )

        # Draw major tick marks every 30°
        for angle in range(0, 360, 30):
            self.draw_tick(angle, length=15, width=2)
            # Label major angles
            self.draw_angle_label(angle)

        # Draw minor tick marks every 10°
        for angle in range(0, 360, 10):
            if angle % 30 != 0:
                self.draw_tick(angle, length=8, width=1)

        # Center dot
        self.create_oval(
            self.center - 5, self.center - 5,
            self.center + 5, self.center + 5,
            fill="#333", outline=""
        )

        # Draw pointer
        self.draw_pointer()

    def draw_tick(self, angle, length=10, width=1):
        """Draw a tick mark at specified angle"""
        rad = math.radians(angle - 90)  # -90 to start at top

        x1 = self.center + (self.radius - length) * math.cos(rad)
        y1 = self.center + (self.radius - length) * math.sin(rad)
        x2 = self.center + self.radius * math.cos(rad)
        y2 = self.center + self.radius * math.sin(rad)

        self.create_line(x1, y1, x2, y2, fill="#333", width=width)

    def draw_angle_label(self, angle):
        """Draw angle label"""
        rad = math.radians(angle - 90)
        label_radius = self.radius + 20

        x = self.center + label_radius * math.cos(rad)
        y = self.center + label_radius * math.sin(rad)

        self.create_text(x, y, text=f"{angle}°", font=("Arial", 10, "bold"), fill="#333")

    def draw_pointer(self):
        """Draw the pointer showing current angle"""
        self.delete("pointer")

        rad = math.radians(self.current_angle - 90)

        # Pointer line
        x = self.center + (self.radius - 20) * math.cos(rad)
        y = self.center + (self.radius - 20) * math.sin(rad)

        self.create_line(
            self.center, self.center, x, y,
            fill="#ff0000", width=3, arrow=tk.LAST,
            tags="pointer"
        )

        # Angle text in center
        self.create_text(
            self.center, self.center + 30,
            text=f"{self.current_angle:.1f}°",
            font=("Arial", 14, "bold"),
            fill="#ff0000",
            tags="pointer"
        )

    def set_angle(self, angle):
        """Update knob to show specified angle"""
        self.current_angle = angle % 360
        self.draw_pointer()

    def get_angle_from_mouse(self, event):
        """Calculate angle from mouse position"""
        dx = event.x - self.center
        dy = event.y - self.center

        angle = math.degrees(math.atan2(dy, dx)) + 90
        if angle < 0:
            angle += 360

        return angle % 360

    def on_mouse_down(self, event):
        """Start dragging"""
        self.dragging = True
        self.on_mouse_drag(event)

    def on_mouse_drag(self, event):
        """Handle dragging to set angle"""
        if not self.dragging:
            return

        angle = self.get_angle_from_mouse(event)
        self.set_angle(angle)

        # Rate limit angle change callbacks (every 100ms)
        import time
        current_time = time.time()
        if current_time - self.last_update_time > 0.1:
            self.last_update_time = current_time
            if self.on_angle_change:
                self.on_angle_change(angle)

    def on_mouse_up(self, event):
        """Stop dragging"""
        self.dragging = False


class ServoControllerGUI:
    """GUI for ST3215 Servo Control"""

    def __init__(self, root, callbacks):
        """
        Initialize the GUI

        Args:
            root: tkinter root window
            callbacks: Dictionary of callback functions
        """
        self.root = root
        self.callbacks = callbacks

        # Widget references
        self.knob_widget = None
        self.angle_input_cw = None
        self.angle_input_ccw = None
        self.increment_input = None
        self.speed_label = None
        self.speed_slider = None
        self.status_label = None
        self.direction_label = None
        self.position_label = None
        self.actual_speed_label = None
        self.temp_label = None
        self.voltage_label = None
        self.current_label = None
        self.load_label = None
        self.moving_label = None

        self.setup_gui()

    def setup_gui(self):
        """Set up the complete GUI layout"""
        self.root.title("ST3215 Servo Control")
        self.root.geometry("1400x700")
        self.root.configure(bg="#f0f0f0")

        # Title
        title_label = tk.Label(self.root, text="ST3215 Servo Controller",
                               font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Status
        self.status_label = tk.Label(self.root, text="Initializing...",
                                     font=("Arial", 12), bg="#f0f0f0")
        self.status_label.grid(row=1, column=0, columnspan=3, pady=5)

        # Direction
        self.direction_label = tk.Label(self.root, text="Direction: STOPPED",
                                        font=("Arial", 14, "bold"), fg="gray", bg="#f0f0f0")
        self.direction_label.grid(row=2, column=0, columnspan=3, pady=5)

        # Create left, middle, and right frames
        self.setup_left_frame()
        self.setup_middle_frame()
        self.setup_right_frame()

    def setup_left_frame(self):
        """Set up left control panel"""
        left_frame = tk.Frame(self.root, bg="#f0f0f0")
        left_frame.grid(row=3, column=0, padx=20, sticky="n")

        # Speed control
        self.speed_label = tk.Label(left_frame, text=f"Speed: 10%",
                                    font=("Arial", 16), bg="#f0f0f0")
        self.speed_label.pack(pady=5)

        slider_frame = tk.Frame(left_frame, bg="#f0f0f0")
        slider_frame.pack(pady=10)

        tk.Label(slider_frame, text="10%", font=("Arial", 10), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        self.speed_slider = tk.Scale(slider_frame, from_=10, to=100, orient=tk.HORIZONTAL,
                                     length=200, command=self.callbacks.get('on_slider_change'), bg="#f0f0f0")
        self.speed_slider.set(10)
        self.speed_slider.pack(side=tk.LEFT)
        tk.Label(slider_frame, text="100%", font=("Arial", 10), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)

        speed_btn_frame = tk.Frame(left_frame, bg="#f0f0f0")
        speed_btn_frame.pack(pady=5)

        decrease_btn = tk.Button(speed_btn_frame, text="- 10%", font=("Arial", 14),
                                 command=self.callbacks.get('decrease_speed'), width=8, bg="#ffcccc")
        decrease_btn.pack(side=tk.LEFT, padx=5)

        increase_btn = tk.Button(speed_btn_frame, text="+ 10%", font=("Arial", 14),
                                 command=self.callbacks.get('increase_speed'), width=8, bg="#ccffcc")
        increase_btn.pack(side=tk.LEFT, padx=5)

        # Direction control frames
        control_frame = tk.Frame(left_frame, bg="#f0f0f0")
        control_frame.pack(pady=10)

        # CCW Frame
        ccw_frame = tk.LabelFrame(control_frame, text="Counter-Clockwise",
                                  font=("Arial", 12, "bold"), bg="#f0f0f0",
                                  fg="#ff8c00", padx=10, pady=10)
        ccw_frame.grid(row=0, column=0, padx=10, pady=5, sticky="n")

        ccw_btn = tk.Button(ccw_frame, text="← CCW", font=("Arial", 14, "bold"),
                            command=self.callbacks.get('move_ccw'), width=15, height=2, bg="#ffa500", fg="white")
        ccw_btn.pack(pady=5)

        tk.Label(ccw_frame, text="Go to Angle:", font=("Arial", 10), bg="#f0f0f0").pack(pady=(10, 2))
        self.angle_input_ccw = tk.Entry(ccw_frame, font=("Arial", 12), width=10, justify="center")
        self.angle_input_ccw.pack()
        self.angle_input_ccw.insert(0, "180")
        go_angle_ccw_btn = tk.Button(ccw_frame, text="Go", font=("Arial", 11),
                                     command=self.callbacks.get('go_to_angle_ccw'), width=12, bg="#ffb347")
        go_angle_ccw_btn.pack(pady=5)

        tk.Label(ccw_frame, text="Increment:", font=("Arial", 10), bg="#f0f0f0").pack(pady=(10, 2))
        ccw_inc_frame = tk.Frame(ccw_frame, bg="#f0f0f0")
        ccw_inc_frame.pack()
        ccw_dec_btn = tk.Button(ccw_inc_frame, text="−", font=("Arial", 14, "bold"),
                                command=self.callbacks.get('decrement_angle_ccw'), width=3, bg="#ffcccc")
        ccw_dec_btn.pack(side=tk.LEFT, padx=2)
        ccw_inc_btn = tk.Button(ccw_inc_frame, text="+", font=("Arial", 14, "bold"),
                                command=self.callbacks.get('increment_angle_ccw'), width=3, bg="#ccffcc")
        ccw_inc_btn.pack(side=tk.LEFT, padx=2)

        # CW Frame
        cw_frame = tk.LabelFrame(control_frame, text="Clockwise",
                                 font=("Arial", 12, "bold"), bg="#f0f0f0",
                                 fg="#4169e1", padx=10, pady=10)
        cw_frame.grid(row=0, column=1, padx=10, pady=5, sticky="n")

        cw_btn = tk.Button(cw_frame, text="CW ➜", font=("Arial", 14, "bold"),
                           command=self.callbacks.get('move_cw'), width=15, height=2, bg="#4169e1", fg="white")
        cw_btn.pack(pady=5)

        tk.Label(cw_frame, text="Go to Angle:", font=("Arial", 10), bg="#f0f0f0").pack(pady=(10, 2))
        self.angle_input_cw = tk.Entry(cw_frame, font=("Arial", 12), width=10, justify="center")
        self.angle_input_cw.pack()
        self.angle_input_cw.insert(0, "90")
        go_angle_cw_btn = tk.Button(cw_frame, text="Go", font=("Arial", 11),
                                    command=self.callbacks.get('go_to_angle_cw'), width=12, bg="#6495ed")
        go_angle_cw_btn.pack(pady=5)

        tk.Label(cw_frame, text="Increment:", font=("Arial", 10), bg="#f0f0f0").pack(pady=(10, 2))
        cw_inc_frame = tk.Frame(cw_frame, bg="#f0f0f0")
        cw_inc_frame.pack()
        cw_dec_btn = tk.Button(cw_inc_frame, text="−", font=("Arial", 14, "bold"),
                               command=self.callbacks.get('decrement_angle_cw'), width=3, bg="#ffcccc")
        cw_dec_btn.pack(side=tk.LEFT, padx=2)
        cw_inc_btn = tk.Button(cw_inc_frame, text="+", font=("Arial", 14, "bold"),
                               command=self.callbacks.get('increment_angle_cw'), width=3, bg="#ccffcc")
        cw_inc_btn.pack(side=tk.LEFT, padx=2)

        # Increment control
        increment_frame = tk.Frame(left_frame, bg="#f0f0f0")
        increment_frame.pack(pady=10)
        tk.Label(increment_frame, text="Increment (degrees):",
                 font=("Arial", 11, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        self.increment_input = tk.Entry(increment_frame, font=("Arial", 12), width=8, justify="center")
        self.increment_input.pack(side=tk.LEFT)
        self.increment_input.insert(0, "10")

        # Tools frame
        tools_frame = tk.Frame(left_frame, bg="#f0f0f0")
        tools_frame.pack(pady=10)

        debug_btn = tk.Button(tools_frame, text="Debug", font=("Arial", 10),
                              command=self.callbacks.get('debug_position'), width=8, bg="#e0e0e0")
        debug_btn.pack(side=tk.LEFT, padx=2)

        # Stop button
        stop_btn = tk.Button(left_frame, text="STOP", font=("Arial", 18, "bold"),
                             command=self.callbacks.get('stop_servo'), width=25, height=2,
                             bg="#dc143c", fg="white")
        stop_btn.pack(pady=20)

    def setup_middle_frame(self):
        """Set up middle knob control"""
        middle_frame = tk.LabelFrame(self.root, text="Visual Angle Control",
                                     font=("Arial", 14, "bold"), bg="#f0f0f0",
                                     padx=10, pady=10)
        middle_frame.grid(row=3, column=1, padx=20, sticky="n")

        self.knob_widget = AngleKnob(middle_frame, size=280)
        self.knob_widget.pack(pady=10)

        knob_label = tk.Label(middle_frame, text="Drag the knob to set servo angle",
                              font=("Arial", 10, "italic"), bg="#f0f0f0", fg="#666")
        knob_label.pack(pady=5)

    def setup_right_frame(self):
        """Set up right telemetry panel"""
        right_frame = tk.LabelFrame(self.root, text="Real-Time Telemetry",
                                    font=("Arial", 14, "bold"), bg="#f0f0f0",
                                    padx=20, pady=20)
        right_frame.grid(row=3, column=2, padx=20, sticky="n")

        self.position_label = tk.Label(right_frame, text="Position: --",
                                       font=("Arial", 13), bg="#f0f0f0", anchor="w", width=30)
        self.position_label.pack(pady=8)

        self.actual_speed_label = tk.Label(right_frame, text="Actual Speed: --",
                                           font=("Arial", 13), bg="#f0f0f0", anchor="w", width=30)
        self.actual_speed_label.pack(pady=8)

        self.temp_label = tk.Label(right_frame, text="Temperature: --°C",
                                   font=("Arial", 13), bg="#f0f0f0", anchor="w", width=30)
        self.temp_label.pack(pady=8)

        self.voltage_label = tk.Label(right_frame, text="Voltage: --V",
                                      font=("Arial", 13), bg="#f0f0f0", anchor="w", width=30)
        self.voltage_label.pack(pady=8)

        self.current_label = tk.Label(right_frame, text="Current: --mA",
                                      font=("Arial", 13), bg="#f0f0f0", anchor="w", width=30)
        self.current_label.pack(pady=8)

        self.load_label = tk.Label(right_frame, text="Load: --%",
                                   font=("Arial", 13), bg="#f0f0f0", anchor="w", width=30)
        self.load_label.pack(pady=8)

        self.moving_label = tk.Label(right_frame, text="Moving: --",
                                     font=("Arial", 13), bg="#f0f0f0", anchor="w", width=30)
        self.moving_label.pack(pady=8)

    def get_cw_angle(self):
        """Get angle from CW input field"""
        return self.angle_input_cw.get()

    def get_ccw_angle(self):
        """Get angle from CCW input field"""
        return self.angle_input_ccw.get()

    def get_increment(self):
        """Get increment value"""
        return self.increment_input.get()

    def update_speed_display(self, speed_percent):
        """Update speed display"""
        self.speed_label.config(text=f"Speed: {speed_percent}%")

    def update_status(self, text, fg="black"):
        """Update status label"""
        self.status_label.config(text=text, fg=fg)

    def update_direction(self, text, fg="gray"):
        """Update direction label"""
        self.direction_label.config(text=text, fg=fg)

    def update_telemetry(self, telemetry_data):
        """Update all telemetry displays"""
        if 'position' in telemetry_data:
            pos = telemetry_data['position']
            angle = telemetry_data.get('angle', (pos / 4096.0) * 360.0)
            self.position_label.config(text=f"Position: {pos} ({angle:.1f}°)")

        if 'speed' in telemetry_data:
            self.actual_speed_label.config(text=f"Actual Speed: {telemetry_data['speed']}")

        if 'temp' in telemetry_data:
            self.temp_label.config(text=f"Temperature: {telemetry_data['temp']}°C")

        if 'voltage' in telemetry_data:
            self.voltage_label.config(text=f"Voltage: {telemetry_data['voltage'] / 10:.1f}V")

        if 'current' in telemetry_data:
            self.current_label.config(text=f"Current: {telemetry_data['current']}mA")

        if 'load' in telemetry_data:
            self.load_label.config(text=f"Load: {telemetry_data['load']}%")

        if 'moving' in telemetry_data:
            moving = telemetry_data['moving']
            self.moving_label.config(text=f"Moving: {'YES' if moving else 'NO'}",
                                     fg="green" if moving else "gray")

    def set_knob_angle(self, angle):
        """Set knob angle"""
        if self.knob_widget:
            self.knob_widget.set_angle(angle)

    def set_knob_callback(self, callback):
        """Set callback for knob angle changes"""
        if self.knob_widget:
            self.knob_widget.set_angle_change_callback(callback)