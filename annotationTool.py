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
from math import cos, sin

class MillikanExperimentApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Millikan Experiment")
        self.current_page = 0 
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
        self.charge_interval_pairs = []

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
        self.right_frame.pack(side=tk.TOP, fill=tk.Y)

        # Video display and controls (Top Left)
        self.video_container = tk.Frame(self.right_frame)
        self.video_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Video Canvas
        self.video_canvas = tk.Canvas(self.video_container, width=self.display_width, height=self.display_height)
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

        self.fast_forward_button = tk.Button(self.controls_frame, text="Fast Forward", command=self.move_fast_forward, state=tk.DISABLED)
        self.fast_forward_button.pack(fill=tk.X, pady=5)

        self.fast_backward_button = tk.Button(self.controls_frame, text="Fast Backward", command=self.move_fast_backward, state=tk.DISABLED)
        self.fast_backward_button.pack(fill=tk.X, pady=5)

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




        ##################################################
        # Instructions Frame (Container for instructions and buttons)
        self.instructions_frame = tk.Frame(self.right_frame, bg="white")
        self.instructions_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Configure the layout for instructions_frame
        self.instructions_frame.grid_rowconfigure(0, weight=1)  # Instructions text
        self.instructions_frame.grid_rowconfigure(1, weight=1)  # Image row
        self.instructions_frame.grid_rowconfigure(2, weight=0)  # Empty row for padding (optional)
        self.instructions_frame.grid_rowconfigure(3, weight=0)  # Buttons row
        self.instructions_frame.grid_columnconfigure(0, weight=1)  # For centering elements
        self.instructions_frame.grid_columnconfigure(1, weight=1)  # To position "Next" properly

        # Instructions Label
        self.instructions_label = tk.Label(
            self.instructions_frame,
            text="Instructions: \n1. Load videos\n2. Select a video\n3. Play or analyze",
            bg="white",
            anchor="nw",
            justify="left",
            wraplength=600 # Adjust for better text wrapping
        )
        self.instructions_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        
        ###########################
        # Add visual element (Image)
        self.add_visual_element()
        # Add eq 1
        self.add_equation_widget()
        # Add eq 2 
        self.add_equation_widget2()
        # Add eq 3
        self.add_equation_widget3()
        # Add eq 4
        self.add_equation_widget4()
        # Add eq 5
        self.add_equation_widget5()
        ###########################

        # Back Button (bottom-left of instructions grid)
        self.back_button = tk.Button(self.instructions_frame, text="Back", command=self.back_action, state=tk.DISABLED)
        self.back_button.grid(row=3, column=0, sticky="w", padx=5, pady=5)

        # Next Button (bottom-right of instructions grid)
        self.next_button = tk.Button(self.instructions_frame, text="Next", command=self.next_action)
        self.next_button.grid(row=3, column=1, sticky="e", padx=5, pady=5)
        
        # Page content
        self.pages = [
            "Welcome! This application is designed to facilitate the prediction of electrical charge.\n\n"
            "This experiment was originally conducted by Robert A. Millikan in 1909. The Millikan Oil Drop\n "
            "Experiment is a classic physics experiment designed to measure the charge of an electron.\n "
            "Millikan achieved this by suspending tiny charged oil droplets in an electric field and\n "
            "analyzing their motion.\n\n"
            "Illustrated below is an example of the apparatus used by Millikan to suspend microscopic oil droplets. The motion of these droplets could be carefully controlled, allowing them to rise under the influence of an electric field or fall due to the force of gravity.\n\n"
            "Oil droplets are sprayed into a chamber between two closely spaced horizontal plates. These plates are insulated and connected to a voltage source. A potential difference across the plates creates an electric field, which can balance the downward force of gravity on the charged droplets, holding them stationary.\n\n"
            "Click the Next button to Continue.",
            
            "These tiny oil-dropleps viewed through a microscope are under the influence different forces when rising or falling.\n\n"
            "1) Forces Acting on the droplet. \n\n"
            "When the droplet is falling, the forces acting on it can be balanced as follows: \n\n\n\n\n\n\n\n"
            "Where: V(t) is the terminal velocity of the falling droplet, r is the radius of the droplet, η is the viscosity of air, ρ oil density of the oil, ρ air is the density of the air, and g is gravity.\n\n"
            "The radius of the droplet is calculated using: \n\n\n\n\n\n\n\n\n"
            "Click the Next button to Continue.",
            
            "2) Forces During the Droplets Ascent\n\n"
            "When the droplet rises under the influence of the electric field, the forces balance differently. The electric force must overcome both gravity and drag: \n\n\n\n\n\n\n"
            "Where: V(r) is the rising velocity of the droplet, and E is the electric field strength.\n\n"
            
            
            "Using the relationship E = V / d, this becomes:\n\n\n\n\n\n\n\n\n"
            "From this, the charge q is determined:\n\n\n\n\n\n\n\n\n"
            "Click the Next button to Continue.",
            
            "Computing Electrical Charge.\n\n"
            "As noted by the final equation, there are many variables to be accounted for in order to calculate q, the charge of an oil-droplet in Coulombs.\n\n"
            "Given that this application is meant to be used with the MillikanCV dataset, we have all the variables needed to compute electrical charge.\n\n"
            "Voltage (V) = 500 volts\n\n"
            "Distance (d) = 4.902 mm \n\n"
            
            
            
            
            
            
            
            "As part of this application, the developers have compiled a dataset of over a hundred videos capturing particles first falling under the influence of gravity and then rising due to an applied voltage.\n\n"
            "These videos can be analyzed using this application to accurately predict the charge of the particle under observation!\n\n"
    
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        ]

        # Initialize the first page
        self.update_page()
        
        # Configure the layout for instructions_frame
        self.instructions_frame.grid_rowconfigure(0, weight=1)  # Instructions text
        self.instructions_frame.grid_rowconfigure(1, weight=0)  # Buttons row
        self.instructions_frame.grid_columnconfigure(0, weight=1)  # Back button
        self.instructions_frame.grid_columnconfigure(1, weight=1)  # Next button

        ##################################################
        

        # Chart (Bottom Left)
        self.chart_frame = tk.Frame(self.right_frame)
        self.chart_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.figure = Figure(figsize=(4, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Charge Prediction Frame
        self.prediction_frame = tk.Frame(self.right_frame, bg="white")
        self.prediction_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Sub Frame
        self.prediction_sub_frame = tk.Frame(self.prediction_frame, bg="white")
        self.prediction_sub_frame.pack(fill=tk.BOTH, expand=True)

        # Circular Gauge for Charge
        self.gauge_canvas = tk.Canvas(self.prediction_sub_frame, width=200, height=200, bg="white")
        self.gauge_canvas.pack(side=tk.LEFT, padx=5, pady=10)

        # Interval Scatter Plot Chart
        self.interval_figure = Figure(figsize=(4, 1), dpi=100)  # Reduced figure size
        self.interval_ax = self.interval_figure.add_subplot(111)
        self.interval_chart_canvas = FigureCanvasTkAgg(self.interval_figure, self.prediction_sub_frame)
        self.interval_chart_canvas.get_tk_widget().pack(
            side=tk.RIGHT, padx=5, pady=10, fill=tk.BOTH, expand=False  # Added padding
        )

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
        
        # Reset states
        self.reset_states()

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
        self.fast_forward_button.config(state=tk.NORMAL)
        self.fast_backward_button.config(state=tk.NORMAL)

        # Read the first frame
        ret, self.frame = self.video.read()
        if ret:
            self.current_frame = 0
            self.frame = cv2.resize(self.frame, (self.display_width, self.display_height))
            self.display_frame(self.frame)

            if self.slider is not None:
                self.slider.config(to=self.total_frames - 1)  # Set slider range
                self.slider.set(self.current_frame)

            # Bind Mouse Event Listeners to Canvas
            self.video_canvas.bind("<ButtonPress-1>", self.on_mouse_down)
            self.video_canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.video_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        else:
            messagebox.showerror("Error", "Could not read the first frame of the video")
    
    
    ########################
    def update_page(self):
        """Update the instructions label and buttons based on the current page."""
        # Set the text for the current page
        self.instructions_label.config(text=self.pages[self.current_page])

        # Show or hide the image depending on the page
        if self.current_page == 0:
            self.image_label.grid()  # Show the image on the first page
        else:
            self.image_label.grid_remove()  # Hide the image on other pages
        
        # Show/hide equation
        if self.current_page == 1: 
            # Example: On page 1, display the equation
            self.set_equation_text(r"$6 \pi \eta r v_t = \frac{4}{3} \pi r^3 (\rho_{\text{oil}} - \rho_{\text{air}}) \cdot g$")
            self.equation_widget.grid()
            
            self.set_equation_text2(r"$r = \sqrt{\frac{9 \eta v_t}{2 g (\rho_{\text{oil}} - \rho_{\text{air}})}}$") 
            self.equation_widget2.grid()
        else:
            self.equation_widget.grid_remove()
            self.equation_widget2.grid_remove()
        
        if self.current_page == 2:
            self.set_equation_text3(r"$q \cdot E = 6 \pi \eta r v_r + \frac{4}{3} \pi r^3 (\rho_{\text{oil}} - \rho_{\text{air}}) \cdot g$")
            self.equation_widget3.grid()
            
            self.set_equation_text4(r"$q \cdot \frac{V}{d} = 6 \pi \eta r v_r + \frac{4}{3} \pi r^3 (\rho_{\text{oil}} - \rho_{\text{air}}) \cdot g$")
            self.equation_widget4.grid()
            
            self.set_equation_text5(r"$q = \frac{6 \pi \eta r v_r + \frac{4}{3} \pi r^3 (\rho_{\text{oil}} - \rho_{\text{air}}) \cdot g}{\left(\frac{V}{d}\right)}$")
            self.equation_widget5.grid()
            
        else:
            self.equation_widget3.grid_remove()
            self.equation_widget4.grid_remove()
            self.equation_widget5.grid_remove()
           
            
            
        # Enable or disable buttons based on the current page
        if self.current_page == 0:
            self.back_button.config(state=tk.DISABLED)  # Disable back on the first page
        else:
            self.back_button.config(state=tk.NORMAL)

        if self.current_page == len(self.pages) - 1:
            self.next_button.config(state=tk.DISABLED)  # Disable next on the last page
        else:
            self.next_button.config(state=tk.NORMAL)
        

    def back_action(self):
        """Handle the Back button click."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def next_action(self):
        """Handle the Next button click."""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_page()
            
    def add_visual_element(self):
        """Add an image to the instructions frame."""
        image_path = "/Users/calebchristian/Desktop/WorkingMillikanCV/MillikanCVV1/media/millikanApparatus.png"
        image = Image.open(image_path).resize((400, 300), Image.Resampling.LANCZOS)  # Resize image
        self.image_tk = ImageTk.PhotoImage(image)  # Keep a reference to avoid garbage collection

        # Create a label for the image
        self.image_label = tk.Label(self.instructions_frame, image=self.image_tk, bg="white")
        self.image_label.grid(row=1, column=0, columnspan=2, pady=10, sticky="n")  # Center image horizontally
   ##########
   # Eq 1 
    def add_equation_widget(self):
        """Create the matplotlib figure to display a LaTeX equation, then hide it initially."""
        self.equation_figure = Figure(figsize=(3, 1), dpi=100) #(Width, Height)
        self.equation_ax = self.equation_figure.add_subplot(111)
        self.equation_ax.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas = FigureCanvasTkAgg(self.equation_figure, self.instructions_frame)
        self.equation_widget = self.equation_canvas.get_tk_widget()
        
        # Position in grid, but hide initially
        self.equation_widget.grid(row=0, column=0, columnspan=2, pady=(130,80), sticky="n")
        self.equation_widget.grid_remove() # Hide for now   
        
    def set_equation_text(self, latex_equation: str):
        """Render the LaTeX equation text in the existing matplotlib figure."""
        # Clear old text
        self.equation_ax.clear()
        self.equation_ax.axis('off')

        # Render the new LaTeX equation
        self.equation_ax.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax.transAxes
        )
        self.equation_canvas.draw()
        
    # Eq 2
    def add_equation_widget2(self):
        """Create a second matplotlib figure to display another LaTeX equation, then hide it initially."""
        self.equation_figure2 = Figure(figsize=(3, 1), dpi=100)
        self.equation_ax2 = self.equation_figure2.add_subplot(111)
        self.equation_ax2.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas2 = FigureCanvasTkAgg(self.equation_figure2, self.instructions_frame)
        self.equation_widget2 = self.equation_canvas2.get_tk_widget()
        
        # Position in the grid but hide for now
        # Adjust row/column to your liking (e.g., row=2 or row=3)
        self.equation_widget2.grid(row=0, column=0, columnspan=2, pady=(330, 80), sticky="n")
        self.equation_widget2.grid_remove()  # Hide initially
    
    def set_equation_text2(self, latex_equation: str):
        """Render the LaTeX equation text in the second matplotlib figure."""
        self.equation_ax2.clear()
        self.equation_ax2.axis('off')

        self.equation_ax2.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax2.transAxes
        )
        self.equation_canvas2.draw() 
        
    # Eq 3 
    def add_equation_widget3(self):
        """Create a second matplotlib figure to display another LaTeX equation, then hide it initially."""
        self.equation_figure3 = Figure(figsize=(3, 1), dpi=100)
        self.equation_ax3 = self.equation_figure3.add_subplot(111)
        self.equation_ax3.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas3 = FigureCanvasTkAgg(self.equation_figure3, self.instructions_frame)
        self.equation_widget3 = self.equation_canvas3.get_tk_widget()
        
        # Position in the grid but hide for now
        # Adjust row/column to your liking (e.g., row=2 or row=3)
        self.equation_widget3.grid(row=0, column=0, columnspan=2, pady=(80, 80), sticky="n")
        self.equation_widget3.grid_remove()  # Hide initially
    
    def set_equation_text3(self, latex_equation: str):
        """Render the LaTeX equation text in the second matplotlib figure."""
        self.equation_ax3.clear()
        self.equation_ax3.axis('off')

        self.equation_ax3.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax3.transAxes
        )
        self.equation_canvas3.draw() 
    
    # Eq 4
    def add_equation_widget4(self):
        """Create a second matplotlib figure to display another LaTeX equation, then hide it initially."""
        self.equation_figure4 = Figure(figsize=(3, 1), dpi=100)
        self.equation_ax4 = self.equation_figure4.add_subplot(111)
        self.equation_ax4.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas4 = FigureCanvasTkAgg(self.equation_figure4, self.instructions_frame)
        self.equation_widget4 = self.equation_canvas4.get_tk_widget()
        
        # Position in the grid but hide for now
        # Adjust row/column to your liking (e.g., row=2 or row=3)
        self.equation_widget4.grid(row=0, column=0, columnspan=2, pady=(250, 100), sticky="n")
        self.equation_widget4.grid_remove()  # Hide initially
    
    def set_equation_text4(self, latex_equation: str):
        """Render the LaTeX equation text in the second matplotlib figure."""
        self.equation_ax4.clear()
        self.equation_ax4.axis('off')

        self.equation_ax4.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax4.transAxes
        )
        self.equation_canvas4.draw() 
    
    # Eq 5
    def add_equation_widget5(self):
        """Create a second matplotlib figure to display another LaTeX equation, then hide it initially."""
        self.equation_figure5 = Figure(figsize=(3, 1), dpi=100)
        self.equation_ax5 = self.equation_figure5.add_subplot(111)
        self.equation_ax5.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas5 = FigureCanvasTkAgg(self.equation_figure5, self.instructions_frame)
        self.equation_widget5 = self.equation_canvas5.get_tk_widget()
        
        # Position in the grid but hide for now
        # Adjust row/column to your liking (e.g., row=2 or row=3)
        self.equation_widget5.grid(row=0, column=0, columnspan=2, pady=(380, 50), sticky="n")
        self.equation_widget5.grid_remove()  # Hide initially
    
    def set_equation_text5(self, latex_equation: str):
        """Render the LaTeX equation text in the second matplotlib figure."""
        self.equation_ax5.clear()
        self.equation_ax5.axis('off')

        self.equation_ax5.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax5.transAxes
        )
        self.equation_canvas5.draw() 
        ######################
    
    def reset_states(self):
        """Reset all states to their initial values."""
        # Reset variables
        self.video = None
        self.tracker = cv2.TrackerCSRT_create()
        self.current_frame = 0
        self.total_frames = 0
        self.frame_width = 0
        self.frame_height = 0
        self.bbox = None
        self.bbox_history = {}
        self.y_centers = []
        self.charge_interval_pairs = []
        self.paused = True

        # Reset UI components
        self.video_canvas.delete("all")
        self.canvas_image = None
        self.progress_bar['value'] = 0
        self.ax.clear()
        self.chart_canvas.draw()
        self.gauge_canvas.delete("all")
        self.interval_ax.clear()
        self.interval_chart_canvas.draw()

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

        # Safely remove the slider
        if self.slider is not None:
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
            self.update_prediction_display(charge, interval)
            # self.prediction_label.config(
            #     text=f"Charge Prediction:\nCharge: {charge:.5e} C\nInterval: {interval:.2f} e"
            # )
        except ValueError as e:
            # self.prediction_label.config(text=f"Error in calculation: {str(e)}")
            pass

        # Plotting
        self.ax.clear()
        self.ax.set_title('Detected Peaks and Troughs in Y-Center Data')
        self.ax.set_xlabel('Frame Index')
        self.ax.set_ylabel('Y-Center Value')
        self.ax.grid(True)
        self.ax.plot(t, y, label='Y-Center Data', color='black')
        self.ax.plot(t[peaks], y[peaks], 'x', label='Peaks', color='blue')
        self.ax.plot(t[troughs], y[troughs], 'bo', label='Troughs')
        self.ax.invert_yaxis()
        self.ax.legend()
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

    def move_fast_forward(self):
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 10
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

    def move_fast_backward(self):
        if self.current_frame > 0:
            self.current_frame -= 10
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

    def update_prediction_display(self, charge, interval):
        """Update the gauge and bar chart with new prediction values."""
        self.update_gauge(charge)
        self.update_interval_chart(charge, interval)

    def update_gauge(self, charge):
        """Update the circular gauge with tick marks and charge label."""
        self.gauge_canvas.delete("all")
        max_charge = 1e-18  # Adjust maximum for better scaling
        normalized_charge = min(charge / max_charge, 1.0)

        center_x, center_y, radius = 100, 100, 80
        start_angle = -90
        end_angle = start_angle + normalized_charge * 360

        # Draw the filled arc for the gauge
        self.gauge_canvas.create_arc(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            start=start_angle, extent=end_angle - start_angle,
            fill="blue", outline="blue"
        )

        # Draw the outer circle
        self.gauge_canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="black"
        )

        # Add tick marks
        num_ticks = 10  # Number of ticks around the gauge
        for i in range(num_ticks + 1):
            tick_angle = start_angle + (360 / num_ticks) * i
            rad_angle = np.radians(tick_angle)

            # Tick mark start and end points
            x_start = center_x + (radius - 10) * cos(rad_angle)
            y_start = center_y + (radius - 10) * sin(rad_angle)
            x_end = center_x + radius * cos(rad_angle)
            y_end = center_y + radius * sin(rad_angle)

            # Draw tick marks
            self.gauge_canvas.create_line(x_start, y_start, x_end, y_end, fill="black")

            # Add labels at every other tick
            if i % 2 == 0:
                label_angle = np.radians(tick_angle)
                label_x = center_x + (radius - 20) * cos(label_angle)
                label_y = center_y + (radius - 20) * sin(label_angle)
                tick_value = max_charge * (i / num_ticks)
                self.gauge_canvas.create_text(
                    label_x, label_y, text=f"{tick_value:.1e}", font=("Arial", 8)
                )

        # Display the charge value in the center of the gauge
        self.gauge_canvas.create_text(
            center_x, center_y,
            text=f"{charge:.2e} C", font=("Arial", 12, "bold")
        )

    def update_interval_chart(self, charge, interval):
        """Update the scatter plot for charge vs. interval."""
        self.interval_ax.clear()
        
        # Add the new charge-interval pair to the list
        if charge is not None:
            self.charge_interval_pairs.append((charge, interval))
        
        # Prepare data for the scatter plot
        charges = [pair[0] for pair in self.charge_interval_pairs]
        intervals = [pair[1] for pair in self.charge_interval_pairs]

        # Scatter plot for charge vs. interval
        self.interval_ax.scatter(charges, intervals, color="blue", label="Data Points", s=20)  # Reduced point size
        self.interval_ax.set_title("Charge vs. Interval", fontsize=10)  # Smaller title font
        self.interval_ax.set_xlabel("Charge (C)", fontsize=8)  # Smaller label font
        self.interval_ax.set_ylabel("Interval", fontsize=8)
        self.interval_ax.grid(True)

        self.interval_figure.tight_layout()

        # Adjust tick label sizes
        self.interval_ax.tick_params(axis='both', which='major', labelsize=8)

        self.interval_chart_canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = MillikanExperimentApp(root)
    root.mainloop()
