#!/usr/bin/env python3
"""
Batch Rename and Sort - ComfyUI Workflow Tool:
1) Rename images by Base+LoRA-sorted GEN
2) Generate metadata files into '<sorted_root>/Gen Data'
3) Sort (copy/move) renamed PNGs into folders named after checkpoint filenames
4) Gather non-PNG/other files into '<sorted_root>/Other Files'

Usage:
    python batch_rename_and_sort.py <directory> <user_string> [<out_dir>] [--move] [--retain-old]
"""
import os
import json
import re
import shutil
from PIL import Image

# --- Helpers ---

def extract_comfyui_metadata(image_path):
    try:
        with Image.open(image_path) as img:
            data = img.info.get('prompt') or img.info.get('parameters')
        return json.loads(data) if data else None
    except Exception as e:
        print(f"[Meta Error] {image_path}: {e}")
        return None


def filter_metadata_for_grouping(metadata):
    base = None
    loras = []
    for entry in metadata.values():
        inputs = entry.get('inputs', {})
        if base is None and 'ckpt_name' in inputs:
            base = inputs['ckpt_name']
        if 'lora_name' in inputs:
            loras.append(inputs['lora_name'])
    loras = sorted(set(loras))
    return (base or 'None') + (' | ' + ','.join(loras) if loras else '')

# --- Step 1: Rename PNGs ---

def rename_files(directory, user_string):
    pngs = [f for f in os.listdir(directory) if f.lower().endswith('.png')]
    records = []
    for name in pngs:
        path = os.path.join(directory, name)
        meta = extract_comfyui_metadata(path)
        group = filter_metadata_for_grouping(meta) if meta else 'None'
        records.append({'orig': name, 'path': path, 'group': group})

    def version_key(k):
        m = re.search(r"(\d+\.\d+)", k)
        return float(m.group(1)) if m else float('inf')

    groups = sorted({r['group'] for r in records}, key=lambda g: (version_key(g), g))
    gen_map = {}
    counter = 1
    for g in groups:
        gen_map[g] = 0 if g == 'None' else counter
        counter += (g != 'None')

    renamed = []
    idx = 1
    for rec in sorted(records, key=lambda x: (version_key(x['group']), x['orig'])):
        gen = gen_map[rec['group']]
        new_name = f"[{user_string}] Gen {gen:02d} ${idx:04d}.png"
        base, ext = os.path.splitext(new_name)
        unique = new_name
        suffix = 1
        while os.path.exists(os.path.join(directory, unique)):
            unique = f"{base}_{suffix}{ext}"
            suffix += 1
        new_path = os.path.join(directory, unique)
        os.rename(rec['path'], new_path)
        print(f"[REN] {rec['orig']} -> {unique}")
        renamed.append({'path': new_path, 'gen': gen})
        idx += 1
    return renamed

# --- Step 2: Create Metadata Files ---

def filter_params(metadata):
    keys = {'ckpt_name','lora_name','vae_name','emb_name','strength_model','strength_clip'}
    out = {}
    for entry in metadata.values():
        inputs = entry.get('inputs', {})
        keep = {k: inputs[k] for k in inputs if k in keys}
        if keep:
            out.setdefault('params', []).append(keep)
    return out


def format_metadata(filtered):
    lines = []
    for p in filtered.get('params', []):
        if 'ckpt_name' in p:
            lines.append(f"Base Model: {os.path.basename(p['ckpt_name'])}")
        if 'lora_name' in p:
            lines.append(
                f"LoRA: {os.path.basename(p['lora_name'])}"
                + f" (SM={p.get('strength_model','N/A')}, SC={p.get('strength_clip','N/A')})"
            )
        if 'vae_name' in p:
            lines.append(f"VAE: {os.path.basename(p['vae_name'])}")
        if 'emb_name' in p:
            lines.append(f"Embedding: {os.path.basename(p['emb_name'])}")
    return "\n".join(lines) or 'No metadata found.'


def create_gen_meta_files(src_dir, renamed, gen_data_dir):
    os.makedirs(gen_data_dir, exist_ok=True)
    by_gen = {}
    for rec in renamed:
        meta = extract_comfyui_metadata(rec['path']) or {}
        filtered = filter_params(meta)
        text = format_metadata(filtered)
        base = os.path.splitext(os.path.basename(rec['path']))[0]
        txt_path = os.path.join(gen_data_dir, f"{base}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[TXT] {os.path.basename(txt_path)}")
        by_gen.setdefault(rec['gen'], []).append(text)

    for gen, texts in by_gen.items():
        file = os.path.join(gen_data_dir, f"GEN {gen} META.txt")
        with open(file, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(texts))
        print(f"[GEN] {os.path.basename(file)}")

    bundle = os.path.join(gen_data_dir, 'ALL_GEN_METADATA_BUNDLE.txt')
    with open(bundle, 'w', encoding='utf-8') as bf:
        for gen in sorted(by_gen):
            bf.write(f"GEN {gen}\n" + '-'*30 + "\n")
            bf.write("\n\n".join(by_gen[gen]) + "\n\n")
    print(f"[BUNDLE] {os.path.basename(bundle)}")

# --- Step 3: Sort PNGs ---

def get_base_checkpoint(image_path):
    meta = extract_comfyui_metadata(image_path)
    if not meta:
        return None
    for entry in meta.values():
        ckpt = entry.get('inputs', {}).get('ckpt_name')
        if ckpt:
            return os.path.splitext(ckpt.replace('\\','/').split('/')[-1])[0]
    return None


def sanitize(name):
    return ''.join(c for c in name if c.isalnum() or c in '-_.') or 'NO_BASE_MODEL'


def sort_by_base(src_dir, sorted_root, move=False):
    for fname in os.listdir(src_dir):
        if not fname.lower().endswith('.png'):
            continue
        src = os.path.join(src_dir, fname)
        base_name = get_base_checkpoint(src) or 'NO_BASE_MODEL'
        folder = sanitize(base_name)
        dest_folder = os.path.join(sorted_root, folder)
        os.makedirs(dest_folder, exist_ok=True)
        dest = os.path.join(dest_folder, fname)
        if move:
            shutil.move(src, dest)
            action = 'Moved'
        else:
            shutil.copy2(src, dest)
            action = 'Copied'
        print(f"[{action}] {fname} -> {folder}")

# --- Step 4: Main ---
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Batch rename + sort + metadata for ComfyUI PNGs')
    parser.add_argument('directory', help='Folder with PNGs')
    parser.add_argument('user_string', help='Prefix for renaming')
    parser.add_argument('out_dir', nargs='?', help='Optional sorted root (default: <dir>/sorted)')
    parser.add_argument('--move', action='store_true', help='Move vs copy')
    parser.add_argument('--retain-old', action='store_true', help='Keep existing sorted root')
    args = parser.parse_args()

    src_dir = args.directory
    sorted_root = args.out_dir if args.out_dir else os.path.join(src_dir, 'sorted')

    # Clean or prepare sorted root
    if os.path.exists(sorted_root) and not args.retain_old:
        shutil.rmtree(sorted_root)
    os.makedirs(sorted_root, exist_ok=True)

    # Step 1: Rename
    renamed = rename_files(src_dir, args.user_string)

    # Step 2: Metadata
    gen_data_dir = os.path.join(sorted_root, 'Gen Data')
    create_gen_meta_files(src_dir, renamed, gen_data_dir)

    # Step 3: Sort PNGs into folders
    sort_by_base(src_dir, sorted_root, move=args.move)

    # Step 4: Move other files
    other_root = os.path.join(sorted_root, 'Other Files')
    os.makedirs(other_root, exist_ok=True)
    for fname in os.listdir(src_dir):
        path = os.path.join(src_dir, fname)
        if os.path.isfile(path) and not fname.lower().endswith('.png'):
            shutil.move(path, os.path.join(other_root, fname))
            print(f"[Moved Other] {fname}")
