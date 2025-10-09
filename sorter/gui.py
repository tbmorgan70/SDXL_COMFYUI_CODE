"""
Sorter 2.3 - Modern GUI Interface

Beautiful, compact interface for all sorting operations with real-time progress tracking.
Built on the rock-solid command-line backend for maximum reliability.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from threading import Thread
import queue

# Limit size of progress queue to avoid uncontrolled growth
MAX_QUEUE_SIZE = 1000
from pathlib import Path

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.metadata_engine import MetadataExtractor, MetadataAnalyzer
from core.diagnostics import SortLogger
from sorters.checkpoint_sorter import CheckpointSorter
from sorters.lora_stack_sorter import LoRAStackSorter
from sorters.metadata_search import MetadataSearchSorter
from sorters.color_sorter import ColorSorter
from sorters.image_flattener import ImageFlattener
from sorters.metadata_generator import MetadataGenerator

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # "light" or "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class ProgressWindow(ctk.CTkToplevel):
    """Progress tracking window with real-time updates"""
    
    def __init__(self, parent, title="Processing...", output_dir=None):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("500x300")
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"500x300+{x}+{y}")
        
        # Store output directory for "Open Folder" functionality
        self.output_dir = output_dir
        
        # Create UI
        self.setup_ui()
        
        # Progress tracking
        self.current_operation = ""
        self.progress_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)

        # Start progress checker
        self.check_progress()

    def enqueue(self, item):
        """Safely add an update to the progress queue"""
        try:
            self.progress_queue.put_nowait(item)
        except queue.Full:
            pass
    
    def setup_ui(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            main_frame, 
            text="🚀 Processing Files...", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=10)
        
        # Current operation
        self.operation_label = ctk.CTkLabel(
            main_frame,
            text="Preparing...",
            font=ctk.CTkFont(size=14)
        )
        self.operation_label.pack(pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Progress text
        self.progress_label = ctk.CTkLabel(
            main_frame,
            text="0 / 0 files processed",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=5)
        
        # Current file
        self.file_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.file_label.pack(pady=5)
        
        # Log output
        self.log_text = ctk.CTkTextbox(main_frame, height=100)
        self.log_text.pack(fill="both", expand=True, pady=10)
        
        # Button frame for multiple buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=5, fill="x")
        
        # Open Output Folder button (initially hidden)
        self.open_folder_button = ctk.CTkButton(
            button_frame,
            text="📁 Open Output Folder",
            command=self.open_output_folder,
            fg_color="green",
            hover_color="darkgreen"
        )
        # Don't pack it initially - it will be shown on completion
        
        # Cancel/Close button
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            fg_color="red",
            hover_color="darkred"
        )
        self.cancel_button.pack(side="right", padx=5)
        
        self.cancelled = False
    
    def update_operation(self, operation):
        self.operation_label.configure(text=operation)
    
    def update_progress(self, completed, total, current_file=""):
        # Ensure completed and total are integers
        try:
            completed = int(completed)
            total = int(total)
        except (ValueError, TypeError):
            # If conversion fails, skip the update
            return
            
        if total > 0:
            progress = completed / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"{completed} / {total} files processed")
        
        if current_file:
            # Truncate long filenames
            if len(current_file) > 50:
                current_file = current_file[:47] + "..."
            self.file_label.configure(text=current_file)
    
    def log_message(self, message):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.update()
    
    def check_progress(self):
        """Check for progress updates from the queue"""
        log_batch = []
        try:
            while True:
                update_type, data = self.progress_queue.get_nowait()

                if update_type == "operation":
                    self.update_operation(data)
                elif update_type == "progress":
                    completed, total, current_file = data
                    self.update_progress(completed, total, current_file)
                elif update_type == "log":
                    log_batch.append(data)
                elif update_type == "complete":
                    self.on_complete(data)
                elif update_type == "error":
                    self.on_error(data)

                if len(log_batch) >= 10:
                    self.log_message("\n".join(log_batch))
                    log_batch = []

        except queue.Empty:
            pass

        if log_batch:
            self.log_message("\n".join(log_batch))

        # Schedule next check
        if not self.cancelled:
            self.after(100, self.check_progress)
    
    def on_complete(self, success):
        if success:
            self.title_label.configure(text="✅ Complete!")
            self.operation_label.configure(text="Operation completed successfully")
            self.cancel_button.configure(text="Close", fg_color="green", hover_color="darkgreen")
            
            # Debug logging for output directory
            self.log_message(f"🔍 Debug: output_dir = '{self.output_dir}'")
            if self.output_dir:
                self.log_message(f"🔍 Debug: Directory exists = {os.path.exists(self.output_dir)}")
            
            # Show "Open Output Folder" button if output directory exists
            if self.output_dir and os.path.exists(self.output_dir):
                self.open_folder_button.pack(side="left", padx=5)
                self.update_idletasks()  # Force UI update
                self.log_message("📁 Open Output Folder button added")
            else:
                self.log_message("❌ Open Output Folder button NOT added")
            
            # Remove auto-close to let user decide when to close
        else:
            self.title_label.configure(text="❌ Failed!")
            self.operation_label.configure(text="Operation failed")
            self.cancel_button.configure(text="Close", fg_color="red", hover_color="darkred")
    
    def on_error(self, error_msg):
        self.title_label.configure(text="❌ Error!")
        self.operation_label.configure(text="An error occurred")
        self.log_message(f"ERROR: {error_msg}")
        self.cancel_button.configure(text="Close", fg_color="red", hover_color="darkred")
    
    def open_output_folder(self):
        """Open the output folder in the system file explorer"""
        if self.output_dir and os.path.exists(self.output_dir):
            try:
                # Windows
                if os.name == 'nt':
                    os.startfile(self.output_dir)
                # macOS
                elif sys.platform == 'darwin':
                    os.system(f'open "{self.output_dir}"')
                # Linux and others
                else:
                    os.system(f'xdg-open "{self.output_dir}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {str(e)}")
        else:
            messagebox.showwarning("Warning", "Output folder not found or doesn't exist")
    
    def on_cancel(self):
        self.cancelled = True
        self.destroy()

class SorterGUI(ctk.CTk):
    """Main Sorter 2.0 GUI Application - Compact Design"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window - compact size like unified_sorter
        self.title("🚀 Sorter 2.3 - Advanced ComfyUI Image Organizer")
        self.geometry("750x700")
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (750 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"750x700+{x}+{y}")
        
        # Initialize logger
        self.logger = SortLogger()
        
        # Initialize variables
        self.source_dir = ""
        self.output_dir = ""
        self.current_operation = None
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        # Configure main padding
        self.configure(padx=20, pady=20)
        
        # Header - compact
        header_frame = ctk.CTkFrame(self, corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🚀 Sorter 2.3 - ComfyUI Image Organizer",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=15)
        
        # Mode Selection - like unified_sorter
        mode_frame = ctk.CTkFrame(self, corner_radius=10)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        mode_inner = ctk.CTkFrame(mode_frame)
        mode_inner.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(mode_inner, text="Sort Mode:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        self.mode_var = ctk.StringVar(value="Sort by Checkpoint")
        self.mode_menu = ctk.CTkOptionMenu(
            mode_inner, 
            variable=self.mode_var,
            values=["Sort by Checkpoint", "Sort by LoRA Stack", "Search & Sort", "Sort by Color", "Flatten Images", "Generate Metadata", "View Session Logs"],
            command=self._switch_mode
        )
        self.mode_menu.pack(side="left", padx=(10, 0))
        
        # Dynamic form area
        self.forms_frame = ctk.CTkFrame(self, corner_radius=10)
        self.forms_frame.pack(fill="x", pady=(0, 15))
        
        # Individual mode frames
        self.checkpoint_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.lora_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.search_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.color_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.flatten_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.metadata_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.logs_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        
        # Build all forms
        self._build_checkpoint_form()
        self._build_lora_form()
        self._build_search_form()
        self._build_color_form()
        self._build_flatten_form()
        self._build_metadata_form()
        self._build_logs_form()
        
        # Run button
        self.run_btn = ctk.CTkButton(
            self, 
            text="🚀 Run Operation",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            command=self.run_operation
        )
        self.run_btn.pack(fill="x", pady=(0, 15))
        
        # Status/Log area - compact
        self.status_frame = ctk.CTkFrame(self, corner_radius=10)
        self.status_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            self.status_frame, 
            text="� Status Log:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.status_text = ctk.CTkTextbox(self.status_frame, height=150)
        self.status_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Initialize with first mode
        self._switch_mode("Sort by Checkpoint")
        self.log_message("🚀 Sorter 2.3 initialized. Select your sorting mode and configure options.")
    
    def _build_checkpoint_form(self):
        """Build checkpoint sorting form - matches main.py exactly"""
        # Source directory
        src_row = ctk.CTkFrame(self.checkpoint_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Source Directory", command=lambda: self._choose_directory("source")).pack(side="left")
        self.checkpoint_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.checkpoint_src_label.pack(side="left", padx=(10, 0))
        
        # Output directory
        out_row = ctk.CTkFrame(self.checkpoint_frame)
        out_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(out_row, text="📂 Select Output Directory (Optional)", command=lambda: self._choose_directory("output")).pack(side="left")
        self.checkpoint_out_label = ctk.CTkLabel(out_row, text="Will create 'sorted' subfolder if not set", text_color="#888")
        self.checkpoint_out_label.pack(side="left", padx=(10, 0))
        
        # Options row 1
        opts1 = ctk.CTkFrame(self.checkpoint_frame)
        opts1.pack(fill="x", padx=15, pady=5)
        
        self.checkpoint_move_var = ctk.BooleanVar(value=False)
        self.checkpoint_metadata_var = ctk.BooleanVar(value=True)
        self.checkpoint_rename_var = ctk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(opts1, text="Move files (instead of copy)", variable=self.checkpoint_move_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(opts1, text="Create metadata files", variable=self.checkpoint_metadata_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(opts1, text="Rename files", variable=self.checkpoint_rename_var).pack(side="left")
        
        # Rename options row
        rename_row = ctk.CTkFrame(self.checkpoint_frame)
        rename_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(rename_row, text="Rename Prefix:").pack(side="left")
        self.checkpoint_prefix_entry = ctk.CTkEntry(rename_row, width=150, placeholder_text="e.g. nova_skyrift")
        self.checkpoint_prefix_entry.pack(side="left", padx=(10, 20))
        
        # Grouping options
        group_row = ctk.CTkFrame(self.checkpoint_frame)
        group_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(group_row, text="Grouping:").pack(side="left")
        self.checkpoint_grouping_var = ctk.StringVar(value="Checkpoint Only")
        group_menu = ctk.CTkOptionMenu(group_row, variable=self.checkpoint_grouping_var,
                                     values=["Checkpoint Only", "Checkpoint + LoRA Stack"])
        group_menu.pack(side="left", padx=(10, 0))
        
        # Info
        info_label = ctk.CTkLabel(self.checkpoint_frame, 
                                 text="🎯 Organizes images by their base checkpoint models. Your #1 priority feature!",
                                 text_color="#aaa", font=ctk.CTkFont(size=11))
        info_label.pack(padx=15, pady=(5, 15))
    
    def _build_lora_form(self):
        """Build LoRA stack sorting form"""
        # Source directory
        src_row = ctk.CTkFrame(self.lora_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Source Directory", command=lambda: self._choose_directory("source")).pack(side="left")
        self.lora_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.lora_src_label.pack(side="left", padx=(10, 0))
        
        # Output directory
        out_row = ctk.CTkFrame(self.lora_frame)
        out_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(out_row, text="📂 Select Output Directory (Optional)", command=lambda: self._choose_directory("output")).pack(side="left")
        self.lora_out_label = ctk.CTkLabel(out_row, text="Will create 'lora_sorted' subfolder if not set", text_color="#888")
        self.lora_out_label.pack(side="left", padx=(10, 0))
        
        # Options row 1
        opts1 = ctk.CTkFrame(self.lora_frame)
        opts1.pack(fill="x", padx=15, pady=5)
        
        self.lora_move_var = ctk.BooleanVar(value=False)
        self.lora_metadata_var = ctk.BooleanVar(value=True)
        self.lora_rename_var = ctk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(opts1, text="Move files", variable=self.lora_move_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(opts1, text="Create metadata files", variable=self.lora_metadata_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(opts1, text="Rename files", variable=self.lora_rename_var).pack(side="left")
        
        # Rename row
        rename_row = ctk.CTkFrame(self.lora_frame)
        rename_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(rename_row, text="Rename Prefix:").pack(side="left")
        self.lora_prefix_entry = ctk.CTkEntry(rename_row, width=150, placeholder_text="e.g. lora_stack")
        self.lora_prefix_entry.pack(side="left", padx=(10, 20))
        
        # Info
        info_label = ctk.CTkLabel(self.lora_frame, 
                                 text="🎨 Sorts images purely by LoRA combinations - ignores checkpoints, VAE, and other settings",
                                 text_color="#aaa", font=ctk.CTkFont(size=11))
        info_label.pack(padx=15, pady=(5, 15))
    
    def _build_search_form(self):
        """Build search & sort form"""
        # Source directory
        src_row = ctk.CTkFrame(self.search_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Source Directory", command=lambda: self._choose_directory("source")).pack(side="left")
        self.search_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.search_src_label.pack(side="left", padx=(10, 0))
        
        # Search terms
        search_row = ctk.CTkFrame(self.search_frame)
        search_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(search_row, text="Search Terms:").pack(side="left")
        self.search_entry = ctk.CTkEntry(search_row, width=300, placeholder_text="Enter search terms (comma-separated)")
        self.search_entry.pack(side="left", padx=(10, 0))
        
        # Search mode
        mode_row = ctk.CTkFrame(self.search_frame)
        mode_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(mode_row, text="Search Mode:").pack(side="left")
        self.search_mode_var = ctk.StringVar(value="Any term (OR)")
        search_menu = ctk.CTkOptionMenu(mode_row, variable=self.search_mode_var,
                                      values=["Any term (OR)", "All terms (AND)", "Exact match"])
        search_menu.pack(side="left", padx=(10, 20))
        
        self.search_case_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(mode_row, text="Case sensitive", variable=self.search_case_var).pack(side="left")
        
        # Output directory
        out_row = ctk.CTkFrame(self.search_frame)
        out_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(out_row, text="📂 Select Output Directory (Optional)", command=lambda: self._choose_directory("output")).pack(side="left")
        self.search_out_label = ctk.CTkLabel(out_row, text="Will create 'search_results' subfolder if not set", text_color="#888")
        self.search_out_label.pack(side="left", padx=(10, 0))
        
        # Options
        opts = ctk.CTkFrame(self.search_frame)
        opts.pack(fill="x", padx=15, pady=5)
        self.search_move_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opts, text="Move files (instead of copy)", variable=self.search_move_var).pack(side="left")
        
        # Info
        info_label = ctk.CTkLabel(self.search_frame, 
                                 text="🔍 Find images by metadata content - LoRAs, prompts, settings, etc.",
                                 text_color="#aaa", font=ctk.CTkFont(size=11))
        info_label.pack(padx=15, pady=(5, 15))
    
    def _build_color_form(self):
        """Build color sorting form"""
        # Source directory
        src_row = ctk.CTkFrame(self.color_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Source Directory", command=lambda: self._choose_directory("source")).pack(side="left")
        self.color_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.color_src_label.pack(side="left", padx=(10, 0))
        
        # Output directory
        out_row = ctk.CTkFrame(self.color_frame)
        out_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(out_row, text="📂 Select Output Directory (Optional)", command=lambda: self._choose_directory("output")).pack(side="left")
        self.color_out_label = ctk.CTkLabel(out_row, text="Will create 'color_sorted' subfolder if not set", text_color="#888")
        self.color_out_label.pack(side="left", padx=(10, 0))
        
        # Options row 1
        opts1 = ctk.CTkFrame(self.color_frame)
        opts1.pack(fill="x", padx=15, pady=5)
        
        self.color_move_var = ctk.BooleanVar(value=False)
        self.color_metadata_var = ctk.BooleanVar(value=True)
        self.color_rename_var = ctk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(opts1, text="Move files", variable=self.color_move_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(opts1, text="Create metadata files", variable=self.color_metadata_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(opts1, text="Rename files", variable=self.color_rename_var).pack(side="left")
        
        # Rename and threshold row
        opts2 = ctk.CTkFrame(self.color_frame)
        opts2.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(opts2, text="Prefix:").pack(side="left")
        self.color_prefix_entry = ctk.CTkEntry(opts2, width=120, placeholder_text="e.g. myproject")
        self.color_prefix_entry.pack(side="left", padx=(5, 20))
        ctk.CTkLabel(opts2, text="Dark threshold:").pack(side="left")
        self.color_threshold_entry = ctk.CTkEntry(opts2, width=80, placeholder_text="0.1")
        self.color_threshold_entry.pack(side="left", padx=(5, 0))
        
        # Info
        info_label = ctk.CTkLabel(self.color_frame, 
                                 text="🌈 Organizes images by dominant colors - supports PNG, JPG, GIF, BMP, TIFF, WebP",
                                 text_color="#aaa", font=ctk.CTkFont(size=11))
        info_label.pack(padx=15, pady=(5, 15))
    
    def _build_flatten_form(self):
        """Build flatten images form"""
        # Source directory
        src_row = ctk.CTkFrame(self.flatten_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Nested Source Directory", command=lambda: self._choose_directory("source")).pack(side="left")
        self.flatten_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.flatten_src_label.pack(side="left", padx=(10, 0))
        
        # Output directory
        out_row = ctk.CTkFrame(self.flatten_frame)
        out_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(out_row, text="📂 Select Output Directory (Optional)", command=lambda: self._choose_directory("output")).pack(side="left")
        self.flatten_out_label = ctk.CTkLabel(out_row, text="Will create 'flattened' subfolder if not set", text_color="#888")
        self.flatten_out_label.pack(side="left", padx=(10, 0))
        
        # Options
        opts = ctk.CTkFrame(self.flatten_frame)
        opts.pack(fill="x", padx=15, pady=5)
        
        self.flatten_move_var = ctk.BooleanVar(value=False)
        self.flatten_remove_empty_var = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(opts, text="Move files (instead of copy)", variable=self.flatten_move_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(opts, text="Remove empty directories", variable=self.flatten_remove_empty_var).pack(side="left")
        
        # Info
        info_label = ctk.CTkLabel(self.flatten_frame, 
                                 text="📂 Consolidates all images from nested folders into a single directory",
                                 text_color="#aaa", font=ctk.CTkFont(size=11))
        info_label.pack(padx=15, pady=(5, 15))
    
    def _build_logs_form(self):
        """Build view logs form"""
        info_frame = ctk.CTkFrame(self.logs_frame)
        info_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(info_frame, 
                    text="📊 View Previous Session Logs",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 20))
        
        ctk.CTkLabel(info_frame, 
                    text="Click 'Run Operation' to view your previous sorting session logs.\n" +
                         "Logs contain detailed information about:\n" +
                         "• Files processed and results\n" +
                         "• Any errors encountered\n" +
                         "• Performance statistics",
                    font=ctk.CTkFont(size=12),
                    text_color="#aaa").pack(pady=10)
    
    def _build_metadata_form(self):
        """Build metadata generation form"""
        # Source directory
        src_row = ctk.CTkFrame(self.metadata_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Source Directory", command=lambda: self._choose_directory("source")).pack(side="left")
        self.metadata_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.metadata_src_label.pack(side="left", padx=(10, 0))
        
        # Output directory
        out_row = ctk.CTkFrame(self.metadata_frame)
        out_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(out_row, text="📂 Select Output Directory", command=lambda: self._choose_directory("output")).pack(side="left")
        self.metadata_out_label = ctk.CTkLabel(out_row, text="No folder selected", text_color="#888")
        self.metadata_out_label.pack(side="left", padx=(10, 0))
        
        # Options
        opts = ctk.CTkFrame(self.metadata_frame)
        opts.pack(fill="x", padx=15, pady=5)
        
        self.metadata_overwrite_var = ctk.BooleanVar(value=False)
        self.metadata_recursive_var = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(opts, text="Overwrite existing metadata files", variable=self.metadata_overwrite_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(opts, text="Include subdirectories", variable=self.metadata_recursive_var).pack(side="left")
        
        # Info
        info_label = ctk.CTkLabel(self.metadata_frame, 
                                 text="📄 Generate metadata text files without moving or organizing images",
                                 text_color="#aaa", font=ctk.CTkFont(size=11))
        info_label.pack(padx=15, pady=(5, 15))
    
    def _choose_directory(self, dir_type):
        """Choose directory and update appropriate labels"""
        if dir_type == "source":
            directory = filedialog.askdirectory(title="Select Source Directory")
            if directory:
                self.source_dir = directory
                # Update current mode's source label
                if self.mode_var.get() == "Sort by Checkpoint":
                    self.checkpoint_src_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Search & Sort":
                    self.search_src_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Sort by Color":
                    self.color_src_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Flatten Images":
                    self.flatten_src_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Sort by LoRA Stack":
                    self.lora_src_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Generate Metadata":
                    self.metadata_src_label.configure(text=os.path.basename(directory))
                
                self.log_message(f"📁 Source directory selected: {directory}")
        
        elif dir_type == "output":
            directory = filedialog.askdirectory(title="Select Output Directory")
            if directory:
                self.output_dir = directory
                # Update current mode's output label
                if self.mode_var.get() == "Sort by Checkpoint":
                    self.checkpoint_out_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Search & Sort":
                    self.search_out_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Sort by Color":
                    self.color_out_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Flatten Images":
                    self.flatten_out_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Sort by LoRA Stack":
                    self.lora_out_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Generate Metadata":
                    self.metadata_out_label.configure(text=os.path.basename(directory))
                
                self.log_message(f"📂 Output directory selected: {directory}")
    
    def _switch_mode(self, choice=None):
        """Switch between different sorting modes"""
        # Hide all frames
        for frame in [self.checkpoint_frame, self.lora_frame, self.search_frame, self.color_frame, self.flatten_frame, self.metadata_frame, self.logs_frame]:
            frame.pack_forget()
        
        # Show selected frame
        mode = self.mode_var.get()
        if mode == "Sort by Checkpoint":
            self.checkpoint_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("🎯 Checkpoint sorting mode selected")
        elif mode == "Sort by LoRA Stack":
            self.lora_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("🎨 LoRA stack sorting mode selected")
        elif mode == "Search & Sort":
            self.search_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("🔍 Search & sort mode selected")
        elif mode == "Sort by Color":
            self.color_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("🌈 Color sorting mode selected")
        elif mode == "Flatten Images":
            self.flatten_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("📂 Flatten images mode selected")
        elif mode == "Generate Metadata":
            self.metadata_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("📄 Generate metadata mode selected")
        elif mode == "View Session Logs":
            self.logs_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("📊 View logs mode selected")
    
    def log_message(self, message):
        """Add message to status log"""
        self.status_text.insert("end", f"{message}\n")
        self.status_text.see("end")
        self.update()
    
    def run_operation(self):
        """Run the selected operation"""
        mode = self.mode_var.get()
        
        if mode == "Sort by Checkpoint":
            self.sort_by_checkpoint()
        elif mode == "Sort by LoRA Stack":
            self.sort_by_lora_stack()
        elif mode == "Search & Sort":
            self.search_and_sort()
        elif mode == "Sort by Color":
            self.sort_by_color()
        elif mode == "Flatten Images":
            self.flatten_images()
        elif mode == "Generate Metadata":
            self.generate_metadata()
        elif mode == "View Session Logs":
            self.view_session_logs()
    
    def sort_by_checkpoint(self):
        """Sort images by checkpoint - matches main.py exactly"""
        if not self.source_dir:
            messagebox.showerror("Error", "Please select a source directory")
            return
        
        if not os.path.exists(self.source_dir):
            messagebox.showerror("Error", "Source directory does not exist")
            return
        
        # Count PNG files
        png_files = [f for f in os.listdir(self.source_dir) if f.lower().endswith('.png')]
        if not png_files:
            messagebox.showerror("Error", "No PNG files found in source directory")
            return
        
        self.log_message(f"📊 Found {len(png_files)} PNG files to sort")
        
        # Get output directory
        output_dir = self.output_dir if self.output_dir else os.path.join(self.source_dir, "sorted")
        
        # Get user options
        move_files = self.checkpoint_move_var.get()
        create_metadata = self.checkpoint_metadata_var.get()
        rename_files = self.checkpoint_rename_var.get()
        user_prefix = self.checkpoint_prefix_entry.get().strip() if rename_files else ""
        group_by_lora = self.checkpoint_grouping_var.get() == "Checkpoint + LoRA Stack"
        
        # Validate prefix if renaming
        if rename_files and not user_prefix:
            messagebox.showerror("Error", "Prefix is required for renaming. Using default 'image'.")
            user_prefix = "image"
        
        # Confirm operation
        operation = "MOVE" if move_files else "COPY"
        grouping = "Checkpoint + LoRA Stack" if group_by_lora else "Checkpoint Only"
        
        confirmation = messagebox.askyesno(
            "Confirm Checkpoint Sorting",
            f"📋 CONFIRMATION:\n" +
            f"   Source: {self.source_dir}\n" +
            f"   Output: {output_dir}\n" +
            f"   Files: {len(png_files)} PNG files\n" +
            f"   Operation: {operation}\n" +
            f"   Metadata files: {'Yes' if create_metadata else 'No'}\n" +
            f"   Grouping: {grouping}\n" +
            f"   Rename files: {'Yes' if rename_files else 'No'}\n" +
            (f"   Naming pattern: {user_prefix}_img1, {user_prefix}_img2, etc.\n" if rename_files and user_prefix else "") +
            f"\nProceed with sorting?"
        )
        
        if not confirmation:
            return
        
        # Show progress window and run in background
        progress_window = ProgressWindow(self, "Sorting by Checkpoint", output_dir)
        
        def run_sort():
            try:
                sorter = CheckpointSorter(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.enqueue(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                progress_window.enqueue(("operation", "Sorting by checkpoint..."))
                
                results = sorter.sort_by_checkpoint(
                    source_dir=self.source_dir,
                    output_dir=output_dir,
                    move_files=move_files,
                    create_metadata_files=create_metadata,
                    rename_files=rename_files,
                    user_prefix=user_prefix,
                    group_by_lora_stack=group_by_lora
                )
                
                # Show results
                if results:
                    stats = results.get('sorter_stats', {})
                    success_msg = f"✅ SORTING COMPLETE!\n" + \
                                f"   Sorted: {stats.get('sorted_images', 0)}/{stats.get('total_images', 0)} images\n" + \
                                f"   Folders created: {stats.get('folders_created', 0)}\n" + \
                                f"   Unknown checkpoints: {stats.get('unknown_checkpoint', 0)}"
                    progress_window.enqueue(("log", success_msg))
                
                progress_window.enqueue(("complete", True))
                
            except Exception as e:
                progress_window.enqueue(("error", str(e)))
        
        Thread(target=run_sort, daemon=True).start()
    
    def sort_by_lora_stack(self):
        """Sort images by LoRA stack combinations - GUI implementation"""
        if not self.source_dir:
            messagebox.showerror("Error", "Please select a source directory")
            return
        
        if not os.path.exists(self.source_dir):
            messagebox.showerror("Error", "Source directory does not exist")
            return
        
        # Count PNG files
        png_files = [f for f in os.listdir(self.source_dir) if f.lower().endswith('.png')]
        if not png_files:
            messagebox.showerror("Error", "No PNG files found in source directory")
            return
        
        self.log_message(f"📊 Found {len(png_files)} PNG files to sort")
        
        # Get output directory
        output_dir = self.output_dir if self.output_dir else os.path.join(self.source_dir, "lora_sorted")
        
        # Get user options
        move_files = self.lora_move_var.get()
        create_metadata = self.lora_metadata_var.get()
        rename_files = self.lora_rename_var.get()
        user_prefix = self.lora_prefix_entry.get().strip() if rename_files else ""
        
        # Validate prefix if renaming
        if rename_files and not user_prefix:
            messagebox.showerror("Error", "Prefix is required for renaming. Using default 'lora'.")
            user_prefix = "lora"
        
        # Confirm operation
        operation = "MOVE" if move_files else "COPY"
        
        confirmation = messagebox.askyesno(
            "Confirm LoRA Stack Sorting",
            f"📋 CONFIRMATION:\n" +
            f"   Source: {self.source_dir}\n" +
            f"   Output: {output_dir}\n" +
            f"   Files: {len(png_files)} PNG files\n" +
            f"   Operation: {operation}\n" +
            f"   Metadata files: {'Yes' if create_metadata else 'No'}\n" +
            f"   Grouping: LoRA Stack Only\n" +
            f"   Rename files: {'Yes' if rename_files else 'No'}\n" +
            (f"   Naming pattern: {user_prefix}_001, {user_prefix}_002, etc.\n" if rename_files and user_prefix else "") +
            f"\nProceed with sorting?"
        )
        
        if not confirmation:
            return
        
        # Show progress window and run in background
        progress_window = ProgressWindow(self, "Sorting by LoRA Stack", output_dir)
        
        def run_sort():
            try:
                # Create sorter and run operation
                lora_sorter = LoRAStackSorter()
                
                result = lora_sorter.sort_by_lora_stack(
                    source_dir=self.source_dir,
                    output_dir=output_dir,
                    move_files=move_files,
                    create_metadata=create_metadata,
                    rename_files=rename_files,
                    rename_prefix=user_prefix,
                    progress_callback=progress_window.update_progress
                )
                
                # Signal completion
                progress_window.enqueue(("complete", True))
                
            except Exception as e:
                progress_window.enqueue(("error", str(e)))
        
        Thread(target=run_sort, daemon=True).start()
    
    def search_and_sort(self):
        """Search and sort by metadata - matches main.py"""
        if not self.source_dir:
            messagebox.showerror("Error", "Please select a source directory")
            return
        
        # Get search terms
        search_text = self.search_entry.get().strip()
        if not search_text:
            messagebox.showerror("Error", "Please enter search terms")
            return
        
        search_terms = [term.strip() for term in search_text.split(",") if term.strip()]
        
        # Map GUI mode to backend mode
        mode_mapping = {
            "Any term (OR)": "any",
            "All terms (AND)": "all", 
            "Exact match": "exact"
        }
        search_mode = mode_mapping.get(self.search_mode_var.get(), "any")
        case_sensitive = self.search_case_var.get()
        
        # Get output directory
        output_dir = self.output_dir if self.output_dir else os.path.join(self.source_dir, "search_results")
        move_files = self.search_move_var.get()
        
        # Count PNG files
        png_files = [f for f in os.listdir(self.source_dir) if f.lower().endswith('.png')]
        if not png_files:
            messagebox.showerror("Error", "No PNG files found in source directory")
            return
        
        # Confirm operation
        operation = "MOVE" if move_files else "COPY"
        confirmation = messagebox.askyesno(
            "Confirm Search & Sort",
            f"📋 SEARCH CONFIGURATION:\n" +
            f"   Files: {len(png_files)} PNG files\n" +
            f"   Terms: {search_terms}\n" +
            f"   Mode: {search_mode.upper()}\n" +
            f"   Case sensitive: {case_sensitive}\n" +
            f"   Operation: {operation}\n" +
            f"   Output: {output_dir}\n\n" +
            f"Proceed with search?"
        )
        
        if not confirmation:
            return
        
        # Show progress window and run in background
        progress_window = ProgressWindow(self, "Searching & Sorting", output_dir)
        
        def run_search():
            try:
                searcher = MetadataSearchSorter(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.enqueue(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                progress_window.enqueue(("operation", f"Searching for: {', '.join(search_terms)}"))
                
                results = searcher.search_and_sort(
                    source_dir=self.source_dir,
                    output_dir=output_dir,
                    search_terms=search_terms,
                    search_mode=search_mode,
                    move_files=move_files,
                    case_sensitive=case_sensitive
                )
                
                # Show results
                if results:
                    stats = results.get('search_stats', {})
                    success_msg = f"✅ Search complete!\n" + \
                                f"   Found: {stats.get('images_matched', 0)} matching images\n" + \
                                f"   Sorted: {stats.get('images_sorted', 0)} images"
                    progress_window.enqueue(("log", success_msg))
                
                progress_window.enqueue(("complete", True))
                
            except Exception as e:
                progress_window.enqueue(("error", str(e)))
        
        Thread(target=run_search, daemon=True).start()
    
    def sort_by_color(self):
        """Sort images by color - matches main.py"""
        if not self.source_dir:
            messagebox.showerror("Error", "Please select a source directory")
            return
        
        # Count image files
        from pathlib import Path
        source_path = Path(self.source_dir)
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(source_path.glob(f'*{ext}'))
            image_files.extend(source_path.glob(f'*{ext.upper()}'))
        
        if not image_files:
            messagebox.showerror("Error", "No image files found")
            return
        
        self.log_message(f"📊 Found {len(image_files)} image files to sort")
        
        # Get options
        output_dir = self.output_dir if self.output_dir else os.path.join(self.source_dir, "color_sorted")
        move_files = self.color_move_var.get()
        create_metadata = self.color_metadata_var.get()
        rename_files = self.color_rename_var.get()
        user_prefix = self.color_prefix_entry.get().strip() if rename_files else ""
        
        # Get dark threshold
        threshold_text = self.color_threshold_entry.get().strip()
        try:
            dark_threshold = float(threshold_text) if threshold_text else 0.1
            dark_threshold = max(0.0, min(1.0, dark_threshold))
        except ValueError:
            dark_threshold = 0.1
        
        # Confirm operation
        operation = "MOVE" if move_files else "COPY"
        confirmation = messagebox.askyesno(
            "Confirm Color Sorting",
            f"📋 CONFIRMATION:\n" +
            f"   Source: {self.source_dir}\n" +
            f"   Output: {output_dir}\n" +
            f"   Files: {len(image_files)} image files\n" +
            f"   Operation: {operation}\n" +
            f"   Metadata files: {'Yes' if create_metadata else 'No'}\n" +
            f"   Rename files: {'Yes' if rename_files else 'No'}\n" +
            (f"   Prefix: '{user_prefix}' (e.g. {user_prefix}_red_img1.png)\n" if rename_files and user_prefix else "") +
            f"   Dark threshold: {dark_threshold}\n\n" +
            f"Proceed with color sorting?"
        )
        
        if not confirmation:
            return
        
        # Show progress window and run in background
        progress_window = ProgressWindow(self, "Sorting by Color", output_dir)
        
        def run_sort():
            try:
                color_sorter = ColorSorter(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.enqueue(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                progress_window.enqueue(("operation", "Analyzing colors and sorting..."))
                
                success = color_sorter.sort_by_color(
                    source_dir=self.source_dir,
                    output_dir=output_dir,
                    move_files=move_files,
                    create_metadata=create_metadata,
                    ignore_dark_threshold=dark_threshold,
                    rename_files=rename_files,
                    user_prefix=user_prefix
                )
                
                if success:
                    progress_window.enqueue(("log", "✅ COLOR SORTING COMPLETE!"))
                
                progress_window.enqueue(("complete", success))
                
            except Exception as e:
                progress_window.enqueue(("error", str(e)))
        
        Thread(target=run_sort, daemon=True).start()
    
    def flatten_images(self):
        """Flatten nested image folders - matches main.py"""
        if not self.source_dir:
            messagebox.showerror("Error", "Please select a source directory")
            return
        
        # Preview first
        flattener = ImageFlattener(self.logger)
        preview_data = flattener.preview_flatten(self.source_dir)
        
        if preview_data['total_images'] == 0:
            messagebox.showerror("Error", "No image files found in directory or subdirectories")
            return
        
        # Get options
        output_dir = self.output_dir if self.output_dir else os.path.join(self.source_dir, "flattened")
        move_files = self.flatten_move_var.get()
        remove_empty = self.flatten_remove_empty_var.get()
        
        # Confirm operation
        operation = "MOVE" if move_files else "COPY"
        confirmation = messagebox.askyesno(
            "Confirm Flatten Images",
            f"📋 CONFIRMATION:\n" +
            f"   Source: {self.source_dir}\n" +
            f"   Target: {output_dir}\n" +
            f"   Images: {preview_data['total_images']} files\n" +
            f"   Folders: {preview_data['folders']} folders\n" +
            f"   Operation: {operation}\n" +
            f"   Remove empty dirs: {'Yes' if remove_empty else 'No'}\n" +
            f"   Duplicates to rename: {preview_data['duplicates']}\n\n" +
            f"Proceed with flattening?"
        )
        
        if not confirmation:
            return
        
        # Show progress window and run in background
        progress_window = ProgressWindow(self, "Flattening Images", output_dir)
        
        def run_flatten():
            try:
                flattener = ImageFlattener(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.enqueue(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                progress_window.enqueue(("operation", "Flattening image folders..."))
                
                success = flattener.flatten_images(
                    source_dir=self.source_dir,
                    target_dir=output_dir,
                    move_files=move_files,
                    remove_empty_dirs=remove_empty
                )
                
                if success:
                    progress_window.enqueue(("log", "✅ IMAGE FLATTENING COMPLETE!"))
                
                progress_window.enqueue(("complete", success))
                
            except Exception as e:
                progress_window.enqueue(("error", str(e)))
        
        Thread(target=run_flatten, daemon=True).start()
    
    def view_session_logs(self):
        """View previous session logs - matches main.py"""
        logs_dir = os.path.join(os.getcwd(), "sort_logs")
        if not os.path.exists(logs_dir):
            messagebox.showerror("Error", "No logs directory found")
            return
        
        log_files = [f for f in os.listdir(logs_dir) if f.startswith('sort_') and f.endswith('.log')]
        
        if not log_files:
            messagebox.showerror("Error", "No log files found")
            return
        
        # Show log selection dialog
        self.show_log_viewer(logs_dir, log_files)
    
    def show_log_viewer(self, logs_dir, log_files):
        """Show a dialog to select and view log files"""
        log_window = ctk.CTkToplevel(self)
        log_window.title("📊 Session Logs")
        log_window.geometry("800x600")
        log_window.transient(self)
        log_window.grab_set()
        
        # Center window
        log_window.update_idletasks()
        x = (log_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (log_window.winfo_screenheight() // 2) - (600 // 2)
        log_window.geometry(f"800x600+{x}+{y}")
        
        # Title
        ctk.CTkLabel(
            log_window,
            text="📊 Previous Session Logs",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)
        
        # Log file selection
        select_frame = ctk.CTkFrame(log_window)
        select_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(select_frame, text="Select log file:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        log_var = ctk.StringVar(value=sorted(log_files, reverse=True)[0])
        log_menu = ctk.CTkOptionMenu(
            select_frame,
            variable=log_var,
            values=sorted(log_files, reverse=True)[:10],  # Show last 10 log files
            command=lambda choice: self.load_log_content(logs_dir, choice, log_text)
        )
        log_menu.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Log content area
        log_text = ctk.CTkTextbox(log_window, height=400)
        log_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Load first log file
        self.load_log_content(logs_dir, log_var.get(), log_text)
        
        # Close button
        ctk.CTkButton(
            log_window,
            text="Close",
            command=log_window.destroy,
            width=100
        ).pack(pady=(0, 20))
    
    def load_log_content(self, logs_dir, log_file, text_widget):
        """Load and display log file content"""
        try:
            log_path = os.path.join(logs_dir, log_file)
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", content)
            
        except Exception as e:
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", f"Error loading log file: {e}")

    def generate_metadata(self):
        """Generate metadata files without moving or organizing images"""
        if not self.source_dir:
            messagebox.showerror("Error", "Please select a source directory")
            return
        
        if not self.output_dir:
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        if not os.path.exists(self.source_dir):
            messagebox.showerror("Error", "Source directory does not exist")
            return
        
        # Get user options
        overwrite_existing = self.metadata_overwrite_var.get()
        include_subdirs = self.metadata_recursive_var.get()
        
        self.log_message("📄 Starting metadata generation...")
        
        try:
            # Create and run progress window
            progress_window = ProgressWindow(
                parent=self,
                title="Generating Metadata",
                output_dir=self.output_dir
            )
            
            # Create metadata generator and run operation
            metadata_gen = MetadataGenerator()
            
            def run_generation():
                result = metadata_gen.generate_metadata_files(
                    source_dir=self.source_dir,
                    output_dir=self.output_dir,
                    overwrite_existing=overwrite_existing,
                    include_subdirectories=include_subdirs,
                    progress_callback=progress_window.update_progress
                )
                
                # Extract stats for display
                generator_stats = result.get('generator_stats', {})
                success = generator_stats.get('processed_images', 0) > 0
                
                # Log summary to the progress window
                if success:
                    progress_window.log_message(f"✅ Generated {generator_stats.get('metadata_files_created', 0)} metadata files")
                    progress_window.log_message(f"📊 Processed {generator_stats.get('processed_images', 0)} images")
                else:
                    progress_window.log_message("❌ No files were processed")
                
                # Complete the progress window
                progress_window.on_complete(success)
            
            # Run in separate thread
            import threading
            thread = threading.Thread(target=run_generation)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.log_message(f"❌ Error during metadata generation: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate metadata: {str(e)}")

def main():
    """Launch the Sorter 2.3 GUI"""
    try:
        app = SorterGUI()
        app.mainloop()
    except Exception as e:
        print(f"Error launching GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
