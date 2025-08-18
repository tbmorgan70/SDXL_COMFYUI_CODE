"""Simple Text File Sorter

Searches text files in a directory for user provided placeholder
strings. Files containing a placeholder string are moved or copied
into a folder named after that string. Files with no matches are
placed in a "NO DATA" folder.
"""

import os
import shutil
from typing import Dict, Optional


def sort_text_files(directory: str, placeholders: Dict[str, Optional[str]], move: bool = False) -> None:
    """Sort .txt files by placeholder strings.

    Parameters
    ----------
    directory: path to search for .txt files
    placeholders: mapping of placeholder labels to search strings. Any value that
        is falsy or equal to "N/A" is ignored.
    move: if True, files are moved; otherwise they are copied.
    """
    directory = os.path.abspath(directory)

    # Prepare destination folders
    valid_searches = []
    for label, text in placeholders.items():
        if text and text.upper() != "N/A":
            dest = os.path.join(directory, text)
            os.makedirs(dest, exist_ok=True)
            valid_searches.append(text)
    no_data_folder = os.path.join(directory, "NO DATA")
    os.makedirs(no_data_folder, exist_ok=True)

    for fname in os.listdir(directory):
        if not fname.lower().endswith(".txt"):
            continue
        path = os.path.join(directory, fname)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            print(f"[ERROR] Failed to read {fname}: {e}")
            continue

        destination = None
        for search in valid_searches:
            if search in content:
                destination = os.path.join(directory, search)
                break

        if destination is None:
            destination = no_data_folder

        dest_path = os.path.join(destination, fname)
        if move:
            shutil.move(path, dest_path)
            action = "Moved"
        else:
            shutil.copy2(path, dest_path)
            action = "Copied"
        print(f"[{action}] {fname} -> {os.path.basename(destination)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sort text files by placeholder strings")
    parser.add_argument("directory", help="Folder containing .txt files")
    parser.add_argument("--A", dest="A", help="Placeholder A text")
    parser.add_argument("--B", dest="B", help="Placeholder B text")
    parser.add_argument("--C", dest="C", help="Placeholder C text")
    parser.add_argument("--D", dest="D", help="Placeholder D text")
    parser.add_argument("--move", action="store_true", help="Move files instead of copying")
    args = parser.parse_args()

    placeholders = {"A": args.A, "B": args.B, "C": args.C, "D": args.D}

    sort_text_files(args.directory, placeholders, move=args.move)
