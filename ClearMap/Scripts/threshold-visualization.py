#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import datetime
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



# Try importing tifffile, fall back to PIL if not available
try:
    import tifffile
    USE_TIFFFILE = True
except ImportError:
    from PIL import Image
    USE_TIFFFILE = False
    print("tifffile not found, using PIL instead. Install tifffile for better performance with large stacks.")

class ThresholdVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Object Threshold Visualizer")
        self.root.geometry("1200x800")
        
        # File paths
        self.image_path = None
        self.coords_path = None
        self.intensities_path = None
        
        # Data containers
        self.image_stack = None
        self.current_z = 0
        self.max_z = 0
        self.coords = None  # Will be in ZYX order
        self.intensities = None
        
        # Threshold values (with upper and lower)
        self.raw_lower = 0
        self.raw_upper = 100
        self.filtered_lower = 0
        self.filtered_upper = 100
        self.watershed_lower = 0
        self.watershed_upper = 100
        self.size_lower = 0
        self.size_upper = 100
        
        # Create UI
        self.create_ui()
    
    def create_ui(self):
        
        # Create main frames
        self.left_frame = tk.Frame(self.root, width=300, height=800)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.left_frame.pack_propagate(False)
        
        self.center_frame = tk.Frame(self.root, width=600, height=800)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = tk.Frame(self.root, width=400, height=800)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_frame.pack_propagate(False)
        
        # File selection and status in left frame
        #file_frame = tk.LabelFrame(self.left_frame, text="File Selection", padx=10, pady=10)
        #file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        #tk.Button(file_frame, text="Select Image Stack (.tif)", command=self.load_image).pack(fill=tk.X, pady=5)
        #tk.Button(file_frame, text="Select Coordinates (.npy)", command=self.load_coords).pack(fill=tk.X, pady=5)
        #tk.Button(file_frame, text="Select Intensities (.npy)", command=self.load_intensities).pack(fill=tk.X, pady=5)
        
        # Status indicators
        self.status_frame = tk.LabelFrame(self.left_frame, text="Status", padx=10, pady=10)
        self.status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.image_status = tk.Label(self.status_frame, text="Image: Not loaded")
        self.image_status.pack(anchor=tk.W)
        self.coords_status = tk.Label(self.status_frame, text="Coordinates: Not loaded")
        self.coords_status.pack(anchor=tk.W)
        self.intensities_status = tk.Label(self.status_frame, text="Intensities: Not loaded")
        self.intensities_status.pack(anchor=tk.W)
        
        # Z-slice control
        self.z_frame = tk.LabelFrame(self.left_frame, text="Z-Slice Control", padx=10, pady=10)
        self.z_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.z_nav_frame = tk.Frame(self.z_frame)
        self.z_nav_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(self.z_nav_frame, text="<<", command=lambda: self.change_z(-10)).pack(side=tk.LEFT)
        tk.Button(self.z_nav_frame, text="<", command=lambda: self.change_z(-1)).pack(side=tk.LEFT)
        self.z_label = tk.Label(self.z_nav_frame, text="Z: 0/0")
        self.z_label.pack(side=tk.LEFT, padx=10)
        tk.Button(self.z_nav_frame, text=">", command=lambda: self.change_z(1)).pack(side=tk.LEFT)
        tk.Button(self.z_nav_frame, text=">>", command=lambda: self.change_z(10)).pack(side=tk.LEFT)
        
        self.z_slider_var = tk.IntVar(value=0)
        self.z_slider = tk.Scale(self.z_frame, from_=0, to=0, orient=tk.HORIZONTAL, 
                            variable=self.z_slider_var, command=self.z_slider_changed)
        self.z_slider.pack(fill=tk.X)
        
        # Z range slider
        self.z_range_frame = tk.LabelFrame(self.left_frame, text="Z Range Visualization (±)", padx=10, pady=10)
        self.z_range_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.z_range_var = tk.IntVar(value=0)
        self.z_range_slider = tk.Scale(self.z_range_frame, from_=0, to=10, orient=tk.HORIZONTAL, 
                                variable=self.z_range_var, command=self.update_visualization)
        self.z_range_slider.pack(fill=tk.X)
        
        # Export button
        export_button = tk.Button(self.left_frame, text="Export Results", command=self.export_results, 
                        font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white', pady=10)
        export_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Stats display
        self.stats_frame = tk.LabelFrame(self.left_frame, text="Statistics", padx=10, pady=10)
        self.stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.total_objects_label = tk.Label(self.stats_frame, text="Total Objects: 0")
        self.total_objects_label.pack(anchor=tk.W)
        
        self.visible_objects_label = tk.Label(self.stats_frame, text="Visible Objects: 0")
        self.visible_objects_label.pack(anchor=tk.W)
        
        self.percent_visible_label = tk.Label(self.stats_frame, text="Percent Visible: 0%")
        self.percent_visible_label.pack(anchor=tk.W)
        
        self.z_slice_objects_label = tk.Label(self.stats_frame, text="Current Z Objects: 0")
        self.z_slice_objects_label.pack(anchor=tk.W)
        
        # Visualization area in center
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.center_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize empty plot
        self.ax.set_title("Load image and data files to begin")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.canvas.draw()
        
        # Add this right after creating the center_frame and before creating the visualization

        # Image adjustment panel above the visualization area in center frame
        image_adjust_frame = tk.Frame(self.center_frame)
        image_adjust_frame.pack(fill=tk.X, pady=5, before=self.canvas.get_tk_widget())

        # Image brightness and contrast controls
        tk.Label(image_adjust_frame, text="Image Display Controls:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10)

        # Brightness control
        tk.Label(image_adjust_frame, text="Brightness:").pack(side=tk.LEFT, padx=(10, 0))
        self.brightness_var = tk.DoubleVar(value=1.0)
        brightness_slider = tk.Scale(image_adjust_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL,
                                    variable=self.brightness_var, resolution=0.1, length=150,
                                    command=self.update_image_display)
        brightness_slider.pack(side=tk.LEFT)

        # Contrast control
        tk.Label(image_adjust_frame, text="Contrast:").pack(side=tk.LEFT, padx=(10, 0))
        self.contrast_var = tk.DoubleVar(value=1.0)
        contrast_slider = tk.Scale(image_adjust_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL,
                                variable=self.contrast_var, resolution=0.1, length=150,
                                command=self.update_image_display)
        contrast_slider.pack(side=tk.LEFT)

        # Auto-adjust button
        tk.Button(image_adjust_frame, text="Auto Adjust", 
                command=self.auto_adjust_image, padx=10).pack(side=tk.LEFT, padx=10)

        # Reset button
        tk.Button(image_adjust_frame, text="Reset", 
                command=self.reset_image_display, padx=10).pack(side=tk.LEFT)
                
        # Threshold controls in right frame
        self.threshold_frame = tk.LabelFrame(self.right_frame, text="Threshold Controls", padx=10, pady=10)
        self.threshold_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Raw intensity thresholds
        raw_frame = tk.LabelFrame(self.threshold_frame, text="Raw Intensity Thresholds")
        raw_frame.pack(fill=tk.X, pady=10, padx=5)

        # Raw lower
        raw_lower_frame = tk.Frame(raw_frame)
        raw_lower_frame.pack(fill=tk.X, pady=5)
        tk.Label(raw_lower_frame, text="Lower:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.raw_lower_var = tk.DoubleVar(value=0)
        self.raw_lower_slider = tk.Scale(raw_lower_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                variable=self.raw_lower_var, command=self.update_thresholds,
                                length=200, width=20)
        self.raw_lower_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_button_frame = tk.Frame(raw_lower_frame)
        entry_button_frame.pack(side=tk.LEFT, padx=5)
        self.raw_lower_entry = tk.Entry(entry_button_frame, width=8)
        self.raw_lower_entry.pack(side=tk.LEFT)
        tk.Button(entry_button_frame, text="Set", width=5, 
                command=lambda: self.set_threshold_from_entry(self.raw_lower_entry, self.raw_lower_var, self.raw_lower_slider)).pack(side=tk.LEFT, padx=2)

        # Raw upper
        raw_upper_frame = tk.Frame(raw_frame)
        raw_upper_frame.pack(fill=tk.X, pady=5)
        tk.Label(raw_upper_frame, text="Upper:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.raw_upper_var = tk.DoubleVar(value=100)
        self.raw_upper_slider = tk.Scale(raw_upper_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                variable=self.raw_upper_var, command=self.update_thresholds,
                                length=200, width=20)
        self.raw_upper_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_button_frame = tk.Frame(raw_upper_frame)
        entry_button_frame.pack(side=tk.LEFT, padx=5)
        self.raw_upper_entry = tk.Entry(entry_button_frame, width=8)
        self.raw_upper_entry.pack(side=tk.LEFT)
        tk.Button(entry_button_frame, text="Set", width=5, 
                command=lambda: self.set_threshold_from_entry(self.raw_upper_entry, self.raw_upper_var, self.raw_upper_slider)).pack(side=tk.LEFT, padx=2)

        # Filtered intensity thresholds
        filtered_frame = tk.LabelFrame(self.threshold_frame, text="Filtered Intensity Thresholds")
        filtered_frame.pack(fill=tk.X, pady=10, padx=5)

        # Filtered lower
        filtered_lower_frame = tk.Frame(filtered_frame)
        filtered_lower_frame.pack(fill=tk.X, pady=5)
        tk.Label(filtered_lower_frame, text="Lower:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.filtered_lower_var = tk.DoubleVar(value=0)
        self.filtered_lower_slider = tk.Scale(filtered_lower_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                    variable=self.filtered_lower_var, command=self.update_thresholds,
                                    length=200, width=20)
        self.filtered_lower_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_button_frame = tk.Frame(filtered_lower_frame)
        entry_button_frame.pack(side=tk.LEFT, padx=5)
        self.filtered_lower_entry = tk.Entry(entry_button_frame, width=8)
        self.filtered_lower_entry.pack(side=tk.LEFT)
        tk.Button(entry_button_frame, text="Set", width=5, 
                command=lambda: self.set_threshold_from_entry(self.filtered_lower_entry, self.filtered_lower_var, self.filtered_lower_slider)).pack(side=tk.LEFT, padx=2)

        # Filtered upper
        filtered_upper_frame = tk.Frame(filtered_frame)
        filtered_upper_frame.pack(fill=tk.X, pady=5)
        tk.Label(filtered_upper_frame, text="Upper:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.filtered_upper_var = tk.DoubleVar(value=100)
        self.filtered_upper_slider = tk.Scale(filtered_upper_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                    variable=self.filtered_upper_var, command=self.update_thresholds,
                                    length=200, width=20)
        self.filtered_upper_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_button_frame = tk.Frame(filtered_upper_frame)
        entry_button_frame.pack(side=tk.LEFT, padx=5)
        self.filtered_upper_entry = tk.Entry(entry_button_frame, width=8)
        self.filtered_upper_entry.pack(side=tk.LEFT)
        tk.Button(entry_button_frame, text="Set", width=5, 
                command=lambda: self.set_threshold_from_entry(self.filtered_upper_entry, self.filtered_upper_var, self.filtered_upper_slider)).pack(side=tk.LEFT, padx=2)

        # Watershed intensity thresholds
        watershed_frame = tk.LabelFrame(self.threshold_frame, text="Watershed Intensity Thresholds")
        watershed_frame.pack(fill=tk.X, pady=10, padx=5)

        # Watershed lower
        watershed_lower_frame = tk.Frame(watershed_frame)
        watershed_lower_frame.pack(fill=tk.X, pady=5)
        tk.Label(watershed_lower_frame, text="Lower:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.watershed_lower_var = tk.DoubleVar(value=0)
        self.watershed_lower_slider = tk.Scale(watershed_lower_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                    variable=self.watershed_lower_var, command=self.update_thresholds,
                                    length=200, width=20)
        self.watershed_lower_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_button_frame = tk.Frame(watershed_lower_frame)
        entry_button_frame.pack(side=tk.LEFT, padx=5)
        self.watershed_lower_entry = tk.Entry(entry_button_frame, width=8)
        self.watershed_lower_entry.pack(side=tk.LEFT)
        tk.Button(entry_button_frame, text="Set", width=5, 
                command=lambda: self.set_threshold_from_entry(self.watershed_lower_entry, self.watershed_lower_var, self.watershed_lower_slider)).pack(side=tk.LEFT, padx=2)

        # Watershed upper
        watershed_upper_frame = tk.Frame(watershed_frame)
        watershed_upper_frame.pack(fill=tk.X, pady=5)
        tk.Label(watershed_upper_frame, text="Upper:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.watershed_upper_var = tk.DoubleVar(value=100)
        self.watershed_upper_slider = tk.Scale(watershed_upper_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                    variable=self.watershed_upper_var, command=self.update_thresholds,
                                    length=200, width=20)
        self.watershed_upper_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_button_frame = tk.Frame(watershed_upper_frame)
        entry_button_frame.pack(side=tk.LEFT, padx=5)
        self.watershed_upper_entry = tk.Entry(entry_button_frame, width=8)
        self.watershed_upper_entry.pack(side=tk.LEFT)
        tk.Button(entry_button_frame, text="Set", width=5, 
                command=lambda: self.set_threshold_from_entry(self.watershed_upper_entry, self.watershed_upper_var, self.watershed_upper_slider)).pack(side=tk.LEFT, padx=2)

        # Size thresholds
        size_frame = tk.LabelFrame(self.threshold_frame, text="Size Thresholds")
        size_frame.pack(fill=tk.X, pady=10, padx=5)

        # Size lower
        size_lower_frame = tk.Frame(size_frame)
        size_lower_frame.pack(fill=tk.X, pady=5)
        tk.Label(size_lower_frame, text="Lower:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.size_lower_var = tk.DoubleVar(value=0)
        self.size_lower_slider = tk.Scale(size_lower_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                variable=self.size_lower_var, command=self.update_thresholds,
                                length=200, width=20)
        self.size_lower_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_button_frame = tk.Frame(size_lower_frame)
        entry_button_frame.pack(side=tk.LEFT, padx=5)
        self.size_lower_entry = tk.Entry(entry_button_frame, width=8)
        self.size_lower_entry.pack(side=tk.LEFT)
        tk.Button(entry_button_frame, text="Set", width=5, 
                command=lambda: self.set_threshold_from_entry(self.size_lower_entry, self.size_lower_var, self.size_lower_slider)).pack(side=tk.LEFT, padx=2)

        # Size upper
        size_upper_frame = tk.Frame(size_frame)
        size_upper_frame.pack(fill=tk.X, pady=5)
        tk.Label(size_upper_frame, text="Upper:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.size_upper_var = tk.DoubleVar(value=100)
        self.size_upper_slider = tk.Scale(size_upper_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                variable=self.size_upper_var, command=self.update_thresholds,
                                length=200, width=20)
        self.size_upper_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_button_frame = tk.Frame(size_upper_frame)
        entry_button_frame.pack(side=tk.LEFT, padx=5)
        self.size_upper_entry = tk.Entry(entry_button_frame, width=8)
        self.size_upper_entry.pack(side=tk.LEFT)
        tk.Button(entry_button_frame, text="Set", width=5, 
                command=lambda: self.set_threshold_from_entry(self.size_upper_entry, self.size_upper_var, self.size_upper_slider)).pack(side=tk.LEFT, padx=2)
    

        # Threshold storage controls
        threshold_storage_frame = tk.LabelFrame(self.left_frame, text="Threshold Management", padx=10, pady=10)
        threshold_storage_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(threshold_storage_frame, text="Store Current Thresholds", 
                command=self.save_current_thresholds, bg='#4CAF50', fg='white').pack(fill=tk.X, pady=5)

        tk.Button(threshold_storage_frame, text="Update With Average", 
                command=self.update_thresholds_with_average, bg='#2196F3', fg='white').pack(fill=tk.X, pady=5)

        # File selection with a single button
        file_frame = tk.LabelFrame(self.left_frame, text="File Selection", padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(file_frame, text="Load Data Files", 
                command=self.load_all_data, 
                font=('Arial', 11, 'bold'), 
                bg='#4CAF50', fg='white', pady=8).pack(fill=tk.X, pady=5)

    # Then add this new method to the class:
    def load_all_data(self):
        """Load all data files (image, coordinates, intensities) with a common base name"""
        # First, ask for the image file
        self.image_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("TIFF files", "*.tif"), ("All files", "*.*")]
        )
        
        if not self.image_path:
            return
        
        # Get the base directory and filename
        base_dir = os.path.dirname(self.image_path)
        base_name = os.path.splitext(os.path.basename(self.image_path))[0]
        
        # Look for corresponding coordinate and intensity files
        coords_path = os.path.join(base_dir, f"{base_name}_cells-allpoints.npy")
        intensities_path = os.path.join(base_dir, f"{base_name}_intensities-allpoints.npy")
        
        # Load image
        try:
            if USE_TIFFFILE:
                # Use tifffile to load multi-page TIF
                self.image_stack = tifffile.imread(self.image_path)
            else:
                # Use PIL as fallback
                img = Image.open(self.image_path)
                
                # Check if this is a multi-page TIFF
                try:
                    n_frames = img.n_frames
                except AttributeError:
                    n_frames = 1
                
                # Load all frames
                self.image_stack = []
                for i in range(n_frames):
                    img.seek(i)
                    self.image_stack.append(np.array(img))
                
                self.image_stack = np.array(self.image_stack)
            
            # Check if we have a stack or a single image
            if len(self.image_stack.shape) == 2:
                # Convert single image to stack with 1 frame
                self.image_stack = np.expand_dims(self.image_stack, axis=0)
            
            # Update Z slider
            self.max_z = self.image_stack.shape[0] - 1
            self.current_z = 0
            self.z_slider.config(to=self.max_z)
            self.z_range_slider.config(to=min(10, self.max_z))
            self.z_label.config(text=f"Z: {self.current_z}/{self.max_z}")
            
            self.image_status.config(text=f"Image: {os.path.basename(self.image_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # Load coordinates
        try:
            if os.path.exists(coords_path):
                self.coords = np.load(coords_path)
                self.coords_path = coords_path
                
                # Basic validation of coordinates
                if self.coords.shape[1] < 3:
                    messagebox.showerror("Error", "Coordinates must have at least 3 columns (x, y, z)")
                    self.coords = None
                    return
                
                self.coords_status.config(text=f"Coordinates: {os.path.basename(coords_path)}")
                
                # Display stats about coordinates
                unique_z = np.unique(self.coords[:, 2])  # Z is third column (XYZ order)
            else:
                # If not found automatically, ask user to select
                messagebox.showinfo("Coordinates File Not Found", 
                                f"Could not find coordinates file: {os.path.basename(coords_path)}\nPlease select it manually.")
                self.load_coords()
                if self.coords is None:
                    return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load coordinates: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # Load intensities
        try:
            if os.path.exists(intensities_path):
                self.intensities = np.load(intensities_path)
                self.intensities_path = intensities_path
                
                # Basic validation of intensities
                if self.intensities.shape[1] < 4:
                    messagebox.showerror("Error", "Intensities must have at least 4 columns (raw, filtered, watershed, size)")
                    self.intensities = None
                    return
                
                # Adjust sliders to data range
                if self.intensities is not None:
                    raw_max = np.max(self.intensities[:, 0])
                    filtered_max = np.max(self.intensities[:, 1])
                    watershed_max = np.max(self.intensities[:, 2])
                    size_max = np.max(self.intensities[:, 3])
                    
                    # Update lower sliders
                    self.raw_lower_slider.config(to=raw_max)
                    self.filtered_lower_slider.config(to=filtered_max)
                    self.watershed_lower_slider.config(to=watershed_max)
                    self.size_lower_slider.config(to=size_max)
                    
                    # Update upper sliders
                    self.raw_upper_slider.config(to=raw_max)
                    self.filtered_upper_slider.config(to=filtered_max)
                    self.watershed_upper_slider.config(to=watershed_max)
                    self.size_upper_slider.config(to=size_max)
                    
                    # Set initial upper values
                    self.raw_upper_var.set(raw_max)
                    self.filtered_upper_var.set(filtered_max)
                    self.watershed_upper_var.set(watershed_max)
                    self.size_upper_var.set(size_max)
                
                self.intensities_status.config(text=f"Intensities: {os.path.basename(intensities_path)}")
            else:
                # If not found automatically, ask user to select
                messagebox.showinfo("Intensities File Not Found", 
                                f"Could not find intensities file: {os.path.basename(intensities_path)}\nPlease select it manually.")
                self.load_intensities()
                if self.intensities is None:
                    return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load intensities: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # All data loaded successfully, update visualization
        self.update_visualization()
        
        # Show summary information
        messagebox.showinfo("Data Loaded Successfully", 
                        f"Loaded data files for {base_name}:\n"
                        f"- Image stack with {self.max_z + 1} slices\n"
                        f"- {len(self.coords)} coordinate points\n"
                        f"- Intensity data for {len(self.intensities)} points")
    
    def load_coords(self):
        """Load coordinate data from a NumPy file (XYZ order)"""
        self.coords_path = filedialog.askopenfilename(
            title="Select Coordinates File",
            filetypes=[("NumPy files", "*.npy"), ("All files", "*.*")]
        )
        
        if not self.coords_path:
            return
            
        try:
            self.coords = np.load(self.coords_path)
            
            # Basic validation of coordinates
            if self.coords.shape[1] < 3:
                messagebox.showerror("Error", "Coordinates must have at least 3 columns (x, y, z)")
                self.coords = None
                return
            
            self.coords_status.config(text=f"Coordinates: {os.path.basename(self.coords_path)}")
            self.update_visualization()
            
            # Display stats about coordinates
            unique_z = np.unique(self.coords[:, 2])  # Z is third column
            messagebox.showinfo("Coordinates Loaded", 
                            f"Loaded {len(self.coords)} coordinate points\n"
                            f"Z range: {np.min(self.coords[:, 2])} to {np.max(self.coords[:, 2])}\n"
                            f"Number of Z slices with points: {len(unique_z)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load coordinates: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def load_intensities(self):
        """Load intensity data from a NumPy file"""
        self.intensities_path = filedialog.askopenfilename(
            title="Select Intensities File",
            filetypes=[("NumPy files", "*.npy"), ("All files", "*.*")]
        )
        
        if not self.intensities_path:
            return
            
        try:
            self.intensities = np.load(self.intensities_path)
            
            # Basic validation of intensities
            if self.intensities.shape[1] < 4:
                messagebox.showerror("Error", "Intensities must have at least 4 columns (raw, filtered, watershed, size)")
                self.intensities = None
                return
            
            # Adjust sliders to data range
            if self.intensities is not None:
                raw_max = np.max(self.intensities[:, 0])
                filtered_max = np.max(self.intensities[:, 1])
                watershed_max = np.max(self.intensities[:, 2])
                size_max = np.max(self.intensities[:, 3])
                
                # Update lower sliders
                self.raw_lower_slider.config(to=raw_max)
                self.filtered_lower_slider.config(to=filtered_max)
                self.watershed_lower_slider.config(to=watershed_max)
                self.size_lower_slider.config(to=size_max)
                
                # Update upper sliders
                self.raw_upper_slider.config(to=raw_max)
                self.filtered_upper_slider.config(to=filtered_max)
                self.watershed_upper_slider.config(to=watershed_max)
                self.size_upper_slider.config(to=size_max)
                
                # Set initial upper values
                self.raw_upper_var.set(raw_max)
                self.filtered_upper_var.set(filtered_max)
                self.watershed_upper_var.set(watershed_max)
                self.size_upper_var.set(size_max)
            
            self.intensities_status.config(text=f"Intensities: {os.path.basename(self.intensities_path)}")
            self.update_visualization()
            
            # Show summary statistics
            messagebox.showinfo("Intensities Loaded", 
                                f"Raw intensity range: {np.min(self.intensities[:, 0]):.2f} to {np.max(self.intensities[:, 0]):.2f}\n"
                                f"Filtered intensity range: {np.min(self.intensities[:, 1]):.2f} to {np.max(self.intensities[:, 1]):.2f}\n"
                                f"Watershed intensity range: {np.min(self.intensities[:, 2]):.2f} to {np.max(self.intensities[:, 2]):.2f}\n"
                                f"Size range: {np.min(self.intensities[:, 3]):.2f} to {np.max(self.intensities[:, 3]):.2f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load intensities: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def set_threshold_from_entry(self, entry_widget, var, slider):
        """Set threshold from manual entry"""
        try:
            value = float(entry_widget.get())
            var.set(value)
            slider.set(value)
            self.update_thresholds()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def update_thresholds(self, *args):
        """Update threshold values and validate them"""
        # Get current values from variables
        self.raw_lower = self.raw_lower_var.get()
        self.raw_upper = self.raw_upper_var.get()
        self.filtered_lower = self.filtered_lower_var.get()
        self.filtered_upper = self.filtered_upper_var.get()
        self.watershed_lower = self.watershed_lower_var.get()
        self.watershed_upper = self.watershed_upper_var.get()
        self.size_lower = self.size_lower_var.get()
        self.size_upper = self.size_upper_var.get()
        
        # Check if lower exceeds upper
        if self.raw_lower > self.raw_upper:
            self.raw_lower = self.raw_upper
            self.raw_lower_var.set(self.raw_lower)
            
        if self.filtered_lower > self.filtered_upper:
            self.filtered_lower = self.filtered_upper
            self.filtered_lower_var.set(self.filtered_lower)
            
        if self.watershed_lower > self.watershed_upper:
            self.watershed_lower = self.watershed_upper
            self.watershed_lower_var.set(self.watershed_lower)
            
        if self.size_lower > self.size_upper:
            self.size_lower = self.size_upper
            self.size_lower_var.set(self.size_lower)
        
        self.update_visualization()
    
    def change_z(self, delta):
        """Change Z slice by delta amount"""
        new_z = self.current_z + delta
        if 0 <= new_z <= self.max_z:
            self.current_z = new_z
            self.z_slider_var.set(new_z)
            self.z_label.config(text=f"Z: {self.current_z}/{self.max_z}")
            self.update_visualization()
    
    def z_slider_changed(self, *args):
        """Handle Z slider changes"""
        self.current_z = self.z_slider_var.get()
        self.z_label.config(text=f"Z: {self.current_z}/{self.max_z}")
        self.update_visualization()
    
    def update_visualization(self, *args):
        """Update the visualization based on current settings"""
        self.ax.clear()
        
        # Display image if loaded
        if self.image_stack is not None and self.current_z <= self.max_z:
            # Get the current slice
            img_slice = self.image_stack[self.current_z].copy()
            
            # Apply brightness and contrast adjustments
            brightness = self.brightness_var.get()
            contrast = self.contrast_var.get()
            
            # Normalize image to 0-1 range for adjustment
            img_min = np.min(img_slice)
            img_max = np.max(img_slice)
            if img_max > img_min:
                img_norm = (img_slice - img_min) / (img_max - img_min)
            else:
                img_norm = img_slice - img_min
            
            # Apply contrast (multiply)
            img_norm = img_norm * contrast
            
            # Apply brightness (add)
            img_norm = img_norm + (brightness - 1.0)
            
            # Clip to valid range
            img_norm = np.clip(img_norm, 0, 1)
            
            # Display the adjusted image
            self.ax.imshow(img_norm, cmap='gray', vmin=0, vmax=1)
        
        # Check if all data is loaded
        if self.image_stack is None or self.coords is None or self.intensities is None:
            self.ax.set_title("Load all data files to visualize")
            self.canvas.draw()
            return
        
        # Apply thresholds (both upper and lower)
        visible_mask = (
            (self.intensities[:, 0] >= self.raw_lower) &
            (self.intensities[:, 0] <= self.raw_upper) &
            (self.intensities[:, 1] >= self.filtered_lower) &
            (self.intensities[:, 1] <= self.filtered_upper) &
            (self.intensities[:, 2] >= self.watershed_lower) &
            (self.intensities[:, 2] <= self.watershed_upper) &
            (self.intensities[:, 3] >= self.size_lower) &
            (self.intensities[:, 3] <= self.size_upper)
        )
        
        # Get coordinates that pass threshold
        visible_coords = self.coords[visible_mask]
        
        # Filter by Z-range from current slice
        z_range = self.z_range_var.get()
        z_min = max(0, self.current_z - z_range)
        z_max = min(self.max_z, self.current_z + z_range)
        
        # Filter points by Z coordinate (Z is third column)
        z_mask = (visible_coords[:, 2] >= z_min) & (visible_coords[:, 2] <= z_max)
        visible_z_coords = visible_coords[z_mask]
        
        # Update stats
        total_objects = len(self.coords)
        visible_objects = np.sum(visible_mask)
        percent_visible = (visible_objects / total_objects * 100) if total_objects > 0 else 0
        current_z_objects = len(visible_z_coords)
        
        self.total_objects_label.config(text=f"Total Objects: {total_objects}")
        self.visible_objects_label.config(text=f"Visible Objects: {visible_objects}")
        self.percent_visible_label.config(text=f"Percent Visible: {percent_visible:.1f}%")
        self.z_slice_objects_label.config(text=f"Current Z Range Objects: {current_z_objects}")
        
        # Plot coordinates that pass threshold (XYZ order)
        if len(visible_z_coords) > 0:
            # Map opacity by Z-distance from current slice
            z_distances = np.abs(visible_z_coords[:, 2] - self.current_z)
            max_distance = max(1, z_range)  # Avoid division by zero
            opacities = 1 - (z_distances / max_distance) * 0.7  # Scale opacity from 0.3 to 1.0
            
            # Scatter plot with variable opacity
            scatter = self.ax.scatter(
                visible_z_coords[:, 0],  # X is first column
                visible_z_coords[:, 1],  # Y is second column
                c='lime',
                s=30, 
                alpha=0.7,
                marker='o'
            )
        
        self.ax.set_title(f"Z-slice {self.current_z}/{self.max_z} | Showing {current_z_objects} of {visible_objects} objects")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.canvas.draw()
    
    def export_results(self):
        """Export thresholded results to CSV with specific format"""
        if self.coords is None or self.intensities is None:
            messagebox.showerror("Error", "Cannot export: No data loaded")
            return
        
        # Get the directory to save in
        default_dir = os.path.dirname(self.image_path) if self.image_path else os.getcwd()
        export_dir = filedialog.askdirectory(initialdir=default_dir, title="Select Export Directory")
        
        if not export_dir:
            return  # User cancelled
        
        try:
            # Apply current thresholds
            visible_mask = (
                (self.intensities[:, 0] >= self.raw_lower) &
                (self.intensities[:, 0] <= self.raw_upper) &
                (self.intensities[:, 1] >= self.filtered_lower) &
                (self.intensities[:, 1] <= self.filtered_upper) &
                (self.intensities[:, 2] >= self.watershed_lower) &
                (self.intensities[:, 2] <= self.watershed_upper) &
                (self.intensities[:, 3] >= self.size_lower) &
                (self.intensities[:, 3] <= self.size_upper)
            )
            
            # Get filtered data
            filtered_coords = self.coords[visible_mask]
            filtered_intensities = self.intensities[visible_mask]
            
            # Generate timestamp for filenames
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create base filename
            base_name = os.path.splitext(os.path.basename(self.image_path))[0] if self.image_path else "export"
            base_filename = f"{base_name}_filtered_{timestamp}"
            
            # Save coordinates as NumPy file
            coords_filename = os.path.join(export_dir, f"{base_filename}_coords.npy")
            #np.save(coords_filename, filtered_coords)
            
            # Save intensities as NumPy file
            intensities_filename = os.path.join(export_dir, f"{base_filename}_intensities.npy")
            #np.save(intensities_filename, filtered_intensities)
            
            # Create threshold table in CSV format exactly as specified
            # Format: Two columns (threshold, row) with rows for lower/upper bounds
            threshold_data = {
                'threshold': [
                    f"({self.raw_lower},{self.raw_upper})",
                    f"({self.filtered_lower},{self.filtered_upper})",
                    f"({self.watershed_lower},{self.watershed_upper})",
                    f"({self.size_lower},{self.size_upper})"
                ],
                'row': [(0,0), (1,1), (2,2), (3,3)]
            }
            
            threshold_df = pd.DataFrame(threshold_data)
            
            # Use the preset filename "thresholdParameter.csv"
            threshold_csv = os.path.join(export_dir, "thresholdParameter.csv")
            threshold_df.to_csv(threshold_csv, index=False)
            
            # Also save combined data as CSV
            csv_filename = os.path.join(export_dir, f"{base_filename}.csv")
            
            # Create DataFrame with combined data
            data = []
            for i in range(len(filtered_coords)):
                data.append({
                    'x': filtered_coords[i, 0],
                    'y': filtered_coords[i, 1],
                    'z': filtered_coords[i, 2],
                    'raw_intensity': filtered_intensities[i, 0],
                    'filtered_intensity': filtered_intensities[i, 1],
                    'watershed_intensity': filtered_intensities[i, 2],
                    'size': filtered_intensities[i, 3]
                })
            
            df = pd.DataFrame(data)
            #df.to_csv(csv_filename, index=False)
            
            # Store current thresholds
            self.save_current_thresholds()
            
            messagebox.showinfo("Export Complete", 
                            f"Exported {len(filtered_coords)} objects to:\n{export_dir}\n\n"
                            f"Files created:\n"
                            f"- {os.path.basename(csv_filename)}\n"
                            f"- {os.path.basename(coords_filename)}\n"
                            f"- {os.path.basename(intensities_filename)}\n"
                            f"- thresholdParameter.csv")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
            import traceback
            traceback.print_exc()

    def save_current_thresholds(self):
        """Save current threshold values to be averaged later"""
        # Create a dictionary to store current thresholds
        self.stored_thresholds = {
            'count': 1,  # Number of thresholds stored/averaged
            'raw_lower': self.raw_lower,
            'raw_upper': self.raw_upper,
            'filtered_lower': self.filtered_lower,
            'filtered_upper': self.filtered_upper,
            'watershed_lower': self.watershed_lower,
            'watershed_upper': self.watershed_upper,
            'size_lower': self.size_lower,
            'size_upper': self.size_upper
        }
        
        messagebox.showinfo("Thresholds Stored", "Current threshold values have been stored.")

    def update_thresholds_with_average(self):
        """Update current thresholds by averaging with stored values"""
        # Check if we have stored thresholds
        if not hasattr(self, 'stored_thresholds'):
            messagebox.showinfo("No Stored Thresholds", "No previous thresholds have been stored to average with.")
            return
        
        # Calculate new threshold values by averaging current and stored values
        count = self.stored_thresholds['count']
        new_count = count + 1
        
        # Calculate the weighted average of old and new values
        def weighted_avg(stored_val, current_val):
            return (stored_val * count + current_val) / new_count
        
        # Update stored threshold values with weighted averages
        self.stored_thresholds = {
            'count': new_count,
            'raw_lower': weighted_avg(self.stored_thresholds['raw_lower'], self.raw_lower),
            'raw_upper': weighted_avg(self.stored_thresholds['raw_upper'], self.raw_upper),
            'filtered_lower': weighted_avg(self.stored_thresholds['filtered_lower'], self.filtered_lower),
            'filtered_upper': weighted_avg(self.stored_thresholds['filtered_upper'], self.filtered_upper),
            'watershed_lower': weighted_avg(self.stored_thresholds['watershed_lower'], self.watershed_lower),
            'watershed_upper': weighted_avg(self.stored_thresholds['watershed_upper'], self.watershed_upper),
            'size_lower': weighted_avg(self.stored_thresholds['size_lower'], self.size_lower),
            'size_upper': weighted_avg(self.stored_thresholds['size_upper'], self.size_upper)
        }
        
        # Update UI sliders and variables with new averaged values
        self.raw_lower_var.set(self.stored_thresholds['raw_lower'])
        self.raw_upper_var.set(self.stored_thresholds['raw_upper'])
        self.filtered_lower_var.set(self.stored_thresholds['filtered_lower'])
        self.filtered_upper_var.set(self.stored_thresholds['filtered_upper'])
        self.watershed_lower_var.set(self.stored_thresholds['watershed_lower'])
        self.watershed_upper_var.set(self.stored_thresholds['watershed_upper'])
        self.size_lower_var.set(self.stored_thresholds['size_lower'])
        self.size_upper_var.set(self.stored_thresholds['size_upper'])
        
        # Update internal threshold values
        self.update_thresholds()
        
        messagebox.showinfo("Thresholds Updated", 
                        f"Thresholds have been updated with weighted average of {new_count} images.")

    def update_image_display(self, *args):
        """Update image display based on brightness and contrast settings"""
        self.update_visualization()

    def auto_adjust_image(self):
        """Automatically adjust image brightness and contrast"""
        if self.image_stack is None or self.current_z > self.max_z:
            return
        
        # Get current slice
        current_slice = self.image_stack[self.current_z]
        
        # Calculate p1 and p99 percentiles for auto adjustment
        p1 = np.percentile(current_slice, 1)
        p99 = np.percentile(current_slice, 99)
        
        # Calculate brightness and contrast adjustments
        contrast = 1.0
        if p99 > p1:
            contrast = 255.0 / (p99 - p1)
        brightness = -p1 * contrast / 255.0 + 0.5
        
        # Limit values to slider ranges
        brightness = max(0.1, min(3.0, brightness))
        contrast = max(0.1, min(3.0, contrast))
        
        # Update sliders
        self.brightness_var.set(brightness)
        self.contrast_var.set(contrast)
        
        # Update display
        self.update_visualization()
        
    def reset_image_display(self):
        """Reset image display settings to default"""
        self.brightness_var.set(1.0)
        self.contrast_var.set(1.0)
        self.update_visualization()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ThresholdVisualizer(root)
        root.mainloop()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()            