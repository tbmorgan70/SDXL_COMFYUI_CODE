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
from sorters.image_extractor import ImageExtractorSorter, CROP_PRESETS, SUPPORTED_EXTENSIONS
from sorters.manual_sorter import ManualSorter, IMAGE_EXTENSIONS, TRASH_BUCKET
from PIL import Image

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

class TriageWindow(ctk.CTkToplevel):
    """Visual triage: thumbnail gallery + full-size viewer with keyboard-driven
    bucket assignment. Executes moves into bucket subfolders on demand."""

    PAGE_SIZE = 60
    COLS = 6
    THUMB = 150
    BUCKET_COLORS = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"]
    TRASH_COLOR = "#F44336"

    def __init__(self, parent, sorter: ManualSorter, log_fn):
        super().__init__(parent)
        self.sorter = sorter
        self.log_fn = log_fn

        self.title(f"🖼️ Manual Sort — {sorter.source_dir.name}  ({len(sorter.images)} images)")
        self.geometry("1240x880")

        self.page = 0
        self.current_index = None          # index into sorter.images when in viewer
        self.thumb_cache = {}              # Path -> CTkImage (created in main thread only)
        self.thumb_widgets = {}            # Path -> (cell frame, image label), current page only
        self._viewer_img = None            # keep reference so it isn't GC'd
        self._closing = False
        self._page_token = 0               # invalidates in-flight thumbnail loads on page change
        self._load_queue = queue.Queue()   # worker thread -> main thread handoff

        # Bucket colors: trash always red, others from palette
        self.bucket_colors = {}
        ci = 0
        for b in self.sorter.buckets:
            if b == TRASH_BUCKET:
                self.bucket_colors[b] = self.TRASH_COLOR
            else:
                self.bucket_colors[b] = self.BUCKET_COLORS[ci % len(self.BUCKET_COLORS)]
                ci += 1

        self._build_ui()
        self._show_gallery()
        self._render_page()

        # Keyboard bindings
        self.bind("<Right>", lambda e: self._nav(1))
        self.bind("<Left>", lambda e: self._nav(-1))
        self.bind("<Escape>", lambda e: self._show_gallery())
        self.bind("<Delete>", lambda e: self._assign_key(len(self.sorter.buckets)))
        self.bind("<Key-0>", lambda e: self._assign_key(0))
        for i in range(1, len(self.sorter.buckets) + 1):
            self.bind(f"<Key-{i}>", lambda e, n=i: self._assign_key(n))
        self.bind("<Prior>", lambda e: self._change_page(-1))   # PgUp
        self.bind("<Next>", lambda e: self._change_page(1))     # PgDn
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(200, self.focus_force)

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        # --- Top bar: bucket buttons + counts ---
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=(10, 5))

        self.bucket_buttons = {}
        for i, bucket in enumerate(self.sorter.buckets):
            btn = ctk.CTkButton(
                top,
                text=f"[{i+1}] {bucket} (0)",
                fg_color=self.bucket_colors[bucket],
                hover_color=self.bucket_colors[bucket],
                width=140,
                command=lambda b=bucket: self._assign_current(b),
            )
            btn.pack(side="left", padx=4, pady=8)
            self.bucket_buttons[bucket] = btn

        ctk.CTkButton(top, text="[0] Clear", fg_color="#555", width=80,
                      command=lambda: self._assign_current(None)).pack(side="left", padx=4)

        self.execute_btn = ctk.CTkButton(
            top, text="🚀 Execute Sort", fg_color="green", hover_color="darkgreen",
            width=130, command=self._execute)
        self.execute_btn.pack(side="right", padx=8)

        self.status_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="right", padx=10)

        # --- Page bar (gallery mode) ---
        self.page_bar = ctk.CTkFrame(self)
        self.page_bar.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkButton(self.page_bar, text="◀ Prev", width=70,
                      command=lambda: self._change_page(-1)).pack(side="left", padx=4, pady=4)
        self.page_label = ctk.CTkLabel(self.page_bar, text="Page 1")
        self.page_label.pack(side="left", padx=10)
        ctk.CTkButton(self.page_bar, text="Next ▶", width=70,
                      command=lambda: self._change_page(1)).pack(side="left", padx=4)
        ctk.CTkLabel(self.page_bar,
                     text="Click a thumbnail to view • ←/→ navigate • 1-4 assign • 0 clear • Del = Trash • Esc = gallery",
                     text_color="#888", font=ctk.CTkFont(size=11)).pack(side="right", padx=10)

        # --- Body: gallery + viewer (swapped) ---
        self.body = ctk.CTkFrame(self)
        self.body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.gallery = ctk.CTkScrollableFrame(self.body)

        self.viewer = ctk.CTkFrame(self.body)
        self.viewer_label = ctk.CTkLabel(self.viewer, text="")
        self.viewer_label.pack(fill="both", expand=True, pady=(5, 0))
        self.viewer_info = ctk.CTkLabel(self.viewer, text="", font=ctk.CTkFont(size=13, weight="bold"))
        self.viewer_info.pack(pady=6)

        self._update_counts()

    # ------------------------------------------------------------------ gallery

    def _show_gallery(self):
        self.current_index = None
        self.viewer.pack_forget()
        self.gallery.pack(fill="both", expand=True)
        self.page_bar.pack(fill="x", padx=10, pady=(0, 5), before=self.body)

    def _page_count(self):
        return max(1, (len(self.sorter.images) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

    def _change_page(self, delta):
        if self.current_index is not None:
            return  # viewer mode: pages don't apply
        new_page = max(0, min(self.page + delta, self._page_count() - 1))
        if new_page != self.page:
            self.page = new_page
            self._render_page()

    def _render_page(self):
        for w in self.gallery.winfo_children():
            w.destroy()
        self.thumb_widgets = {}

        start = self.page * self.PAGE_SIZE
        page_paths = self.sorter.images[start:start + self.PAGE_SIZE]
        self.page_label.configure(text=f"Page {self.page + 1} / {self._page_count()}")

        for i, path in enumerate(page_paths):
            # Outer frame acts as the colored "assignment border"
            cell = ctk.CTkFrame(self.gallery, fg_color=self._border_for(path), corner_radius=6)
            cell.grid(row=i // self.COLS, column=i % self.COLS, padx=5, pady=5)

            lbl = ctk.CTkLabel(cell, text="…", width=self.THUMB, height=self.THUMB,
                               fg_color="#333", corner_radius=4)
            lbl.pack(padx=3, pady=3)

            for w in (cell, lbl):
                w.bind("<Button-1>", lambda e, idx=start + i: self._open_viewer(idx))

            self.thumb_widgets[path] = (cell, lbl)

        # Load PIL thumbnails in a worker thread; a main-thread poller creates
        # the CTkImages (Tk image objects must be touched from the main thread only).
        self._page_token += 1
        token = self._page_token
        self._pending_thumbs = len(page_paths)
        Thread(target=self._load_thumbs, args=(list(page_paths), token), daemon=True).start()
        self.after(50, self._poll_thumbs, token)

    def _border_for(self, path):
        bucket = self.sorter.get_assignment(path)
        return self.bucket_colors[bucket] if bucket else "#333"

    def _load_thumbs(self, paths, token):
        """Worker thread: decode images to PIL thumbnails, hand off via queue."""
        for path in paths:
            if self._closing or token != self._page_token:
                return
            if path in self.thumb_cache:
                self._load_queue.put((token, path, "CACHED"))
                continue
            try:
                img = Image.open(path)
                img.thumbnail((self.THUMB, self.THUMB))
                self._load_queue.put((token, path, img.convert("RGB")))
            except Exception:
                self._load_queue.put((token, path, None))

    def _poll_thumbs(self, token):
        """Main thread: drain the queue, create CTkImages, update labels."""
        if self._closing or token != self._page_token:
            return
        try:
            while True:
                item_token, path, pil = self._load_queue.get_nowait()
                if item_token != token:
                    continue  # stale page
                self._pending_thumbs -= 1

                pair = self.thumb_widgets.get(path)
                if pair is None:
                    continue
                cell, lbl = pair
                if not lbl.winfo_exists():
                    continue

                if pil is None:
                    lbl.configure(text="⚠️")
                    continue

                if pil == "CACHED":
                    img = self.thumb_cache[path]
                else:
                    img = ctk.CTkImage(light_image=pil, size=pil.size)
                    self.thumb_cache[path] = img
                lbl.configure(image=img, text="")
        except queue.Empty:
            pass

        if self._pending_thumbs > 0:
            self.after(50, self._poll_thumbs, token)

    # ------------------------------------------------------------------ viewer

    def _open_viewer(self, index):
        self.current_index = index
        self.gallery.pack_forget()
        self.page_bar.pack_forget()
        self.viewer.pack(fill="both", expand=True)
        self._show_current()

    def _show_current(self):
        if self.current_index is None or not self.sorter.images:
            return
        path = self.sorter.images[self.current_index]

        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            self.viewer_info.configure(text=f"⚠️ Cannot open {path.name}: {e}")
            return

        # Fit to available area
        max_w = max(400, self.winfo_width() - 60)
        max_h = max(300, self.winfo_height() - 220)
        scale = min(max_w / img.width, max_h / img.height, 1.0)
        size = (int(img.width * scale), int(img.height * scale))

        self._viewer_img = ctk.CTkImage(light_image=img, size=size)
        self.viewer_label.configure(image=self._viewer_img, text="")

        bucket = self.sorter.get_assignment(path)
        tag = f"  →  {bucket}" if bucket else "  →  (unassigned)"
        color = self.bucket_colors.get(bucket, "#aaa") if bucket else "#aaa"
        self.viewer_info.configure(
            text=f"{self.current_index + 1} / {len(self.sorter.images)}   {path.name}{tag}",
            text_color=color,
        )

    def _nav(self, delta):
        if self.current_index is None:
            return
        n = len(self.sorter.images)
        if n == 0:
            return
        self.current_index = (self.current_index + delta) % n
        self._show_current()

    # ------------------------------------------------------------------ assignment

    def _assign_key(self, num):
        """Handle number key: 0 clears, 1..N assigns bucket by index."""
        if self.current_index is None:
            return
        if num == 0:
            self._assign_current(None)
        elif 1 <= num <= len(self.sorter.buckets):
            self._assign_current(self.sorter.buckets[num - 1])

    def _assign_current(self, bucket):
        if self.current_index is None:
            return
        path = self.sorter.images[self.current_index]
        self.sorter.assign(path, bucket)
        self._update_counts()

        # Refresh thumbnail border if it's on the current page
        pair = self.thumb_widgets.get(path)
        if pair is not None and pair[0].winfo_exists():
            pair[0].configure(fg_color=self._border_for(path))

        if bucket is not None:
            self._nav(1)  # auto-advance after assignment
        else:
            self._show_current()

    def _update_counts(self):
        counts = self.sorter.counts()
        for i, bucket in enumerate(self.sorter.buckets):
            self.bucket_buttons[bucket].configure(text=f"[{i+1}] {bucket} ({counts[bucket]})")
        assigned = len(self.sorter.assignments)
        self.status_label.configure(
            text=f"{assigned} assigned / {counts['unassigned']} remaining")

    # ------------------------------------------------------------------ execute

    def _execute(self):
        if not self.sorter.assignments:
            messagebox.showinfo("Nothing to do", "No images have been assigned to buckets yet.", parent=self)
            return

        counts = self.sorter.counts()
        summary = "\n".join(
            f"   {b}: {counts[b]} images" for b in self.sorter.buckets if counts[b] > 0)
        if not messagebox.askyesno(
                "Execute Manual Sort",
                f"Move {len(self.sorter.assignments)} images into bucket folders?\n\n{summary}\n\n"
                f"Unassigned images ({counts['unassigned']}) stay where they are.",
                parent=self):
            return

        self.execute_btn.configure(state="disabled", text="Moving...")

        def run():
            results = self.sorter.execute()
            self.after(0, self._on_executed, results)

        Thread(target=run, daemon=True).start()

    def _on_executed(self, results):
        moved_total = sum(results["moved"].values())
        moved_paths = set(self.sorter.assignments.keys())

        # Drop moved images from the working set
        self.sorter.images = [p for p in self.sorter.images if p not in moved_paths]
        self.sorter.assignments = {}

        self.execute_btn.configure(state="normal", text="🚀 Execute Sort")
        self._update_counts()

        msg = f"Moved {moved_total} images into bucket folders.\n\nRemaining unsorted: {len(self.sorter.images)}"
        if results["errors"]:
            msg += f"\n\n⚠️ {len(results['errors'])} errors — see session log."
        messagebox.showinfo("Sort Complete", msg, parent=self)
        self.log_fn(f"🖼️ Manual sort executed: {results['moved']}")

        # Back to gallery on a valid page
        self.page = min(self.page, self._page_count() - 1)
        self._show_gallery()
        self._render_page()

    def _on_close(self):
        if self.sorter.assignments:
            if not messagebox.askyesno(
                    "Unsaved assignments",
                    f"{len(self.sorter.assignments)} images are assigned but not yet moved.\n"
                    "Close anyway and lose these assignments?",
                    parent=self):
                return
        self._closing = True
        self.destroy()


class SorterGUI(ctk.CTk):
    """Main Sorter 2.0 GUI Application - Compact Design"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window - compact size like unified_sorter
        self.title("🚀 Sorter 2.4.0 - Advanced ComfyUI Image Organizer")
        self.geometry("750x700")
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (750 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"750x700+{x}+{y}")
        
        # Initialize logger
        self.logger = SortLogger()
        
        # Initialize variables
        self.source_dir = r"D:\ComfyUI_windows_portable\ComfyUI\output"
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
            text="🚀 Sorter 2.4.0 - ComfyUI Image Organizer",
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
            values=["Sort by Checkpoint", "Sort by LoRA Stack", "Search & Sort", "Sort by Color", "Flatten Images", "Extract Images", "Manual Sort (Triage)", "Generate Metadata", "View Session Logs"],
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
        self.extract_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.manual_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.metadata_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)
        self.logs_frame = ctk.CTkFrame(self.forms_frame, corner_radius=10)

        # Build all forms
        self._build_checkpoint_form()
        self._build_lora_form()
        self._build_search_form()
        self._build_color_form()
        self._build_flatten_form()
        self._build_extract_form()
        self._build_manual_form()
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
        self.log_message("🚀 Sorter 2.4.0 initialized. Select your sorting mode and configure options.")
    
    def _build_checkpoint_form(self):
        """Build checkpoint sorting form - matches main.py exactly"""
        # Source directory
        src_row = ctk.CTkFrame(self.checkpoint_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Source Directory", command=lambda: self._choose_directory("source")).pack(side="left")
        self.checkpoint_src_label = ctk.CTkLabel(src_row, text="output", text_color="#888")
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
        self.lora_src_label = ctk.CTkLabel(src_row, text="output", text_color="#888")
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
        self.search_src_label = ctk.CTkLabel(src_row, text="output", text_color="#888")
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
        self.color_src_label = ctk.CTkLabel(src_row, text="output", text_color="#888")
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
        self.flatten_src_label = ctk.CTkLabel(src_row, text="output", text_color="#888")
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

    def _build_extract_form(self):
        """Build the Extract Images form."""
        PRESET_LABELS = list(CROP_PRESETS.keys())

        # --- Source: files or directory ---
        src_row = ctk.CTkFrame(self.extract_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))

        def _pick_files():
            files = filedialog.askopenfilenames(
                title="Select files to extract from",
                filetypes=[
                    ("All supported", " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTENSIONS))),
                    ("PDF", "*.pdf"), ("EPUB", "*.epub"),
                    ("MOBI/AZW", "*.mobi *.azw *.azw3"),
                    ("Comic archives", "*.cbr *.cbz"),
                    ("All files", "*.*"),
                ]
            )
            if files:
                self._extract_input_paths = list(files)
                short = f"{len(files)} file(s) selected" if len(files) > 1 else Path(files[0]).name
                self.extract_src_label.configure(text=short)
                self.log_message(f"📦 Extract source: {short}")

        def _pick_src_dir():
            d = filedialog.askdirectory(title="Select source directory")
            if d:
                self._extract_input_paths = [d]
                self.extract_src_label.configure(text=os.path.basename(d))
                self.log_message(f"📦 Extract source directory: {d}")

        ctk.CTkButton(src_row, text="📄 Select File(s)", command=_pick_files, width=140).pack(side="left", padx=(0, 5))
        ctk.CTkButton(src_row, text="📁 Select Directory", command=_pick_src_dir, width=140).pack(side="left")
        self.extract_src_label = ctk.CTkLabel(src_row, text="No source selected", text_color="#888")
        self.extract_src_label.pack(side="left", padx=(10, 0))

        # --- Output directory ---
        out_row = ctk.CTkFrame(self.extract_frame)
        out_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(out_row, text="📂 Output Directory (Optional)",
                      command=lambda: self._choose_directory("output"), width=210).pack(side="left")
        self.extract_out_label = ctk.CTkLabel(out_row, text="extracted_images", text_color="#888")
        self.extract_out_label.pack(side="left", padx=(10, 0))

        # --- Folder prefix + min dimensions ---
        opts_row = ctk.CTkFrame(self.extract_frame)
        opts_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(opts_row, text="Folder prefix:").pack(side="left")
        self.extract_prefix_entry = ctk.CTkEntry(opts_row, width=120, placeholder_text="optional")
        self.extract_prefix_entry.pack(side="left", padx=(5, 20))

        ctk.CTkLabel(opts_row, text="Min W:").pack(side="left")
        self.extract_min_w = ctk.CTkEntry(opts_row, width=55, placeholder_text="512")
        self.extract_min_w.pack(side="left", padx=(5, 10))

        ctk.CTkLabel(opts_row, text="Min H:").pack(side="left")
        self.extract_min_h = ctk.CTkEntry(opts_row, width=55, placeholder_text="512")
        self.extract_min_h.pack(side="left", padx=5)

        # --- Crop preset ---
        crop_row = ctk.CTkFrame(self.extract_frame)
        crop_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(crop_row, text="Crop preset:").pack(side="left")
        self.extract_crop_var = ctk.StringVar(value=PRESET_LABELS[0])
        self.extract_crop_menu = ctk.CTkOptionMenu(
            crop_row,
            variable=self.extract_crop_var,
            values=PRESET_LABELS,
            command=self._on_crop_preset_change,
            width=250,
        )
        self.extract_crop_menu.pack(side="left", padx=(10, 15))

        ctk.CTkLabel(crop_row, text="Mode:").pack(side="left")
        self.extract_crop_mode_var = ctk.StringVar(value="center")
        self.extract_crop_mode_menu = ctk.CTkOptionMenu(
            crop_row,
            variable=self.extract_crop_mode_var,
            values=["center", "face"],
            width=100,
        )
        self.extract_crop_mode_menu.pack(side="left", padx=(5, 0))

        # --- Custom size row (shown only for "Custom...") ---
        self.extract_custom_row = ctk.CTkFrame(self.extract_frame)
        # Not packed until preset = Custom...
        ctk.CTkLabel(self.extract_custom_row, text="Custom W:").pack(side="left")
        self.extract_custom_w = ctk.CTkEntry(self.extract_custom_row, width=70, placeholder_text="px")
        self.extract_custom_w.pack(side="left", padx=(5, 15))
        ctk.CTkLabel(self.extract_custom_row, text="Custom H:").pack(side="left")
        self.extract_custom_h = ctk.CTkEntry(self.extract_custom_row, width=70, placeholder_text="px")
        self.extract_custom_h.pack(side="left", padx=5)

        # --- Chain-to-sort option ---
        chain_row = ctk.CTkFrame(self.extract_frame)
        chain_row.pack(fill="x", padx=15, pady=5)

        self.extract_chain_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(chain_row, text="Chain to sort after extraction:",
                        variable=self.extract_chain_var).pack(side="left", padx=(0, 10))

        self.extract_chain_mode_var = ctk.StringVar(value="Sort by Checkpoint")
        self.extract_chain_menu = ctk.CTkOptionMenu(
            chain_row,
            variable=self.extract_chain_mode_var,
            values=["Sort by Checkpoint", "Sort by Color", "Flatten Images"],
            width=180,
        )
        self.extract_chain_menu.pack(side="left")

        # --- Info ---
        ctk.CTkLabel(
            self.extract_frame,
            text="📦 Extracts images from PDF, EPUB, MOBI, CBZ, CBR files. Face crop requires mediapipe.",
            text_color="#aaa", font=ctk.CTkFont(size=11),
        ).pack(padx=15, pady=(5, 15))

        # Internal state
        self._extract_input_paths = []

    def _on_crop_preset_change(self, value):
        if value == "Custom...":
            self.extract_custom_row.pack(fill="x", padx=15, pady=(0, 5))
        else:
            self.extract_custom_row.pack_forget()

    def extract_images(self):
        """Run image extraction, then optionally chain to a sort operation."""
        if not self._extract_input_paths:
            messagebox.showerror("Error", "Please select source file(s) or directory.")
            return

        output_dir = self.output_dir if self.output_dir else "extracted_images"

        try:
            min_w = int(self.extract_min_w.get().strip() or 512)
            min_h = int(self.extract_min_h.get().strip() or 512)
        except ValueError:
            min_w = min_h = 512

        preset_label = self.extract_crop_var.get()
        crop_size = CROP_PRESETS.get(preset_label)
        if crop_size == "custom":
            try:
                crop_size = (int(self.extract_custom_w.get()), int(self.extract_custom_h.get()))
            except ValueError:
                messagebox.showerror("Error", "Invalid custom crop dimensions.")
                return

        crop_mode = self.extract_crop_mode_var.get() if crop_size else "none"
        folder_prefix = self.extract_prefix_entry.get().strip()
        chain = self.extract_chain_var.get()
        chain_mode = self.extract_chain_mode_var.get()

        self.log_message(f"📦 Starting extraction → {output_dir}  crop={preset_label}  mode={crop_mode}")

        progress_window = ProgressWindow(self, "Extracting Images", output_dir)

        def run_extract():
            try:
                extractor = ImageExtractorSorter(
                    logger=self.logger,
                    min_width=min_w,
                    min_height=min_h,
                    output_dir=output_dir,
                    folder_prefix=folder_prefix,
                    crop_size=crop_size,
                    crop_mode=crop_mode,
                )

                def on_progress(completed, total, filename):
                    progress_window.enqueue(("progress", (completed, total, filename)))
                    if filename:
                        progress_window.enqueue(("log", f"Processing: {filename}"))

                results = extractor.process_paths(
                    self._extract_input_paths,
                    progress_callback=on_progress,
                )

                progress_window.enqueue(("log", f"✅ Extracted {results['total_extracted']} images from {results['total_files']} file(s)"))
                progress_window.enqueue(("complete", True))

                # Chain to sort if requested
                if chain and results["total_extracted"] > 0:
                    self.source_dir = results["output_dir"]
                    self.after(500, lambda: self._run_chained_sort(chain_mode, results["output_dir"]))

            except Exception as e:
                progress_window.enqueue(("error", str(e)))
                self.logger.log_error(f"Extraction failed: {e}", str(self._extract_input_paths), "Extraction")

        Thread(target=run_extract, daemon=True).start()

    def _run_chained_sort(self, chain_mode: str, source_dir: str):
        """Switch to the selected sort mode pre-filled with extracted output."""
        self.source_dir = source_dir
        self.mode_var.set(chain_mode)
        self._switch_mode(chain_mode)
        self.log_message(f"🔗 Chained to '{chain_mode}' — source set to extracted folder.")

    def _build_manual_form(self):
        """Build the Manual Sort (Triage) form."""
        # Source directory
        src_row = ctk.CTkFrame(self.manual_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Image Folder",
                      command=lambda: self._choose_directory("source")).pack(side="left")
        self.manual_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.manual_src_label.pack(side="left", padx=(10, 0))

        # Bucket names
        buckets_row = ctk.CTkFrame(self.manual_frame)
        buckets_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(buckets_row, text="Bucket names:").pack(side="left")

        self.manual_bucket_entries = []
        defaults = ["Keep", "Favorites", "Maybe"]
        for i in range(3):
            e = ctk.CTkEntry(buckets_row, width=110, placeholder_text=f"Bucket {i+1}")
            e.insert(0, defaults[i])
            e.pack(side="left", padx=5)
            self.manual_bucket_entries.append(e)

        ctk.CTkLabel(buckets_row, text=f"+ {TRASH_BUCKET} (always)",
                     text_color="#F44336").pack(side="left", padx=(10, 0))

        # Info
        ctk.CTkLabel(
            self.manual_frame,
            text="🖼️ Visual triage: browse a gallery, view full-size, press 1-4 to bucket each image,\n"
                 "then Execute to move them into labeled subfolders. Unassigned images stay in place.",
            text_color="#aaa", font=ctk.CTkFont(size=11), justify="left",
        ).pack(padx=15, pady=(5, 15))

    def manual_sort(self):
        """Open the triage window for the selected folder."""
        if not self.source_dir or not os.path.isdir(self.source_dir):
            messagebox.showerror("Error", "Please select an image folder first.")
            return

        bucket_names = [e.get().strip() for e in self.manual_bucket_entries if e.get().strip()]
        if not bucket_names:
            bucket_names = ["Keep"]

        sorter = ManualSorter(self.logger, self.source_dir, bucket_names)

        if not sorter.images:
            messagebox.showerror("Error", "No images found in the selected folder.\n"
                                 f"Supported: {', '.join(sorted(IMAGE_EXTENSIONS))}")
            return

        self.log_message(f"🖼️ Opening triage: {len(sorter.images)} images, buckets: {', '.join(sorter.buckets)}")
        TriageWindow(self, sorter, self.log_message)

    def _build_metadata_form(self):
        """Build metadata generation form"""
        # Source directory
        src_row = ctk.CTkFrame(self.metadata_frame)
        src_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkButton(src_row, text="📁 Select Source Directory", command=lambda: self._choose_directory("source")).pack(side="left")
        self.metadata_src_label = ctk.CTkLabel(src_row, text="output", text_color="#888")
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
            # Start dialog in current source directory or ComfyUI output default
            initial_dir = self.source_dir if self.source_dir and os.path.exists(self.source_dir) else r"D:\ComfyUI_windows_portable\ComfyUI\output"
            directory = filedialog.askdirectory(title="Select Source Directory", initialdir=initial_dir)
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
                elif self.mode_var.get() == "Manual Sort (Triage)":
                    self.manual_src_label.configure(text=os.path.basename(directory))
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
                elif self.mode_var.get() == "Extract Images":
                    self.extract_out_label.configure(text=os.path.basename(directory))
                elif self.mode_var.get() == "Generate Metadata":
                    self.metadata_out_label.configure(text=os.path.basename(directory))

                self.log_message(f"📂 Output directory selected: {directory}")
    
    def _switch_mode(self, choice=None):
        """Switch between different sorting modes"""
        # Hide all frames
        for frame in [self.checkpoint_frame, self.lora_frame, self.search_frame, self.color_frame, self.flatten_frame, self.extract_frame, self.manual_frame, self.metadata_frame, self.logs_frame]:
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
        elif mode == "Extract Images":
            self.extract_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("📦 Extract images mode selected")
        elif mode == "Manual Sort (Triage)":
            self.manual_frame.pack(fill="x", padx=0, pady=0)
            self.log_message("🖼️ Manual sort (triage) mode selected")
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
        elif mode == "Extract Images":
            self.extract_images()
        elif mode == "Manual Sort (Triage)":
            self.manual_sort()
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
