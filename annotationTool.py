import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import os
from util import extract_video_properties, find_slopes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from scipy.signal import find_peaks
from components import ChargeCalculator
from tkinter.ttk import Progressbar

class MillikanExperimentApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Millikan Experiment")

        self.charge_calculator = ChargeCalculator()

        # Video and Tracker Variables
        self.video = None
        self.tracker = cv2.TrackerCSRT_create()
        self.current_frame = 0
        self.total_frames = 0
        self.frame_width = 0
        self.frame_height = 0
        self.display_width = 512 
        self.display_height = 512

        self.roi_selection = False
        self.bbox = None
        self.bbox_history = {}
        self.start_x = self.start_y = self.end_x = self.end_y = 0

        self.paused = True
        self.video_path = None
        self.output_path = None
        self.canvas_image = None
        self.video_directory = "input" 

        self.y_centers = []

        # GUI Layout

        # Progress Bar Frame
        self.progress_frame = tk.Frame(root, bg="white")  # Create a new frame for the progress bar
        self.progress_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)  # Pack it at the top of the root window

        self.progress_bar = Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate', length=self.display_width)
        self.progress_bar.pack(fill=tk.X, pady=5) 

        # Left Frame for loading videos
        self.left_frame = tk.Frame(root, width=200, bg="lightgray")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.video_listbox = tk.Listbox(self.left_frame, width=30)
        self.video_listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.load_videos_button = tk.Button(self.left_frame, text="Load Videos", command=self.load_videos)
        self.load_videos_button.pack(pady=5)

        self.select_video_button = tk.Button(self.left_frame, text="Select Video", command=self.select_video)
        self.select_video_button.pack(pady=5)

        # Right Frame for the 2x2 grid
        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side=tk.TOP, fill=tk.BOTH)

        # Video display and controls (Top Left)
        self.video_container = tk.Frame(self.right_frame)
        self.video_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Video Canvas
        self.video_canvas = tk.Canvas(self.video_container, width=self.display_width, height=self.display_height, bg="black")
        self.video_canvas.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Controls Frame
        self.controls_frame = tk.Frame(self.video_container)
        self.controls_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ns")

        # Video Control Buttons (stacked vertically in the controls frame)
        self.play_button = tk.Button(self.controls_frame, text="Play", command=self.play_video, state=tk.DISABLED)
        self.play_button.pack(fill=tk.X, pady=5)

        self.pause_button = tk.Button(self.controls_frame, text="Pause", command=self.pause_video, state=tk.DISABLED)
        self.pause_button.pack(fill=tk.X, pady=5)

        self.forward_button = tk.Button(self.controls_frame, text="Forward", command=self.move_forward, state=tk.DISABLED)
        self.forward_button.pack(fill=tk.X, pady=5)

        self.backward_button = tk.Button(self.controls_frame, text="Backward", command=self.move_backward, state=tk.DISABLED)
        self.backward_button.pack(fill=tk.X, pady=5)

        # Slider for video scrubbing
        self.slider = tk.Scale(
            self.video_container,
            from_=0,
            to=0,  # This will be updated when a video is loaded
            orient=tk.HORIZONTAL,
            length=self.display_width,
            command=self.on_slider_update
        )
        self.slider.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")


        # Instructions (Top Right)
        self.instructions_label = tk.Label(self.right_frame, text="Instructions: \n1. Load videos\n2. Select a video\n3. Play or analyze", bg="white", anchor="nw", justify="left")
        self.instructions_label.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Chart (Bottom Left)
        self.chart_frame = tk.Frame(self.right_frame)
        self.chart_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.figure = Figure(figsize=(4, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Y-Center Data")
        self.ax.set_xlabel("Frame Index")
        self.ax.set_ylabel("Y-Center")
        self.chart_canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Charge Prediction Label
        self.prediction_label = tk.Label(self.right_frame, text="Charge Prediction:\nN/A", bg="lightblue", anchor="nw", justify="left")
        self.prediction_label.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Configure row and column weights for dynamic resizing
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=1)

        # Configure the layout for dynamic resizing
        self.video_container.grid_rowconfigure(0, weight=1)  # Video canvas and controls
        self.video_container.grid_rowconfigure(1, weight=0)  # Slider
        self.video_container.grid_columnconfigure(0, weight=1)  # Video canvas
        self.video_container.grid_columnconfigure(1, weight=0)  # Controls frame

    def load_videos(self):
        """Load video files from the directory into the Listbox."""
        self.video_listbox.delete(0, tk.END)
        if not os.path.exists(self.video_directory):
            os.makedirs(self.video_directory)
        videos = [f for f in os.listdir(self.video_directory) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
        for video in videos:
            self.video_listbox.insert(tk.END, video)

    def select_video(self):
        """Handle video selection from the Listbox."""
        selected_index = self.video_listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No video selected.")
            return

        selected_video = self.video_listbox.get(selected_index)
        self.video_path = os.path.join(self.video_directory, selected_video)

        # Set up video properties
        self.video = cv2.VideoCapture(self.video_path)
        if not self.video.isOpened():
            messagebox.showerror("Error", f"Could not open video {self.video_path}")
            return

        # Extract video properties
        self.total_frames, self.frame_width, self.frame_height = extract_video_properties(self.video)

        # Prepare output directory
        base_name = os.path.basename(self.video_path).split('.')[0]
        self.output_path = os.path.join('output', base_name)
        os.makedirs(self.output_path, exist_ok=True)

        # Enable controls
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.NORMAL)
        self.forward_button.config(state=tk.NORMAL)
        self.backward_button.config(state=tk.NORMAL)

        # Read the first frame
        ret, self.frame = self.video.read()
        if ret:
            self.current_frame = 0
            self.frame = cv2.resize(self.frame, (self.display_width, self.display_height))
            self.display_frame(self.frame)

            self.slider.config(to=self.total_frames - 1)  # Set slider range
            self.slider.set(self.current_frame)

            # Bind Mouse Event Listeners to Canvas
            self.video_canvas.bind("<ButtonPress-1>", self.on_mouse_down)
            self.video_canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.video_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        else:
            messagebox.showerror("Error", "Could not read the first frame of the video")

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.roi_selection = True

    def on_mouse_drag(self, event):
        if self.roi_selection:
            self.end_x = event.x
            self.end_y = event.y
            self.video_canvas.delete("roi")
            self.video_canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="blue", tag="roi")

    def on_mouse_up(self, event):
        if self.roi_selection:
            self.end_x = event.x
            self.end_y = event.y
            self.roi_selection = False
            self.bbox = (self.start_x, self.start_y, self.end_x - self.start_x, self.end_y - self.start_y)
            self.bbox
            self.tracker.init(self.frame, self.bbox)
            self.bbox_history[self.current_frame] = self.bbox

            # Remove the slider when ROI is drawn
            self.slider.pack_forget()
            self.slider.destroy()
            self.slider = None  # Remove the reference to the slider

    def play_video(self):
        self.video_canvas.delete("roi")
        self.paused = False
        self.update_video_frame()

    def pause_video(self):
        self.paused = True

    def update_video_frame(self):
        if self.paused or not self.video.isOpened():
            return

        ret, self.frame = self.video.read()
        if not ret:
            messagebox.showinfo("End of Video", "Video playback completed")
            return

        self.frame = cv2.resize(self.frame, (self.display_width, self.display_height))
        self.current_frame += 1
        ret, bbox = self.tracker.update(self.frame)
        if ret:
            self.bbox_history[self.current_frame] = bbox
            self.save_yolo_format(self.current_frame, bbox, self.display_width, self.display_height, self.output_path)
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(self.frame, p1, p2, (255, 0, 0), 2, 1)

        
        self.display_frame(self.frame)

        # Update the progress bar
        progress = (self.current_frame / self.total_frames) * 100
        self.progress_bar['value'] = progress

        self.root.after(10, self.update_video_frame)

    def save_yolo_format(self, frame_num, bbox, img_width, img_height, base_output_path):
        x_center = (bbox[0] + bbox[2] / 2) / img_width
        y_center = (bbox[1] + bbox[3] / 2) / img_height
        width = bbox[2] / img_width
        height = bbox[3] / img_height

        self.y_centers.append(y_center)

        # output_path = os.path.join(base_output_path, f"{frame_num:06d}.txt")
        # with open(output_path, 'w') as file:
        #     file.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

        self.update_chart()

    def update_chart(self):
        """Find and plot peaks and troughs in y-center data, ensuring the first and last data points are treated as specified."""
        # Convert list to numpy array for processing
        y = np.array(self.y_centers) * 512  # Scaling to pixel values
        t = np.arange(len(self.y_centers))  # Time indices

        # Finding peaks and troughs
        peaks, _ = find_peaks(y, distance=100, prominence=100)
        troughs, _ = find_peaks(-y, distance=100, prominence=100)

        # Enforce the first and last frame conditions
        # First frame is always a min
        if 0 not in troughs:
            troughs = np.append([0], troughs)

        # Last frame is opposite of the last detected peak or trough
        if len(peaks) > 0 and len(troughs) > 0:
            if peaks[-1] > troughs[-1]:  # Last detected was a peak
                if len(y) - 1 not in troughs:
                    troughs = np.append(troughs, [len(y) - 1])
            else:  # Last detected was a trough
                if len(y) - 1 not in peaks:
                    peaks = np.append(peaks, [len(y) - 1])

        # Create lists of tuples for peaks and troughs
        peak_points = [(t[index], y[index]) for index in peaks]
        trough_points = [(t[index], y[index]) for index in troughs]

        try:
            vu, vd = find_slopes(peak_points, trough_points)
            charge, interval = self.charge_calculator.find_charge_and_interval(vu, vd)
            self.prediction_label.config(
                text=f"Charge Prediction:\nCharge: {charge:.5e} C\nInterval: {interval:.2f} e"
            )
        except ValueError as e:
            self.prediction_label.config(text=f"Error in calculation: {str(e)}")

        # Plotting
        self.ax.clear()
        self.ax.set_title('Detected Peaks and Troughs in Y-Center Data')
        self.ax.set_xlabel('Frame Index')
        self.ax.set_ylabel('Y-Center Value')
        self.ax.grid(True)
        self.ax.plot(t, y, label='Y-Center Data', color='black')
        self.ax.plot(t[peaks], y[peaks], 'x', label='Peaks', color='blue')
        self.ax.plot(t[troughs], y[troughs], 'bo', label='Troughs')
        self.ax.invert_yaxis()  # Invert the y-axis
        self.chart_canvas.draw()

    def display_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        if self.canvas_image is None:
            self.canvas_image = self.video_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        else:
            self.video_canvas.itemconfig(self.canvas_image, image=imgtk)
        self.video_canvas.image = imgtk

    def move_forward(self):
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.video.read()
            if ret:
                frame = cv2.resize(frame, (self.display_width, self.display_height))
                bbox = self.bbox_history.get(self.current_frame, None)
                if bbox:
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                self.display_frame(frame)

    def move_backward(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.video.read()
            if ret:
                frame = cv2.resize(frame, (self.display_width, self.display_height))
                bbox = self.bbox_history.get(self.current_frame, None)
                if bbox:
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                self.display_frame(frame)

    def on_slider_update(self, value):
        if not self.slider:
            return 
        
        if self.video and not self.paused:  # Pause video if it's playing
            self.paused = True
        self.current_frame = int(value)
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.video.read()
        if ret:
            frame = cv2.resize(frame, (self.display_width, self.display_height))
            bbox = self.bbox_history.get(self.current_frame, None)
            if bbox:
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
            self.display_frame(frame)

if __name__ == "__main__":
    root = tk.Tk()
    app = MillikanExperimentApp(root)
    root.mainloop()
