"""UI wrapper for text_file_sorter.py.

Allows the user to select a directory, provide up to four
placeholder strings and choose whether to move or copy the text files.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import text_file_sorter as sorter


class SorterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Text File Sorter")
        self.geometry("500x350")
        self.resizable(False, False)

        self.directory = tk.StringVar()
        self.placeholders = {name: tk.StringVar() for name in ("A", "B", "C", "D")}
        self.move_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        # Directory selection
        dir_frame = ttk.Frame(frm)
        dir_frame.pack(fill="x", pady=5)
        ttk.Label(dir_frame, text="Root Folder:").pack(side="left")
        ttk.Entry(dir_frame, textvariable=self.directory, width=40).pack(side="left", padx=5)
        ttk.Button(dir_frame, text="Browse", command=self._choose_dir).pack(side="left")

        # Placeholder entries
        for idx, name in enumerate(["A", "B", "C", "D"], start=1):
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"Placeholder {name}:").pack(side="left")
            ttk.Entry(row, textvariable=self.placeholders[name], width=30).pack(side="left", padx=5)
            ttk.Label(row, text="(leave blank for N/A)").pack(side="left")

        # Move/Copy toggle
        move_row = ttk.Frame(frm)
        move_row.pack(fill="x", pady=10)
        ttk.Checkbutton(move_row, text="Move files instead of copy", variable=self.move_var).pack(side="left")

        # Run button
        ttk.Button(frm, text="Run", command=self._run).pack(pady=5)

        # Status
        self.status = tk.Text(frm, height=8, state="disabled")
        self.status.pack(fill="both", expand=True, pady=(5, 0))

    def _choose_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.directory.set(folder)

    def _run(self):
        if not self.directory.get():
            messagebox.showwarning("Missing Directory", "Select a folder first.")
            return
        threading.Thread(target=self._do_sort, daemon=True).start()

    def _do_sort(self):
        self._log("Starting...\n")
        placeholders = {k: v.get() or None for k, v in self.placeholders.items()}
        try:
            sorter.sort_text_files(self.directory.get(), placeholders, move=self.move_var.get())
            self._log("Finished\n")
        except Exception as e:
            self._log(f"Error: {e}\n")

    def _log(self, msg: str) -> None:
        self.status.configure(state="normal")
        self.status.insert("end", msg)
        self.status.see("end")
        self.status.configure(state="disabled")


if __name__ == "__main__":
    app = SorterApp()
    app.mainloop()
