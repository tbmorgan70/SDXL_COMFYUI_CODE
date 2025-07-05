"""Unified Sorter UI

A single CustomTkinter interface for both the Text File Sorter and
ComfyUI Batch Sorter tools.
"""

import os
import sys
import threading
import shutil

import customtkinter as ctk
from tkinter import filedialog, messagebox

import text_file_sorter
import final_batch_rename_sort as comfy_sort
import color_sorter

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class UnifiedSorter(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("\U0001F9EE Unified Sorter")
        self.geometry("750x750")
        self.configure(padx=20, pady=20)

        self.mode_var = ctk.StringVar(value="ComfyUI Batch Sorter")

        # State vars
        self.text_dir = ""
        self.comfy_src = ""
        self.comfy_out = ""
        self.color_src = ""
        self.color_out = ""
        self.last_sorted_root = None

        self._build_ui()
        self._switch_mode()

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=10)
        top.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top, text="Sort Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        mode_menu = ctk.CTkOptionMenu(top, variable=self.mode_var,
                                     values=["Text File Sorter", "ComfyUI Batch Sorter", "Color Sorter"],
                                     command=lambda _: self._switch_mode())
        mode_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.forms = ctk.CTkFrame(self, corner_radius=10)
        self.forms.pack(fill="x", pady=(0, 10))

        self.text_frame = ctk.CTkFrame(self.forms, corner_radius=10)
        self._build_text_frame()
        self.comfy_frame = ctk.CTkFrame(self.forms, corner_radius=10)
        self._build_comfy_frame()
        self.color_frame = ctk.CTkFrame(self.forms, corner_radius=10)
        self._build_color_frame()

        self.run_btn = ctk.CTkButton(self, text="\u23E9 Run", command=self.run)
        self.run_btn.pack(fill="x", pady=(0, 10))

        self.status = ctk.CTkTextbox(self, width=700, height=400, corner_radius=10)
        self.status.pack(fill="both", expand=True)

    def _build_text_frame(self) -> None:
        dir_row = ctk.CTkFrame(self.text_frame)
        dir_row.pack(fill="x", pady=5)
        ctk.CTkButton(dir_row, text="\U0001F4C2 Select Folder", command=self._choose_text_dir).pack(side="left")
        self.text_dir_label = ctk.CTkLabel(dir_row, text="No folder selected", text_color="#888")
        self.text_dir_label.pack(side="left", padx=5)

        self.placeholders = {}
        for name in ["A", "B", "C", "D"]:
            row = ctk.CTkFrame(self.text_frame)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"Placeholder {name}:").pack(side="left")
            var = ctk.StringVar()
            self.placeholders[name] = var
            ctk.CTkEntry(row, textvariable=var, width=200).pack(side="left", padx=5)

        self.move_text_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self.text_frame, text="Move files instead of copy", variable=self.move_text_var).pack(anchor="w", pady=5)

    def _build_comfy_frame(self) -> None:
        src_row = ctk.CTkFrame(self.comfy_frame)
        src_row.pack(fill="x", pady=5)
        ctk.CTkButton(src_row, text="\U0001F4C2 Select Image Folder", command=self._choose_comfy_src).pack(side="left")
        self.comfy_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.comfy_src_label.pack(side="left", padx=5)

        user_row = ctk.CTkFrame(self.comfy_frame)
        user_row.pack(fill="x", pady=5)
        ctk.CTkLabel(user_row, text="User String:").pack(side="left")
        self.user_entry = ctk.CTkEntry(user_row, width=200)
        self.user_entry.pack(side="left", padx=5)

        out_row = ctk.CTkFrame(self.comfy_frame)
        out_row.pack(fill="x", pady=5)
        ctk.CTkButton(out_row, text="\U0001F5C2 Optional Output", command=self._choose_comfy_out).pack(side="left")
        self.comfy_out_label = ctk.CTkLabel(out_row, text="Will use default if not set", text_color="#888")
        self.comfy_out_label.pack(side="left", padx=5)

        opts = ctk.CTkFrame(self.comfy_frame)
        opts.pack(fill="x", pady=5)
        self.comfy_move_var = ctk.BooleanVar()
        self.comfy_retain_var = ctk.BooleanVar()
        ctk.CTkCheckBox(opts, text="Move files", variable=self.comfy_move_var).pack(side="left", padx=5)
        ctk.CTkCheckBox(opts, text="Retain existing sorted folder", variable=self.comfy_retain_var).pack(side="left", padx=5)

    def _build_color_frame(self) -> None:
        # Source folder selection
        src_row = ctk.CTkFrame(self.color_frame)
        src_row.pack(fill="x", pady=5)
        ctk.CTkButton(src_row, text="\U0001F4C2 Select Image Folder", command=self._choose_color_src).pack(side="left")
        self.color_src_label = ctk.CTkLabel(src_row, text="No folder selected", text_color="#888")
        self.color_src_label.pack(side="left", padx=5)

        # User prefix for renaming
        prefix_row = ctk.CTkFrame(self.color_frame)
        prefix_row.pack(fill="x", pady=5)
        ctk.CTkLabel(prefix_row, text="Color Prefix (optional):").pack(side="left")
        self.color_prefix_entry = ctk.CTkEntry(prefix_row, width=200, placeholder_text="e.g., MySet")
        self.color_prefix_entry.pack(side="left", padx=5)

        # Sorting method selection
        method_row = ctk.CTkFrame(self.color_frame)
        method_row.pack(fill="x", pady=5)
        ctk.CTkLabel(method_row, text="Sort Method:").pack(side="left")
        self.color_method_var = ctk.StringVar(value="enhanced")
        method_menu = ctk.CTkOptionMenu(method_row, variable=self.color_method_var,
                                       values=["enhanced", "original", "brightness", "temperature", "center_focus"])
        method_menu.pack(side="left", padx=5)
        
        # Method descriptions
        method_info = ctk.CTkLabel(method_row, text="Enhanced = Better black handling | Brightness = Dark/Medium/Bright | Temperature = Warm/Cool", 
                                  text_color="#aaa", font=("Arial", 10))
        method_info.pack(side="left", padx=5)

        # Output folder selection
        out_row = ctk.CTkFrame(self.color_frame)
        out_row.pack(fill="x", pady=5)
        ctk.CTkButton(out_row, text="\U0001F5C2 Select Output Folder", command=self._choose_color_out).pack(side="left")
        self.color_out_label = ctk.CTkLabel(out_row, text="Will create 'color_sorted' subfolder if not set", text_color="#888")
        self.color_out_label.pack(side="left", padx=5)

        # Options
        opts = ctk.CTkFrame(self.color_frame)
        opts.pack(fill="x", pady=5)
        self.color_move_var = ctk.BooleanVar()
        self.color_preview_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts, text="Move files", variable=self.color_move_var).pack(side="left", padx=5)
        ctk.CTkCheckBox(opts, text="Create color preview", variable=self.color_preview_var).pack(side="left", padx=5)

        # Info label
        info_label = ctk.CTkLabel(self.color_frame, 
                                 text="🎨 Enhanced Method: Better handling of dark images | Try different methods if results aren't optimal",
                                 text_color="#aaa", font=("Arial", 11))
        info_label.pack(pady=5)

    def _choose_text_dir(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.text_dir = folder
            self.text_dir_label.configure(text=folder)

    def _choose_comfy_src(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.comfy_src = folder
            self.comfy_src_label.configure(text=folder)

    def _choose_comfy_out(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.comfy_out = folder
            self.comfy_out_label.configure(text=folder)

    def _choose_color_src(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.color_src = folder
            self.color_src_label.configure(text=folder)

    def _choose_color_out(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.color_out = folder
            self.color_out_label.configure(text=folder)

    def _switch_mode(self) -> None:
        for widget in self.forms.winfo_children():
            widget.pack_forget()
        if self.mode_var.get() == "Text File Sorter":
            self.text_frame.pack(fill="x")
        elif self.mode_var.get() == "ComfyUI Batch Sorter":
            self.comfy_frame.pack(fill="x")
        else:
            self.color_frame.pack(fill="x")

    def run(self) -> None:
        if self.mode_var.get() == "Text File Sorter":
            if not self.text_dir:
                messagebox.showwarning("Missing Folder", "Select a folder to sort")
                return
            threading.Thread(target=self._do_text_sort, daemon=True).start()
        elif self.mode_var.get() == "ComfyUI Batch Sorter":
            if not self.comfy_src or not self.user_entry.get().strip():
                messagebox.showwarning("Missing Info", "Select image folder and enter user string")
                return
            threading.Thread(target=self._do_comfy_sort, daemon=True).start()
        else:
            if not self.color_src:
                messagebox.showwarning("Missing Folder", "Select an image folder to sort by color")
                return
            threading.Thread(target=self._do_color_sort, daemon=True).start()

    # --- Logging helpers ---
    def write(self, txt: str) -> None:
        self.status.insert("end", txt)
        self.status.see("end")

    def flush(self) -> None:
        pass

    def log(self, msg: str) -> None:
        self.status.insert("end", msg + "\n")
        self.status.see("end")

    def clear_log(self) -> None:
        self.status.delete("0.0", "end")

    # --- Sorting operations ---
    def _do_text_sort(self) -> None:
        self.clear_log()
        self.log("Starting text file sort...\n")
        orig = sys.stdout
        sys.stdout = self
        try:
            placeholders = {k: v.get() or None for k, v in self.placeholders.items()}
            text_file_sorter.sort_text_files(self.text_dir, placeholders, move=self.move_text_var.get())
            sys.stdout = orig
            self.log("\nDone")
        except Exception as e:
            sys.stdout = orig
            self.log(f"\nError: {e}")

    def _do_comfy_sort(self) -> None:
        self.clear_log()
        self.log("Starting ComfyUI batch sort...\n")
        orig = sys.stdout
        sys.stdout = self
        try:
            sorted_root = self.comfy_out if self.comfy_out else os.path.join(self.comfy_src, "sorted")
            self.last_sorted_root = sorted_root
            if os.path.exists(sorted_root) and not self.comfy_retain_var.get():
                shutil.rmtree(sorted_root)

            renamed = comfy_sort.rename_files(self.comfy_src, self.user_entry.get().strip())
            gen_data_dir = os.path.join(sorted_root, 'Gen Data')
            comfy_sort.create_gen_meta_files(self.comfy_src, renamed, gen_data_dir)
            comfy_sort.sort_by_base(self.comfy_src, sorted_root, move=self.comfy_move_var.get())

            other_root = os.path.join(sorted_root, 'Other Files')
            os.makedirs(other_root, exist_ok=True)
            for fn in os.listdir(self.comfy_src):
                p = os.path.join(self.comfy_src, fn)
                if os.path.isfile(p) and not fn.lower().endswith('.png'):
                    shutil.move(p, os.path.join(other_root, fn))
                    print(f"[Moved Other] {fn}")

            sys.stdout = orig
            self.log("\nDone")
        except Exception as e:
            sys.stdout = orig
            self.log(f"\nError: {e}")

    def _do_color_sort(self) -> None:
        self.clear_log()
        self.log("Starting color-based image sort...\n")
        orig = sys.stdout
        sys.stdout = self
        try:
            # Determine output directory
            output_dir = self.color_out if self.color_out else os.path.join(self.color_src, "color_sorted")
            
            # Get user prefix and method
            user_prefix = self.color_prefix_entry.get().strip()
            sort_method = self.color_method_var.get()
            
            # Sort images by color
            processed_files, color_stats = color_sorter.sort_images_by_color(
                self.color_src, 
                output_dir, 
                move_files=self.color_move_var.get(),
                user_prefix=user_prefix,
                sort_method=sort_method
            )
            
            # Create color preview if requested
            if self.color_preview_var.get():
                color_sorter.create_color_preview(output_dir, color_stats)
            
            sys.stdout = orig
            self.log("\n=== Color Sorting Summary ===")
            self.log(f"Total images processed: {len(processed_files)}")
            self.log("Color distribution:")
            for color, count in sorted(color_stats.items()):
                self.log(f"  {color}: {count} files")
            self.log(f"\nOutput directory: {output_dir}")
            self.log("\nDone! 🎨")
            
        except Exception as e:
            sys.stdout = orig
            self.log(f"\nError: {e}")


if __name__ == "__main__":
    app = UnifiedSorter()
    app.mainloop()
