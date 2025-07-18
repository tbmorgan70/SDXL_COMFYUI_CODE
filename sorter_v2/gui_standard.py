"""
Sorter 2.0 - Standard GUI Interface

Cross-platform GUI using standard tkinter - no additional dependencies required.
Beautiful, functional interface for all sorting operations with real-time progress tracking.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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

class ProgressWindow:
    """Progress tracking window with real-time updates"""
    
    def __init__(self, parent, title="Processing..."):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("600x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"600x400+{x}+{y}")
        
        # Configure style
        self.setup_styles()
        
        # Create UI
        self.setup_ui()
        
        # Progress tracking
        self.current_operation = ""
        self.progress_queue = queue.Queue()
        self.cancelled = False
        
        # Start progress checker
        self.check_progress()
    
    def setup_styles(self):
        """Configure modern-looking styles"""
        self.style = ttk.Style()
        
        # Configure colors for a modern look
        self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#2563eb')
        self.style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#1f2937')
        self.style.configure('Info.TLabel', font=('Segoe UI', 10), foreground='#6b7280')
        self.style.configure('Success.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#059669')
        self.style.configure('Error.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#dc2626')
        
        # Modern button style
        self.style.configure('Modern.TButton', font=('Segoe UI', 10))
        self.style.configure('Cancel.TButton', font=('Segoe UI', 10))
        self.style.configure('Success.TButton', font=('Segoe UI', 10))
    
    def setup_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        self.title_label = ttk.Label(
            main_frame, 
            text="🚀 Processing Files...", 
            style='Title.TLabel'
        )
        self.title_label.pack(pady=(0, 10))
        
        # Current operation
        self.operation_label = ttk.Label(
            main_frame,
            text="Preparing...",
            style='Heading.TLabel'
        )
        self.operation_label.pack(pady=(0, 10))
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            mode='determinate',
            length=500
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Progress text
        self.progress_label = ttk.Label(
            progress_frame,
            text="0 / 0 files processed",
            style='Info.TLabel'
        )
        self.progress_label.pack()
        
        # Current file
        self.file_label = ttk.Label(
            main_frame,
            text="",
            style='Info.TLabel'
        )
        self.file_label.pack(pady=(0, 10))
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Progress Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            text_frame, 
            height=10, 
            font=('Consolas', 9),
            wrap=tk.WORD,
            bg='#f8f9fa',
            fg='#374151'
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Cancel/Close button
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            style='Cancel.TButton'
        )
        self.cancel_button.pack(side=tk.RIGHT)
    
    def update_operation(self, operation):
        self.operation_label.config(text=operation)
    
    def update_progress(self, completed, total, current_file=""):
        # Ensure parameters are the correct type
        try:
            completed = int(completed) if not isinstance(completed, int) else completed
            total = int(total) if not isinstance(total, int) else total
        except (ValueError, TypeError):
            # If conversion fails, use safe defaults
            completed = 0
            total = 1
            
        if total > 0:
            progress_percent = (completed / total) * 100
            self.progress_var.set(progress_percent)
            self.progress_label.config(text=f"{completed} / {total} files processed ({progress_percent:.1f}%)")
        
        if current_file:
            # Truncate long filenames
            if len(current_file) > 70:
                current_file = current_file[:67] + "..."
            self.file_label.config(text=f"Current: {current_file}")
    
    def log_message(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.window.update()
    
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
                    return  # Stop checking when complete
                elif update_type == "error":
                    self.on_error(data)
                    return  # Stop checking on error
                    
        except queue.Empty:
            pass
        
        # Schedule next check if not cancelled
        if not self.cancelled:
            self.window.after(50, self.check_progress)  # Check more frequently
    
    def on_complete(self, success):
        if success:
            self.title_label.config(text="✅ Complete!", style='Success.TLabel')
            self.operation_label.config(text="Operation completed successfully")
            self.cancel_button.config(text="Close", style='Success.TButton')
            self.log_message("🎉 Operation completed successfully!")
        else:
            self.title_label.config(text="❌ Failed!", style='Error.TLabel')
            self.operation_label.config(text="Operation failed")
            self.cancel_button.config(text="Close", style='Cancel.TButton')
            self.log_message("❌ Operation failed")
    
    def on_error(self, error_msg):
        self.title_label.config(text="❌ Error!", style='Error.TLabel')
        self.operation_label.config(text="An error occurred")
        self.log_message(f"ERROR: {error_msg}")
        self.cancel_button.config(text="Close", style='Cancel.TButton')
    
    def on_cancel(self):
        self.cancelled = True
        self.window.destroy()

class SearchDialog:
    """Dialog for configuring metadata search"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Search Configuration")
        self.window.geometry("450x350")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.window.winfo_screenheight() // 2) - (350 // 2)
        self.window.geometry(f"450x350+{x}+{y}")
        
        self.result = (None, None)
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="🔍 Search Configuration",
            font=('Segoe UI', 16, 'bold'),
            foreground='#2563eb'
        )
        title_label.pack(pady=(0, 20))
        
        # Search terms
        search_frame = ttk.LabelFrame(main_frame, text="Search Terms", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(search_frame, text="Enter terms to search for (comma-separated):").pack(anchor=tk.W, pady=(0, 5))
        
        self.search_entry = ttk.Entry(search_frame, font=('Segoe UI', 10))
        self.search_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Examples
        examples_text = "Examples:\n• nova_skyrift, disco_dollz (find images with these LoRAs)\n• \"beautiful woman\", portrait (find images with these prompts)\n• ultraRealistic, realDream (find images with these checkpoints)"
        ttk.Label(search_frame, text=examples_text, font=('Segoe UI', 9), foreground='#6b7280').pack(anchor=tk.W)
        
        # Search mode
        mode_frame = ttk.LabelFrame(main_frame, text="Search Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.search_mode_var = tk.StringVar(value="any")
        
        ttk.Radiobutton(
            mode_frame,
            text="Match ANY term (OR) - Find images containing at least one term",
            variable=self.search_mode_var,
            value="any"
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="Match ALL terms (AND) - Find images containing all terms",
            variable=self.search_mode_var,
            value="all"
        ).pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text="Search",
            command=self.on_search
        ).pack(side=tk.RIGHT)
        
        # Focus on entry
        self.search_entry.focus()
    
    def on_search(self):
        search_text = self.search_entry.get().strip()
        if not search_text:
            messagebox.showerror("Error", "Please enter search terms")
            return
        
        # Split and clean search terms
        search_terms = [term.strip().strip('"\'') for term in search_text.split(",") if term.strip()]
        search_mode = self.search_mode_var.get()
        
        self.result = (search_terms, search_mode)
        self.window.destroy()
    
    def on_cancel(self):
        self.result = (None, None)
        self.window.destroy()
    
    def get_result(self):
        self.window.wait_window()
        return self.result

class SorterGUI:
    """Main Sorter 2.0 GUI Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 Sorter 2.0 - Advanced ComfyUI Image Organizer")
        self.root.geometry("1000x750")
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (750 // 2)
        self.root.geometry(f"1000x750+{x}+{y}")
        
        # Configure style
        self.setup_styles()
        
        # Initialize logger
        self.logger = SortLogger()
        
        # Initialize variables first
        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.move_files_var = tk.BooleanVar(value=False)
        self.create_metadata_var = tk.BooleanVar(value=True)
        self.rename_files_var = tk.BooleanVar(value=False)
        self.user_prefix = tk.StringVar()
        
        # Setup UI
        self.setup_ui()
    
    def setup_styles(self):
        """Configure modern-looking styles"""
        self.style = ttk.Style()
        
        # Use a modern theme if available
        available_themes = self.style.theme_names()
        if 'vista' in available_themes:
            self.style.theme_use('vista')
        elif 'clam' in available_themes:
            self.style.theme_use('clam')
        
        # Configure custom styles
        self.style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), foreground='#1f2937')
        self.style.configure('Subtitle.TLabel', font=('Segoe UI', 12), foreground='#6b7280')
        self.style.configure('Heading.TLabel', font=('Segoe UI', 14, 'bold'), foreground='#374151')
        self.style.configure('SortButton.TButton', font=('Segoe UI', 12, 'bold'), padding=(20, 10))
        self.style.configure('Description.TLabel', font=('Segoe UI', 10), foreground='#6b7280')
    
    def setup_ui(self):
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="30")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = ttk.Label(
            header_frame,
            text="🚀 Sorter 2.0",
            style='Title.TLabel'
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Advanced ComfyUI Image Organizer",
            style='Subtitle.TLabel'
        )
        subtitle_label.pack(pady=(5, 0))
        
        # File selection section
        file_section = ttk.LabelFrame(main_container, text="📁 Directory Selection", padding="20")
        file_section.pack(fill=tk.X, pady=(0, 20))
        
        # Source directory
        source_frame = ttk.Frame(file_section)
        source_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(source_frame, text="Source Directory:", style='Heading.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        source_entry_frame = ttk.Frame(source_frame)
        source_entry_frame.pack(fill=tk.X)
        
        self.source_entry = ttk.Entry(source_entry_frame, textvariable=self.source_dir, font=('Segoe UI', 10))
        self.source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(
            source_entry_frame,
            text="Browse...",
            command=self.browse_source,
            width=12
        ).pack(side=tk.RIGHT)
        
        # Output directory
        output_frame = ttk.Frame(file_section)
        output_frame.pack(fill=tk.X)
        
        ttk.Label(output_frame, text="Output Directory (optional):", style='Heading.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        output_entry_frame = ttk.Frame(output_frame)
        output_entry_frame.pack(fill=tk.X)
        
        self.output_entry = ttk.Entry(output_entry_frame, textvariable=self.output_dir, font=('Segoe UI', 10))
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(
            output_entry_frame,
            text="Browse...",
            command=self.browse_output,
            width=12
        ).pack(side=tk.RIGHT)
        
        # Sorting options section
        options_section = ttk.LabelFrame(main_container, text="🎯 Sorting Operations", padding="20")
        options_section.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create sorting buttons in a 2x2 grid
        buttons_frame = ttk.Frame(options_section)
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.rowconfigure(0, weight=1)
        buttons_frame.rowconfigure(1, weight=1)
        
        # Create sort buttons
        self.create_sort_button_with_desc(
            buttons_frame,
            "🎯 Sort by Checkpoint",
            "Organize images by base checkpoint models\n(Your #1 most-used feature)",
            self.sort_by_checkpoint,
            0, 0
        )
        
        self.create_sort_button_with_desc(
            buttons_frame,
            "🔍 Search & Sort",
            "Find and organize images by metadata\n(LoRAs, prompts, settings)",
            self.search_and_sort,
            0, 1
        )
        
        self.create_sort_button_with_desc(
            buttons_frame,
            "🌈 Sort by Color",
            "Organize images by dominant colors\n(Red, Blue, Green, etc.)",
            self.sort_by_color,
            1, 0
        )
        
        self.create_sort_button_with_desc(
            buttons_frame,
            "📂 Flatten Images",
            "Consolidate nested folder structures\n(Move all images to one level)",
            self.flatten_images,
            1, 1
        )
        
        self.create_sort_button_with_desc(
            buttons_frame,
            "🧹 Cleanup Filenames",
            "Remove old naming patterns & metadata\n(Clean '[workflow] Gen 31 $0152' patterns)",
            self.cleanup_filenames,
            2, 0, columnspan=2
        )
        
        # Settings section
        settings_section = ttk.LabelFrame(main_container, text="⚙️ Options", padding="15")
        settings_section.pack(fill=tk.X)
        
        settings_frame = ttk.Frame(settings_section)
        settings_frame.pack(fill=tk.X)
        
        ttk.Checkbutton(
            settings_frame,
            text="Move files (instead of copy)",
            variable=self.move_files_var
        ).pack(side=tk.LEFT, padx=(0, 30))
        
        ttk.Checkbutton(
            settings_frame,
            text="Create metadata files",
            variable=self.create_metadata_var
        ).pack(side=tk.LEFT)
        
        # Add renaming controls in a new row
        rename_frame = ttk.Frame(settings_section)
        rename_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Checkbutton(
            rename_frame,
            text="Rename files with sequential numbering",
            variable=self.rename_files_var
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(rename_frame, text="Prefix:").pack(side=tk.LEFT, padx=(0, 5))
        prefix_entry = ttk.Entry(rename_frame, textvariable=self.user_prefix, width=20)
        prefix_entry.pack(side=tk.LEFT)
        
        # Add example text
        ttk.Label(rename_frame, text="(e.g. 'nova_skyrift' → nova_skyrift_img1.png)", 
                 foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
    
    def create_sort_button_with_desc(self, parent, title, description, command, row, col, columnspan=1):
        # Button frame
        button_frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1)
        button_frame.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=10, pady=10)
        
        # Configure internal padding
        button_frame.columnconfigure(0, weight=1)
        button_frame.rowconfigure(1, weight=1)
        
        # Button
        button = ttk.Button(
            button_frame,
            text=title,
            command=command,
            style='SortButton.TButton'
        )
        button.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        
        # Description
        desc_label = ttk.Label(
            button_frame,
            text=description,
            style='Description.TLabel',
            justify=tk.CENTER
        )
        desc_label.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
    
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
        progress_window = ProgressWindow(self.root, "Sorting by Checkpoint")
        
        # Run sorting in background thread
        def run_sort():
            try:
                sorter = CheckpointSorter(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", "Analyzing ComfyUI metadata and sorting by checkpoint..."))
                progress_window.progress_queue.put(("log", f"Source: {self.source_dir.get()}"))
                progress_window.progress_queue.put(("log", f"Output: {output_dir}"))
                progress_window.progress_queue.put(("log", f"Operation: {'MOVE' if self.move_files_var.get() else 'COPY'}"))
                
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
        search_dialog = SearchDialog(self.root)
        search_terms, search_mode = search_dialog.get_result()
        
        if not search_terms:
            return
        
        output_dir = self.get_output_directory("search_results")
        
        # Show progress window
        progress_window = ProgressWindow(self.root, "Searching & Sorting")
        
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
                progress_window.progress_queue.put(("log", f"Search terms: {search_terms}"))
                progress_window.progress_queue.put(("log", f"Search mode: {search_mode.upper()}"))
                progress_window.progress_queue.put(("log", f"Source: {self.source_dir.get()}"))
                progress_window.progress_queue.put(("log", f"Output: {output_dir}"))
                progress_window.progress_queue.put(("log", f"Operation: {'MOVE' if self.move_files_var.get() else 'COPY'}"))
                
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
        progress_window = ProgressWindow(self.root, "Sorting by Color")
        
        # Run sorting in background thread
        def run_sort():
            try:
                sorter = ColorSorter(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", "Analyzing dominant colors and sorting..."))
                progress_window.progress_queue.put(("log", f"Source: {self.source_dir.get()}"))
                progress_window.progress_queue.put(("log", f"Output: {output_dir}"))
                progress_window.progress_queue.put(("log", f"Operation: {'MOVE' if self.move_files_var.get() else 'COPY'}"))
                
                success = sorter.sort_by_color(
                    source_dir=self.source_dir.get(),
                    output_dir=output_dir,
                    move_files=self.move_files_var.get(),
                    create_metadata=self.create_metadata_var.get()
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
        progress_window = ProgressWindow(self.root, "Flattening Images")
        
        # Run flattening in background thread
        def run_flatten():
            try:
                flattener = ImageFlattener(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", "Flattening nested image folders..."))
                progress_window.progress_queue.put(("log", f"Source: {self.source_dir.get()}"))
                progress_window.progress_queue.put(("log", f"Target: {output_dir}"))
                progress_window.progress_queue.put(("log", f"Operation: {'MOVE' if self.move_files_var.get() else 'COPY'}"))
                
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
        
        # Show options dialog
        dialog = CleanupDialog(self.root)
        if not dialog.confirmed:
            return
        
        # Show progress window
        progress_window = ProgressWindow(self.root, "Cleaning Up Files")
        
        # Run cleanup in background thread
        def run_cleanup():
            try:
                cleanup = FilenameCleanup(self.logger)
                
                # Set up progress callback
                def progress_callback(completed, total, current_file):
                    progress_window.progress_queue.put(("progress", (completed, total, current_file)))
                
                self.logger.set_progress_callback(progress_callback)
                
                # Update operation
                progress_window.progress_queue.put(("operation", "Cleaning up filenames and metadata files..."))
                progress_window.progress_queue.put(("log", f"Source: {self.source_dir.get()}"))
                progress_window.progress_queue.put(("log", f"Rename files: {dialog.rename_files}"))
                progress_window.progress_queue.put(("log", f"Remove metadata: {dialog.remove_metadata}"))
                progress_window.progress_queue.put(("log", f"Filename prefix: {dialog.filename_prefix}"))
                
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
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

class CleanupDialog:
    """Dialog for configuring filename cleanup options"""
    
    def __init__(self, parent):
        self.parent = parent
        self.confirmed = False
        self.rename_files = True
        self.remove_metadata = True
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Cleanup Configuration")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center window
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="🧹 Filename Cleanup Configuration",
            font=('TkDefaultFont', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_text = """This tool will clean up your filenames by removing old naming patterns
and optionally removing metadata files.

Examples of patterns that will be cleaned:
• [workflow_test_batch1] Gen 31 $0152.png → image_001.png
• ComfyUI_12345_workflow.png → ComfyUI_12345.png
• image Gen 42 $9876.jpg → image.jpg

Metadata files (_metadata.json) can also be removed."""
        
        desc_frame = ttk.Frame(main_frame, relief=tk.RIDGE, borderwidth=1)
        desc_frame.pack(fill=tk.X, pady=(0, 20))
        
        desc_label = ttk.Label(
            desc_frame,
            text=desc_text,
            justify=tk.LEFT,
            wraplength=450
        )
        desc_label.pack(padx=15, pady=15)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.rename_var = tk.BooleanVar(value=True)
        self.metadata_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(
            options_frame,
            text="Clean up filenames (remove workflow patterns)",
            variable=self.rename_var
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Checkbutton(
            options_frame,
            text="Remove _metadata.json files",
            variable=self.metadata_var
        ).pack(anchor=tk.W, pady=5)
        
        # Filename prefix
        prefix_frame = ttk.Frame(options_frame)
        prefix_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            prefix_frame,
            text="Filename prefix:"
        ).pack(anchor=tk.W)
        
        self.prefix_var = tk.StringVar(value="image")
        self.prefix_entry = ttk.Entry(
            prefix_frame,
            textvariable=self.prefix_var,
            width=30
        )
        self.prefix_entry.pack(anchor=tk.W, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text="Clean Up",
            command=self.confirm
        ).pack(side=tk.RIGHT)
    
    def confirm(self):
        self.rename_files = self.rename_var.get()
        self.remove_metadata = self.metadata_var.get()
        self.filename_prefix = self.prefix_var.get().strip() or "image"
        
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
        self.dialog.destroy()
    
    def cancel(self):
        self.confirmed = False
        self.dialog.destroy()

def main():
    """Launch the Sorter 2.0 GUI"""
    try:
        app = SorterGUI()
        app.run()
    except Exception as e:
        print(f"Error launching GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
