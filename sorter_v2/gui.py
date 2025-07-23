"""
Sorter 2.0 - Modern GUI Interface

Beautiful, intuitive interface for all sorting operations with real-time progress tracking.
Built on the rock-solid command-line backend for maximum reliability.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from threading import Thread
import queue
from pathlib import Path

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.metadata_engine import MetadataExtractor
from core.diagnostics import SortLogger
from sorters.checkpoint_sorter import CheckpointSorter
from sorters.metadata_search import MetadataSearchSorter
from sorters.color_sorter import ColorSorter
from sorters.image_flattener import ImageFlattener
from sorters.filename_cleanup import FilenameCleanup

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # "light" or "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class ProgressWindow(ctk.CTkToplevel):
    """Progress tracking window with real-time updates"""
    
    def __init__(self, parent, title="Processing..."):
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
        
        # Create UI
        self.setup_ui()
        
        # Progress tracking
        self.current_operation = ""
        self.progress_queue = queue.Queue()
        
        # Start progress checker
        self.check_progress()
    
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
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            main_frame,
            text="Cancel",
            command=self.on_cancel,
            fg_color="red",
            hover_color="darkred"
        )
        self.cancel_button.pack(pady=5)
        
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
        try:
            while True:
                update_type, data = self.progress_queue.get_nowait()
                
                if update_type == "operation":
                    self.update_operation(data)
                elif update_type == "progress":
                    completed, total, current_file = data
                    self.update_progress(completed, total, current_file)
                elif update_type == "log":
                    self.log_message(data)
                elif update_type == "complete":
                    self.on_complete(data)
                elif update_type == "error":
                    self.on_error(data)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        if not self.cancelled:
            self.after(100, self.check_progress)
    
    def on_complete(self, success):
        if success:
            self.title_label.configure(text="✅ Complete!")
            self.operation_label.configure(text="Operation completed successfully")
            self.cancel_button.configure(text="Close", fg_color="green", hover_color="darkgreen")
        else:
            self.title_label.configure(text="❌ Failed!")
            self.operation_label.configure(text="Operation failed")
            self.cancel_button.configure(text="Close", fg_color="red", hover_color="darkred")
    
    def on_error(self, error_msg):
        self.title_label.configure(text="❌ Error!")
        self.operation_label.configure(text="An error occurred")
        self.log_message(f"ERROR: {error_msg}")
        self.cancel_button.configure(text="Close", fg_color="red", hover_color="darkred")
    
    def on_cancel(self):
        self.cancelled = True
        self.destroy()

class SorterGUI(ctk.CTk):
    """Main Sorter 2.0 GUI Application"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("🚀 Sorter 2.0 - Advanced ComfyUI Image Organizer")
        self.geometry("900x700")
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"900x700+{x}+{y}")
        
        # Initialize logger
        self.logger = SortLogger()
        
        # Initialize variables BEFORE setup_ui
        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.current_operation = None
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_container)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🚀 Sorter 2.0",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=10)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Advanced ComfyUI Image Organizer",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        subtitle_label.pack()
        
        # File selection frame
        file_frame = ctk.CTkFrame(main_container)
        file_frame.pack(fill="x", pady=(0, 20))
        
        # Source directory
        ctk.CTkLabel(file_frame, text="📁 Source Directory:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        source_frame = ctk.CTkFrame(file_frame)
        source_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.source_entry = ctk.CTkEntry(source_frame, textvariable=self.source_dir, placeholder_text="Select source directory...")
        self.source_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        ctk.CTkButton(
            source_frame,
            text="Browse",
            command=self.browse_source,
            width=80
        ).pack(side="right", padx=(5, 10), pady=10)
        
        # Output directory
        ctk.CTkLabel(file_frame, text="📂 Output Directory:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        output_frame = ctk.CTkFrame(file_frame)
        output_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.output_entry = ctk.CTkEntry(output_frame, textvariable=self.output_dir, placeholder_text="Select output directory (optional)...")
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        ctk.CTkButton(
            output_frame,
            text="Browse",
            command=self.browse_output,
            width=80
        ).pack(side="right", padx=(5, 10), pady=10)
        
        # Sorting options
        options_frame = ctk.CTkFrame(main_container)
        options_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        ctk.CTkLabel(options_frame, text="🎯 Sorting Options:", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Create sorting buttons in a grid
        buttons_frame = ctk.CTkFrame(options_frame)
        buttons_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Row 1
        row1_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row1_frame.pack(fill="x", pady=10)
        
        self.create_sort_button(
            row1_frame,
            "🎯 Sort by Checkpoint",
            "Organize by base checkpoint models",
            self.sort_by_checkpoint,
            "left"
        )
        
        self.create_sort_button(
            row1_frame,
            "🔍 Search & Sort",
            "Find images by metadata content",
            self.search_and_sort,
            "right"
        )
        
        # Row 2
        row2_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row2_frame.pack(fill="x", pady=10)
        
        self.create_sort_button(
            row2_frame,
            "🌈 Sort by Color",
            "Organize by dominant colors",
            self.sort_by_color,
            "left"
        )
        
        self.create_sort_button(
            row2_frame,
            "📂 Flatten Images",
            "Consolidate nested folders",
            self.flatten_images,
            "right"
        )
        
        # Row 3
        row3_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row3_frame.pack(fill="x", pady=10)
        
        self.create_sort_button(
            row3_frame,
            "🧹 Cleanup Filenames",
            "Remove old naming patterns & metadata",
            self.cleanup_filenames,
            "center"
        )
        
        # Options frame
        settings_frame = ctk.CTkFrame(main_container)
        settings_frame.pack(fill="x")
        
        ctk.CTkLabel(settings_frame, text="⚙️ Options:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        # Checkboxes
        check_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        check_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.move_files_var = tk.BooleanVar(value=False)
        self.create_metadata_var = tk.BooleanVar(value=True)
        self.rename_files_var = tk.BooleanVar(value=False)
        self.user_prefix = tk.StringVar()
        
        ctk.CTkCheckBox(
            check_frame,
            text="Move files (instead of copy)",
            variable=self.move_files_var
        ).pack(side="left", padx=(0, 20))
        
        ctk.CTkCheckBox(
            check_frame,
            text="Create metadata files",
            variable=self.create_metadata_var
        ).pack(side="left")
        
        # Add renaming controls in a new row
        rename_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        rename_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        ctk.CTkCheckBox(
            rename_frame,
            text="Rename files with sequential numbering",
            variable=self.rename_files_var
        ).pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(rename_frame, text="Prefix:").pack(side="left", padx=(0, 5))
        self.prefix_entry = ctk.CTkEntry(rename_frame, textvariable=self.user_prefix, width=150)
        self.prefix_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(rename_frame, text="(e.g. 'nova_skyrift' → nova_skyrift_img1.png)", 
                    text_color="gray").pack(side="left")
    
    def create_sort_button(self, parent, title, description, command, side):
        button_frame = ctk.CTkFrame(parent)
        if side == "left":
            button_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        elif side == "right":
            button_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        else:  # center
            button_frame.pack(fill="both", expand=True, padx=10)
        
        button = ctk.CTkButton(
            button_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            command=command
        )
        button.pack(fill="x", padx=15, pady=(15, 5))
        
        desc_label = ctk.CTkLabel(
            button_frame,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        desc_label.pack(padx=15, pady=(0, 15))
    
    def browse_source(self):
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_dir.set(directory)
    
    def browse_output(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
    
    def validate_inputs(self):
        if not self.source_dir.get():
            messagebox.showerror("Error", "Please select a source directory")
            return False

        if not os.path.exists(self.source_dir.get()):
            messagebox.showerror("Error", "Source directory does not exist")
            return False

        if self.rename_files_var.get() and not self.user_prefix.get().strip():
            messagebox.showerror(
                "Error",
                "Filename prefix is required when renaming files. Using default prefix 'image'."
            )
            self.user_prefix.set("image")

        return True
    
    def get_output_directory(self, default_name):
        if self.output_dir.get():
            return self.output_dir.get()
        else:
            return os.path.join(self.source_dir.get(), default_name)
    
    def sort_by_checkpoint(self):
        if not self.validate_inputs():
            return
        
        output_dir = self.get_output_directory("sorted_by_checkpoint")
        
        # Show progress window
        progress_window = ProgressWindow(self, "Sorting by Checkpoint")
        
        # Run sorting in background thread
        def run_sort():
            try:
                sorter = CheckpointSorter(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", "Sorting by checkpoint..."))
                
                success = sorter.sort_by_checkpoint(
                    source_dir=self.source_dir.get(),
                    output_dir=output_dir,
                    move_files=self.move_files_var.get(),
                    create_metadata_files=self.create_metadata_var.get(),
                    rename_files=self.rename_files_var.get(),
                    user_prefix=self.user_prefix.get()
                )
                
                progress_window.progress_queue.put(("complete", success))
                
            except Exception as e:
                progress_window.progress_queue.put(("error", str(e)))
        
        Thread(target=run_sort, daemon=True).start()
    
    def search_and_sort(self):
        if not self.validate_inputs():
            return
        
        # Search dialog
        search_dialog = SearchDialog(self)
        search_terms, search_mode = search_dialog.get_result()
        
        if not search_terms:
            return
        
        output_dir = self.get_output_directory("search_results")
        
        # Show progress window
        progress_window = ProgressWindow(self, "Searching & Sorting")
        
        # Run search in background thread
        def run_search():
            try:
                searcher = MetadataSearchSorter(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", f"Searching for: {', '.join(search_terms)}"))
                
                success = searcher.search_and_sort(
                    source_dir=self.source_dir.get(),
                    output_dir=output_dir,
                    search_terms=search_terms,
                    search_mode=search_mode,
                    move_files=self.move_files_var.get()
                )
                
                progress_window.progress_queue.put(("complete", success))
                
            except Exception as e:
                progress_window.progress_queue.put(("error", str(e)))
        
        Thread(target=run_search, daemon=True).start()
    
    def sort_by_color(self):
        if not self.validate_inputs():
            return
        
        output_dir = self.get_output_directory("sorted_by_color")
        
        # Show progress window
        progress_window = ProgressWindow(self, "Sorting by Color")
        
        # Run sorting in background thread
        def run_sort():
            try:
                sorter = ColorSorter(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", "Analyzing colors and sorting..."))
                
                success = sorter.sort_by_color(
                    source_dir=self.source_dir.get(),
                    output_dir=output_dir,
                    move_files=self.move_files_var.get(),
                    create_metadata=self.create_metadata_var.get(),
                    rename_files=self.rename_files_var.get(),
                    user_prefix=self.user_prefix.get()
                )
                
                progress_window.progress_queue.put(("complete", success))
                
            except Exception as e:
                progress_window.progress_queue.put(("error", str(e)))
        
        Thread(target=run_sort, daemon=True).start()
    
    def flatten_images(self):
        if not self.validate_inputs():
            return
        
        output_dir = self.get_output_directory("flattened")
        
        # Show progress window
        progress_window = ProgressWindow(self, "Flattening Images")
        
        # Run flattening in background thread
        def run_flatten():
            try:
                flattener = ImageFlattener(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", "Flattening image folders..."))
                
                success = flattener.flatten_images(
                    source_dir=self.source_dir.get(),
                    target_dir=output_dir,
                    move_files=self.move_files_var.get(),
                    remove_empty_dirs=True
                )
                
                progress_window.progress_queue.put(("complete", success))
                
            except Exception as e:
                progress_window.progress_queue.put(("error", str(e)))
        
        Thread(target=run_flatten, daemon=True).start()
    
    def cleanup_filenames(self):
        if not self.source_dir.get():
            messagebox.showerror("Error", "Please select a source directory")
            return
        
        # Get cleanup options
        dialog = CleanupDialog(self)
        if not dialog.confirmed:
            return
        
        # Show progress window
        progress_window = ProgressWindow(self, "Cleaning Up Files")
        
        # Run cleanup in background thread
        def run_cleanup():
            try:
                cleanup = FilenameCleanup(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", "Cleaning up filenames and metadata..."))
                
                success = cleanup.cleanup_directory(
                    source_dir=self.source_dir.get(),
                    remove_metadata_files=dialog.remove_metadata,
                    rename_files=dialog.rename_files,
                    filename_prefix=dialog.filename_prefix,
                    dry_run=False
                )
                
                progress_window.progress_queue.put(("complete", success))
                
            except Exception as e:
                progress_window.progress_queue.put(("error", str(e)))
        
        Thread(target=run_cleanup, daemon=True).start()

class CleanupDialog(ctk.CTkToplevel):
    """Dialog for configuring filename cleanup"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Cleanup Configuration")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self.confirmed = False
        self.rename_files = True
        self.remove_metadata = True
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_frame,
            text="🧹 Filename Cleanup Configuration",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 20))
        
        # Description
        desc_text = """This tool will clean up your filenames by removing old naming patterns and optionally removing metadata files.

Examples of patterns that will be cleaned:
• [workflow_test_batch1] Gen 31 $0152.png → image_001.png
• ComfyUI_12345_workflow.png → ComfyUI_12345.png
• image Gen 42 $9876.jpg → image.jpg

Metadata files (_metadata.json) can also be removed."""
        
        desc_label = ctk.CTkLabel(
            main_frame,
            text=desc_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        desc_label.pack(pady=(0, 20), fill="x")
        
        # Options
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            options_frame,
            text="Options:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.rename_var = ctk.BooleanVar(value=True)
        self.metadata_var = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(
            options_frame,
            text="Clean up filenames (remove workflow patterns)",
            variable=self.rename_var
        ).pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkCheckBox(
            options_frame,
            text="Remove _metadata.json files",
            variable=self.metadata_var
        ).pack(anchor="w", padx=20, pady=(5, 10))
        
        # Filename prefix
        prefix_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        prefix_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            prefix_frame,
            text="Filename prefix:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")
        
        self.prefix_entry = ctk.CTkEntry(
            prefix_frame,
            placeholder_text="Enter prefix (default: image)",
            width=200
        )
        self.prefix_entry.pack(anchor="w", pady=(5, 0))
        self.prefix_entry.insert(0, "image")
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=100
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="Clean Up",
            command=self.confirm,
            width=100
        ).pack(side="right")
    
    def confirm(self):
        self.rename_files = self.rename_var.get()
        self.remove_metadata = self.metadata_var.get()
        self.filename_prefix = self.prefix_entry.get().strip() or "image"
        
        # Clean the prefix to make it filesystem-safe
        import re
        self.filename_prefix = re.sub(r'[<>:"/\\|?*]', '_', self.filename_prefix)
        self.filename_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', self.filename_prefix)
        self.filename_prefix = self.filename_prefix.strip('_-')
        if not self.filename_prefix:
            self.filename_prefix = "image"
        
        if not self.rename_files and not self.remove_metadata:
            messagebox.showwarning("Warning", "Please select at least one cleanup option")
            return
        
        self.confirmed = True
        self.destroy()
    
    def cancel(self):
        self.confirmed = False
        self.destroy()

class SearchDialog(ctk.CTkToplevel):
    """Dialog for configuring metadata search"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Search Configuration")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"400x300+{x}+{y}")
        
        self.result = (None, None)
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔍 Search Configuration",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Search terms
        ctk.CTkLabel(main_frame, text="Search Terms:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        
        self.search_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter search terms (comma-separated)",
            width=350
        )
        self.search_entry.pack(pady=(0, 20))
        
        # Search mode
        ctk.CTkLabel(main_frame, text="Search Mode:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        
        self.search_mode_var = tk.StringVar(value="any")
        
        ctk.CTkRadioButton(
            main_frame,
            text="Match ANY term (OR)",
            variable=self.search_mode_var,
            value="any"
        ).pack(anchor="w", pady=2)
        
        ctk.CTkRadioButton(
            main_frame,
            text="Match ALL terms (AND)",
            variable=self.search_mode_var,
            value="all"
        ).pack(anchor="w", pady=2)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 10))
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            fg_color="gray",
            hover_color="darkgray"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="Search",
            command=self.on_search
        ).pack(side="right")
    
    def on_search(self):
        search_text = self.search_entry.get().strip()
        if not search_text:
            messagebox.showerror("Error", "Please enter search terms")
            return
        
        # Split and clean search terms
        search_terms = [term.strip() for term in search_text.split(",") if term.strip()]
        search_mode = self.search_mode_var.get()
        
        self.result = (search_terms, search_mode)
        self.destroy()
    
    def on_cancel(self):
        self.result = (None, None)
        self.destroy()
    
    def get_result(self):
        self.wait_window()
        return self.result

def main():
    """Launch the Sorter 2.0 GUI"""
    try:
        app = SorterGUI()
        app.mainloop()
    except Exception as e:
        print(f"Error launching GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
