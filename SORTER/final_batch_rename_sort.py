#!/usr/bin/env python3
"""
Enhanced Batch Rename and Sort - ComfyUI Workflow Tool:
1) Rename images by Base+LoRA-sorted GEN
2) Generate comprehensive metadata files into '<sorted_root>/Gen Data'
   - Individual .txt files with detailed workflow parameters
   - Generation summaries and bundle files
   - Optional detailed workflow analysis files
3) Sort (copy/move) renamed PNGs into folders named after checkpoint filenames
4) Gather non-PNG/other files into '<sorted_root>/Other Files'

New Features:
- Comprehensive metadata extraction including prompts, sampling parameters, seeds, ControlNet, etc.
- Detailed workflow analysis with node usage statistics
- Backward compatibility with compact metadata format
- Enhanced formatting with organized sections

Usage:
    python final_batch_rename_sort.py <directory> <user_string> [<out_dir>] [options]
    
Options:
    --move              Move files instead of copying
    --retain-old        Keep existing sorted root directory
    --detailed-meta     Create detailed workflow analysis files
    --compact-meta      Use compact metadata format (legacy style)
"""
import os
import json
import re
import shutil
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
    base_candidates = []
    loras = []
    
    for node_id, entry in metadata.items():
        class_type = entry.get('class_type', '')
        inputs = entry.get('inputs', {})
        
        # Collect checkpoint candidates, but skip refiner nodes
        if 'ckpt_name' in inputs:
            is_refiner = ('refiner' in class_type.lower() or 
                         'refiner_ckpt' in inputs or 
                         'refiner_model' in inputs or
                         ('base_ckpt' in inputs and 'refiner_ckpt' in inputs))
            
            if not is_refiner:
                base_candidates.append(inputs['ckpt_name'])
        
        if 'lora_name' in inputs:
            loras.append(inputs['lora_name'])
    
    # Use the first non-refiner checkpoint as base
    base = base_candidates[0] if base_candidates else None
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

def safe_basename(path):
    """Safely get basename from a path, handling None and non-string values"""
    if path is None:
        return 'N/A'
    if isinstance(path, list):
        return str(path)
    try:
        return os.path.basename(str(path))
    except:
        return str(path)

def extract_comprehensive_metadata(metadata):
    """Extract comprehensive metadata from ComfyUI workflow JSON"""
    if not metadata:
        return {}
    
    result = {
        'models': {},
        'prompts': {},
        'sampling': {},
        'image_params': {},
        'seeds': [],
        'loras': [],
        'embeddings': {'positive': [], 'negative': []},
        'controlnets': [],
        'upscaling': {},
        'refiner': {},
        'other_nodes': {}
    }
    
    for node_id, entry in metadata.items():
        class_type = entry.get('class_type', '')
        inputs = entry.get('inputs', {})
        
        # Extract model information - prioritize base models over refiners
        if 'ckpt_name' in inputs:
            is_refiner = ('refiner' in class_type.lower() or 
                         'refiner_ckpt' in inputs or 
                         'refiner_model' in inputs or
                         ('base_ckpt' in inputs and 'refiner_ckpt' in inputs))
            
            # Only set as main checkpoint if it's not a refiner and we haven't found one yet
            if not is_refiner and 'checkpoint' not in result['models']:
                result['models']['checkpoint'] = inputs['ckpt_name']
        
        if 'vae_name' in inputs:
            result['models']['vae'] = inputs['vae_name']
        
        # Extract refiner information - improved detection
        if ('refiner' in class_type.lower() or 
            any(key in inputs for key in ['refiner_ckpt', 'refiner_model']) or
            (class_type in ['KSamplerAdvanced'] and 'start_at_step' in inputs and 'refiner' in str(inputs).lower()) or
            ('base_ckpt' in inputs and 'refiner_ckpt' in inputs)):  # Only treat base_ckpt as refiner if refiner_ckpt is also present
            
            refiner_info = {}
            
            # Extract refiner checkpoint
            if 'refiner_ckpt' in inputs:
                refiner_info['model'] = inputs['refiner_ckpt']
            elif 'refiner_model' in inputs:
                refiner_info['model'] = inputs['refiner_model']
            
            # Extract base model for refiner - only if this is actually a refiner node
            if 'base_ckpt' in inputs and ('refiner_ckpt' in inputs or 'refiner_model' in inputs or 'refiner' in class_type.lower()):
                refiner_info['base_model'] = inputs['base_ckpt']
                
            # Extract refiner timing settings
            if 'switch_at' in inputs:
                refiner_info['switch_at'] = inputs['switch_at']
            if 'start_at_step' in inputs:
                refiner_info['start_at_step'] = inputs['start_at_step']
            if 'end_at_step' in inputs:
                refiner_info['end_at_step'] = inputs['end_at_step']
            if 'noise_mode' in inputs:
                refiner_info['noise_mode'] = inputs['noise_mode']
                
            if refiner_info:  # Only add if we found refiner data
                refiner_info['class_type'] = class_type
                result['refiner'].update(refiner_info)
        
        # Extract LoRA information
        if 'lora_name' in inputs:
            lora_info = {
                'name': inputs['lora_name'],
                'strength_model': inputs.get('strength_model', 'N/A'),
                'strength_clip': inputs.get('strength_clip', 'N/A')
            }
            result['loras'].append(lora_info)
        
        # Enhanced embedding extraction
        if 'emb_name' in inputs or 'embedding_name' in inputs:
            emb_name = inputs.get('emb_name') or inputs.get('embedding_name')
            # Try to determine if it's positive or negative based on context
            is_negative = any(term in class_type.lower() for term in ['negative', 'neg']) or \
                         any(term in str(inputs).lower() for term in ['negative', 'worst quality', 'low quality'])
            
            emb_info = {
                'name': emb_name,
                'strength': inputs.get('strength', inputs.get('weight', 1.0)),
                'node_type': class_type
            }
            
            if is_negative:
                result['embeddings']['negative'].append(emb_info)
            else:
                result['embeddings']['positive'].append(emb_info)
        
        # Extract prompt information with embedding detection
        if class_type == 'CLIPTextEncode' or 'text' in inputs:
            text_content = inputs.get('text', '')
            if text_content and len(text_content.strip()) > 0:
                # Check for embeddings in the text
                embedding_pattern = r'<([^>]+)>'
                found_embeddings = re.findall(embedding_pattern, text_content)
                
                # Determine if positive or negative prompt
                is_negative = any(neg_word in text_content.lower() for neg_word in ['worst quality', 'low quality', 'blurry', 'ugly', 'bad anatomy'])
                
                if is_negative:
                    result['prompts']['negative'] = text_content
                    # Add found embeddings to negative list
                    for emb in found_embeddings:
                        result['embeddings']['negative'].append({
                            'name': emb,
                            'strength': 'embedded_in_prompt',
                            'node_type': 'text_embedded'
                        })
                else:
                    result['prompts']['positive'] = text_content
                    # Add found embeddings to positive list
                    for emb in found_embeddings:
                        result['embeddings']['positive'].append({
                            'name': emb,
                            'strength': 'embedded_in_prompt',
                            'node_type': 'text_embedded'
                        })
        
        # Extract sampling parameters - prioritize base model sampling over refiner
        if class_type in ['KSampler', 'KSamplerAdvanced']:
            # Check if this is likely a refiner sampler
            is_refiner_sampler = ('refiner' in class_type.lower() or 
                                 'start_at_step' in inputs or 
                                 'end_at_step' in inputs or
                                 ('switch_at' in str(inputs).lower()))
            
            # Only set sampling parameters if we haven't found them yet, or if this is clearly a base model sampler
            if not result['sampling'] or not is_refiner_sampler:
                sampling_params = {
                    'steps': inputs.get('steps'),
                    'cfg': inputs.get('cfg'),
                    'sampler_name': inputs.get('sampler_name'),
                    'scheduler': inputs.get('scheduler'),
                    'denoise': inputs.get('denoise')
                }
                # Only update if we found meaningful parameters
                if any(v is not None for v in sampling_params.values()):
                    result['sampling'].update(sampling_params)
        
        # Extract seed information (exclude FaceDetailer and similar noise)
        if 'seed' in inputs:
            node_type = class_type.lower()
            # Skip face detailer, noise injection, and other processing seeds
            if not any(skip_term in node_type for skip_term in ['facedetailer', 'face_detailer', 'noise', 'detailer']):
                result['seeds'].append({
                    'node': class_type,
                    'seed': inputs['seed']
                })
        
        # Extract image dimensions from various sources
        if class_type == 'EmptyLatentImage':
            result['image_params'].update({
                'width': inputs.get('width'),
                'height': inputs.get('height'),
                'batch_size': inputs.get('batch_size')
            })
        
        # Also check for resolution in other nodes
        if 'resolution' in inputs or ('width' in inputs and 'height' in inputs):
            if 'width' in inputs:
                result['image_params']['width'] = inputs['width']
            if 'height' in inputs:
                result['image_params']['height'] = inputs['height']
            if 'resolution' in inputs:
                result['image_params']['resolution'] = inputs['resolution']
        
        # Extract ControlNet information
        if 'control_net' in class_type.lower() or 'controlnet' in inputs:
            controlnet_info = {
                'type': class_type,
                'strength': inputs.get('strength'),
                'start_percent': inputs.get('start_percent'),
                'end_percent': inputs.get('end_percent')
            }
            if 'control_net_name' in inputs:
                controlnet_info['model'] = inputs['control_net_name']
            result['controlnets'].append(controlnet_info)
        
        # Enhanced upscaling information
        if any(term in class_type.lower() for term in ['upscal', 'esrgan', 'realesrgan', 'ldsr', 'swinir']):
            upscale_info = {
                'method': class_type,
                'scale_by': inputs.get('scale_by'),
                'upscale_method': inputs.get('upscale_method'),
                'tile_size': inputs.get('tile_size'),
                'denoise': inputs.get('denoise')
            }
            
            # Try to get actual model name from various possible inputs
            model_name = None
            for key in ['model_name', 'upscale_model', 'model', 'upscaler']:
                if key in inputs and inputs[key]:
                    model_name = inputs[key]
                    break
            
            if model_name:
                upscale_info['model_name'] = model_name
            
            result['upscaling'].update(upscale_info)
        
        # Capture other interesting parameters
        interesting_params = ['strength', 'noise', 'guidance', 'weight', 'influence']
        for param in interesting_params:
            if param in inputs and param not in ['strength_model', 'strength_clip']:
                result['other_nodes'].setdefault('misc_params', {})[f"{class_type}_{param}"] = inputs[param]
    
    return result


def format_comprehensive_metadata(comprehensive_meta):
    """Format comprehensive metadata into readable text"""
    if not comprehensive_meta:
        return 'No metadata found.'
    
    lines = []
    
    # Models section
    if comprehensive_meta.get('models'):
        lines.append("=== MODELS ===")
        models = comprehensive_meta['models']
        if 'checkpoint' in models:
            lines.append(f"Base Model: {safe_basename(models['checkpoint'])}")
        if 'vae' in models:
            lines.append(f"VAE: {safe_basename(models['vae'])}")
        lines.append("")
    
    # Refiner section
    if comprehensive_meta.get('refiner') and any(comprehensive_meta['refiner'].values()):
        lines.append("=== REFINER ===")
        refiner = comprehensive_meta['refiner']
        if refiner.get('model'):
            lines.append(f"Refiner Model: {safe_basename(refiner['model'])}")
        if refiner.get('base_model'):
            lines.append(f"Base Model: {safe_basename(refiner['base_model'])}")
        if refiner.get('switch_at') is not None:
            lines.append(f"Switch At: {refiner['switch_at']}")
        if refiner.get('noise_mode'):
            lines.append(f"Noise Mode: {refiner['noise_mode']}")
        lines.append("")
    
    # LoRAs section
    if comprehensive_meta.get('loras'):
        lines.append("=== LORAS ===")
        for i, lora in enumerate(comprehensive_meta['loras'], 1):
            name = safe_basename(lora['name'])
            sm = lora['strength_model']
            sc = lora['strength_clip']
            lines.append(f"LoRA {i}: {name} (Model: {sm}, CLIP: {sc})")
        lines.append("")
    
    # Enhanced Embeddings section
    if comprehensive_meta.get('embeddings'):
        embeddings = comprehensive_meta['embeddings']
        if embeddings.get('positive') or embeddings.get('negative'):
            lines.append("=== EMBEDDINGS ===")
            
            if embeddings.get('positive'):
                lines.append("Positive Embeddings:")
                for emb in embeddings['positive']:
                    name = safe_basename(emb['name']) if '/' in str(emb['name']) or '\\' in str(emb['name']) else emb['name']
                    strength = emb.get('strength', 'N/A')
                    if strength == 'embedded_in_prompt':
                        lines.append(f"  • {name} (embedded in prompt)")
                    else:
                        lines.append(f"  • {name} (strength: {strength})")
            
            if embeddings.get('negative'):
                lines.append("Negative Embeddings:")
                for emb in embeddings['negative']:
                    name = safe_basename(emb['name']) if '/' in str(emb['name']) or '\\' in str(emb['name']) else emb['name']
                    strength = emb.get('strength', 'N/A')
                    if strength == 'embedded_in_prompt':
                        lines.append(f"  • {name} (embedded in prompt)")
                    else:
                        lines.append(f"  • {name} (strength: {strength})")
            lines.append("")
    
    # Prompts section
    if comprehensive_meta.get('prompts'):
        prompts = comprehensive_meta['prompts']
        if 'positive' in prompts:
            lines.append("=== POSITIVE PROMPT ===")
            lines.append(prompts['positive'])
            lines.append("")
        if 'negative' in prompts:
            lines.append("=== NEGATIVE PROMPT ===")
            lines.append(prompts['negative'])
            lines.append("")
    
    # Sampling parameters
    if comprehensive_meta.get('sampling'):
        lines.append("=== SAMPLING PARAMETERS ===")
        sampling = comprehensive_meta['sampling']
        for key, value in sampling.items():
            if value is not None:
                formatted_key = key.replace('_', ' ').title()
                lines.append(f"{formatted_key}: {value}")
        lines.append("")
    
    # Image parameters
    if comprehensive_meta.get('image_params'):
        lines.append("=== IMAGE PARAMETERS ===")
        img_params = comprehensive_meta['image_params']
        for key, value in img_params.items():
            if value is not None:
                formatted_key = key.replace('_', ' ').title()
                lines.append(f"{formatted_key}: {value}")
        lines.append("")
    
    # Seeds
    if comprehensive_meta.get('seeds'):
        lines.append("=== SEEDS ===")
        for seed_info in comprehensive_meta['seeds']:
            lines.append(f"{seed_info['node']}: {seed_info['seed']}")
        lines.append("")
    
    # ControlNet information
    if comprehensive_meta.get('controlnets'):
        lines.append("=== CONTROLNET ===")
        for i, cn in enumerate(comprehensive_meta['controlnets'], 1):
            lines.append(f"ControlNet {i}: {cn['type']}")
            if 'model' in cn:
                lines.append(f"  Model: {safe_basename(cn['model'])}")
            if cn.get('strength') is not None:
                lines.append(f"  Strength: {cn['strength']}")
            if cn.get('start_percent') is not None and cn.get('end_percent') is not None:
                lines.append(f"  Range: {cn['start_percent']} - {cn['end_percent']}")
        lines.append("")
    
    # Enhanced upscaling information
    if comprehensive_meta.get('upscaling'):
        upscale = comprehensive_meta['upscaling']
        if any(upscale.values()):
            lines.append("=== UPSCALING ===")
            if upscale.get('method'):
                lines.append(f"Method: {upscale['method']}")
            if upscale.get('model_name'):
                lines.append(f"Upscale Model: {safe_basename(upscale['model_name'])}")
            if upscale.get('scale_by') is not None:
                lines.append(f"Scale Factor: {upscale['scale_by']}")
            if upscale.get('upscale_method'):
                lines.append(f"Upscale Method: {upscale['upscale_method']}")
            if upscale.get('tile_size'):
                lines.append(f"Tile Size: {upscale['tile_size']}")
            if upscale.get('denoise') is not None:
                lines.append(f"Denoise: {upscale['denoise']}")
            lines.append("")
    
    # Other nodes and parameters
    if comprehensive_meta.get('other_nodes'):
        other = comprehensive_meta['other_nodes']
        if other:
            lines.append("=== OTHER PARAMETERS ===")
            if 'misc_params' in other:
                for param, value in other['misc_params'].items():
                    lines.append(f"{param}: {value}")
            lines.append("")
    
    return "\n".join(lines).strip() or 'No metadata found.'


def create_gen_meta_files(src_dir, renamed, gen_data_dir, use_compact=False):
    os.makedirs(gen_data_dir, exist_ok=True)
    by_gen = {}
    for rec in renamed:
        meta = extract_comfyui_metadata(rec['path']) or {}
        
        if use_compact:
            # Use legacy compact format
            filtered = extract_legacy_metadata(meta)
            text = format_legacy_metadata(filtered)
        else:
            # Use comprehensive format
            comprehensive_meta = extract_comprehensive_metadata(meta)
            text = format_comprehensive_metadata(comprehensive_meta)
        
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
    
    base_candidates = []
    for entry in meta.values():
        class_type = entry.get('class_type', '')
        inputs = entry.get('inputs', {})
        
        # Look for checkpoint names, but skip refiner nodes
        if 'ckpt_name' in inputs:
            is_refiner = ('refiner' in class_type.lower() or 
                         'refiner_ckpt' in inputs or 
                         'refiner_model' in inputs or
                         ('base_ckpt' in inputs and 'refiner_ckpt' in inputs))
            
            if not is_refiner:
                base_candidates.append(inputs['ckpt_name'])
    
    # Return the first non-refiner checkpoint found
    if base_candidates:
        ckpt = base_candidates[0]
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

# --- Step 4: Workflow Analysis ---

def create_workflow_analysis(gen_data_dir, renamed):
    """Create detailed workflow analysis files for debugging and understanding"""
    analysis_dir = os.path.join(gen_data_dir, 'Workflow Analysis')
    os.makedirs(analysis_dir, exist_ok=True)
    
    all_nodes = set()
    all_class_types = set()
    node_usage = {}
    
    workflow_details = []
    
    for rec in renamed:
        meta = extract_comfyui_metadata(rec['path'])
        if not meta:
            continue
            
        filename = os.path.basename(rec['path'])
        workflow_info = {
            'filename': filename,
            'gen': rec['gen'],
            'nodes': {},
            'class_types': set(),
            'total_nodes': len(meta)
        }
        
        for node_id, entry in meta.items():
            class_type = entry.get('class_type', 'Unknown')
            all_nodes.add(node_id)
            all_class_types.add(class_type)
            workflow_info['class_types'].add(class_type)
            workflow_info['nodes'][node_id] = {
                'class_type': class_type,
                'inputs': entry.get('inputs', {})
            }
            
            # Count node usage
            node_usage[class_type] = node_usage.get(class_type, 0) + 1
        
        workflow_details.append(workflow_info)
    
    # Create summary file
    summary_path = os.path.join(analysis_dir, 'Workflow_Summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=== COMFYUI WORKFLOW ANALYSIS SUMMARY ===\n\n")
        f.write(f"Total Images Processed: {len(workflow_details)}\n")
        f.write(f"Unique Node Types Found: {len(all_class_types)}\n")
        f.write(f"Total Unique Node IDs: {len(all_nodes)}\n\n")
        
        f.write("=== NODE TYPE USAGE ===\n")
        for class_type, count in sorted(node_usage.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{class_type}: {count} occurrences\n")
        
        f.write(f"\n=== ALL DETECTED NODE TYPES ===\n")
        for class_type in sorted(all_class_types):
            f.write(f"- {class_type}\n")
    
    print(f"[ANALYSIS] {os.path.basename(summary_path)}")
    
    # Create detailed per-generation analysis
    by_gen = {}
    for workflow in workflow_details:
        by_gen.setdefault(workflow['gen'], []).append(workflow)
    
    for gen, workflows in by_gen.items():
        gen_analysis_path = os.path.join(analysis_dir, f'GEN_{gen:02d}_Analysis.txt')
        with open(gen_analysis_path, 'w', encoding='utf-8') as f:
            f.write(f"=== GENERATION {gen} WORKFLOW ANALYSIS ===\n\n")
            f.write(f"Images in this generation: {len(workflows)}\n\n")
            
            for workflow in workflows:
                f.write(f"File: {workflow['filename']}\n")
                f.write(f"Total Nodes: {workflow['total_nodes']}\n")
                f.write(f"Node Types: {', '.join(sorted(workflow['class_types']))}\n")
                f.write("Detailed Node Structure:\n")
                
                for node_id, node_info in workflow['nodes'].items():
                    f.write(f"  {node_id}: {node_info['class_type']}\n")
                    if node_info['inputs']:
                        for input_key, input_value in node_info['inputs'].items():
                            # Truncate very long values
                            if isinstance(input_value, str) and len(input_value) > 100:
                                input_value = input_value[:100] + "..."
                            f.write(f"    {input_key}: {input_value}\n")
                f.write("\n" + "="*50 + "\n\n")
        
        print(f"[GEN_ANALYSIS] {os.path.basename(gen_analysis_path)}")

# --- Legacy Metadata Functions ---

def extract_legacy_metadata(metadata):
    """Legacy metadata extraction for backward compatibility"""
    keys = {'ckpt_name','lora_name','vae_name','emb_name','strength_model','strength_clip'}
    out = {}
    for entry in metadata.values():
        inputs = entry.get('inputs', {})
        keep = {k: inputs[k] for k in inputs if k in keys}
        if keep:
            out.setdefault('params', []).append(keep)
    return out

def format_legacy_metadata(filtered):
    """Legacy metadata formatting for backward compatibility"""
    lines = []
    for p in filtered.get('params', []):
        if 'ckpt_name' in p:
            lines.append(f"Base Model: {safe_basename(p['ckpt_name'])}")
        if 'lora_name' in p:
            lines.append(
                f"LoRA: {safe_basename(p['lora_name'])}"
                + f" (SM={p.get('strength_model','N/A')}, SC={p.get('strength_clip','N/A')})"
            )
        if 'vae_name' in p:
            lines.append(f"VAE: {safe_basename(p['vae_name'])}")
        if 'emb_name' in p:
            lines.append(f"Embedding: {safe_basename(p['emb_name'])}")
    return "\n".join(lines) or 'No metadata found.'

def extract_advanced_comfyui_params(metadata):
    """Extract advanced ComfyUI-specific parameters"""
    advanced_params = {
        'conditioning': [],
        'preprocessors': [],
        'post_processing': [],
        'custom_nodes': [],
        'schedulers': [],
        'attention': []
    }
    
    for node_id, entry in metadata.items():
        class_type = entry.get('class_type', '')
        inputs = entry.get('inputs', {})
        
        # Conditioning and prompt-related nodes
        if any(term in class_type.lower() for term in ['condition', 'prompt', 'style']):
            advanced_params['conditioning'].append({
                'node_type': class_type,
                'parameters': {k: v for k, v in inputs.items() if k not in ['text']}
            })
        
        # Preprocessors (img2img, controlnet preprocessors, etc.)
        if any(term in class_type.lower() for term in ['preprocess', 'detect', 'extract', 'canny', 'depth']):
            advanced_params['preprocessors'].append({
                'node_type': class_type,
                'parameters': inputs
            })
        
        # Post-processing (upscaling, enhancement, etc.)
        if any(term in class_type.lower() for term in ['upscal', 'enhance', 'sharpen', 'blur']):
            advanced_params['post_processing'].append({
                'node_type': class_type,
                'parameters': inputs
            })
        
        # Custom nodes (anything not in standard ComfyUI)
        if any(term in class_type for term in ['Custom', 'Advanced', 'Enhanced', 'Ultimate']):
            advanced_params['custom_nodes'].append({
                'node_type': class_type,
                'parameters': inputs
            })
        
        # Scheduler-related
        if 'scheduler' in class_type.lower() or 'schedule' in inputs:
            advanced_params['schedulers'].append({
                'node_type': class_type,
                'parameters': inputs
            })
        
        # Attention/cross-attention related
        if any(term in class_type.lower() for term in ['attention', 'cross', 'self']):
            advanced_params['attention'].append({
                'node_type': class_type,
                'parameters': inputs
            })
    
    return advanced_params

def create_html_report(gen_data_dir, renamed, user_string):
    """Create an HTML report for easy viewing of metadata"""
    html_path = os.path.join(gen_data_dir, 'Metadata_Report.html')
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ComfyUI Generation Report - {user_string}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1, h2 {{ color: #333; }}
        .generation-group {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #fafafa; }}
        .image-entry {{ margin: 10px 0; padding: 10px; border-left: 3px solid #007acc; background: white; }}
        .metadata-section {{ margin: 10px 0; }}
        .metadata-section h4 {{ color: #666; margin: 5px 0; }}
        .metadata-content {{ background: #f9f9f9; padding: 8px; border-radius: 3px; font-family: monospace; font-size: 12px; }}
        .stats {{ background: #e7f3ff; padding: 10px; border-radius: 5px; margin: 20px 0; }}
        .prompt {{ background: #fff3cd; padding: 8px; border-radius: 3px; margin: 5px 0; }}
        .negative-prompt {{ background: #f8d7da; padding: 8px; border-radius: 3px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ComfyUI Generation Report: {user_string}</h1>
        <div class="stats">
            <strong>Total Images:</strong> {len(renamed)}<br>
            <strong>Generation Date:</strong> {os.path.basename(gen_data_dir).replace('Gen Data', '')}<br>
            <strong>Generations Found:</strong> {len(set(rec['gen'] for rec in renamed))}
        </div>
"""
    
    # Group by generation
    by_gen = {}
    for rec in renamed:
        by_gen.setdefault(rec['gen'], []).append(rec)
    
    for gen in sorted(by_gen.keys()):
        html_content += f'<div class="generation-group"><h2>Generation {gen:02d}</h2>'
        
        for rec in by_gen[gen]:
            filename = os.path.basename(rec['path'])
            meta = extract_comfyui_metadata(rec['path'])
            comprehensive_meta = extract_comprehensive_metadata(meta) if meta else {}
            
            html_content += f'<div class="image-entry"><h3>{filename}</h3>'
            
            # Add prompts if available
            if comprehensive_meta.get('prompts'):
                prompts = comprehensive_meta['prompts']
                if 'positive' in prompts:
                    html_content += f'<div class="prompt"><strong>Positive:</strong> {prompts["positive"][:200]}{"..." if len(prompts["positive"]) > 200 else ""}</div>'
                if 'negative' in prompts:
                    html_content += f'<div class="negative-prompt"><strong>Negative:</strong> {prompts["negative"][:200]}{"..." if len(prompts["negative"]) > 200 else ""}</div>'
            
            # Add key parameters
            if comprehensive_meta.get('models'):
                models = comprehensive_meta['models']
                html_content += f'<div class="metadata-content"><strong>Base Model:</strong> {os.path.basename(models.get("checkpoint", "N/A"))}</div>'
                if models.get('vae'):
                    html_content += f'<div class="metadata-content"><strong>VAE:</strong> {os.path.basename(models["vae"])}</div>'
            
            # Add refiner information
            if comprehensive_meta.get('refiner') and any(comprehensive_meta['refiner'].values()):
                refiner = comprehensive_meta['refiner']
                if refiner.get('model'):
                    html_content += f'<div class="metadata-content"><strong>Refiner:</strong> {os.path.basename(refiner["model"])} (switch at: {refiner.get("switch_at", "N/A")})</div>'
            
            if comprehensive_meta.get('sampling'):
                sampling = comprehensive_meta['sampling']
                html_content += f'<div class="metadata-content"><strong>Sampling:</strong> Steps: {sampling.get("steps", "N/A")}, CFG: {sampling.get("cfg", "N/A")}, Sampler: {sampling.get("sampler_name", "N/A")}</div>'
            
            if comprehensive_meta.get('loras'):
                loras_text = ", ".join([os.path.basename(lora['name']) for lora in comprehensive_meta['loras']])
                html_content += f'<div class="metadata-content"><strong>LoRAs:</strong> {loras_text}</div>'
            
            # Add embeddings information
            if comprehensive_meta.get('embeddings'):
                embeddings = comprehensive_meta['embeddings']
                if embeddings.get('positive'):
                    pos_embs = ", ".join([emb['name'] for emb in embeddings['positive']])
                    html_content += f'<div class="metadata-content"><strong>Positive Embeddings:</strong> {pos_embs}</div>'
                if embeddings.get('negative'):
                    neg_embs = ", ".join([emb['name'] for emb in embeddings['negative']])
                    html_content += f'<div class="metadata-content"><strong>Negative Embeddings:</strong> {neg_embs}</div>'
            
            # Add upscaling information
            if comprehensive_meta.get('upscaling') and any(comprehensive_meta['upscaling'].values()):
                upscale = comprehensive_meta['upscaling']
                if upscale.get('model_name'):
                    scale_factor = upscale.get('scale_by', 'N/A')
                    html_content += f'<div class="metadata-content"><strong>Upscaling:</strong> {os.path.basename(upscale["model_name"])} (x{scale_factor})</div>'
            
            html_content += '</div>'
        
        html_content += '</div>'
    
    html_content += """
    </div>
</body>
</html>
"""
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[HTML] {os.path.basename(html_path)}")

# --- Step 4: Main ---
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Batch rename + sort + metadata for ComfyUI PNGs')
    parser.add_argument('directory', help='Folder with PNGs')
    parser.add_argument('user_string', help='Prefix for renaming')
    parser.add_argument('out_dir', nargs='?', help='Optional sorted root (default: <dir>/sorted)')
    parser.add_argument('--move', action='store_true', help='Move vs copy')
    parser.add_argument('--retain-old', action='store_true', help='Keep existing sorted root')
    parser.add_argument('--detailed-meta', action='store_true', help='Create detailed workflow analysis files')
    parser.add_argument('--compact-meta', action='store_true', help='Use compact metadata format (legacy style)')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML report for easy viewing')
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
    create_gen_meta_files(src_dir, renamed, gen_data_dir, use_compact=args.compact_meta)
    
    # Step 2a: Create workflow analysis (only if detailed metadata is requested)
    if args.detailed_meta:
        create_workflow_analysis(gen_data_dir, renamed)
    
    # Step 2b: Create HTML report (if requested)
    if args.html_report:
        create_html_report(gen_data_dir, renamed, args.user_string)

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