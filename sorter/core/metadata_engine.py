"""
Sorter - Bulletproof Metadata Engine

Handles ComfyUI metadata extraction with robust error handling,
memory optimization, and support for large batches (500+ files).

Key Features:
- Multiple fallback extraction methods
- Memory-efficient batch processing  
- Comprehensive error recovery
- Detailed extraction diagnostics
"""

import json
import os
import re
import sys
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import traceback
from PIL import Image

class MetadataExtractor:
    """Bulletproof metadata extraction for ComfyUI images"""
    
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'corrupted_files': 0,
            'no_metadata_files': 0,
            'memory_errors': 0
        }
        self.failed_files = []
        
    def extract_single(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a single image with multiple fallback methods
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary of metadata or None if extraction fails
        """
        try:
            # Method 1: Standard PIL extraction
            with Image.open(image_path) as img:
                # Try 'prompt' field first (ComfyUI standard)
                prompt_data = img.info.get('prompt')
                if prompt_data:
                    metadata = json.loads(prompt_data)
                    self.stats['successful_extractions'] += 1
                    return metadata
                
                # Method 2: Try 'parameters' field (fallback)
                params_data = img.info.get('parameters')
                if params_data:
                    metadata = json.loads(params_data)
                    self.stats['successful_extractions'] += 1
                    return metadata
                
                # Method 3: Try other common metadata fields
                for field in ['workflow', 'extra_pnginfo', 'exif']:
                    data = img.info.get(field)
                    if data:
                        try:
                            if isinstance(data, str):
                                metadata = json.loads(data)
                            else:
                                metadata = data
                            self.stats['successful_extractions'] += 1
                            return metadata
                        except (json.JSONDecodeError, TypeError):
                            continue
                
                # No metadata found
                self.stats['no_metadata_files'] += 1
                return None
                
        except (OSError, IOError) as e:
            # File corruption or access issues
            self.stats['corrupted_files'] += 1
            self.failed_files.append((image_path, f"File access error: {str(e)}"))
            return None
            
        except MemoryError as e:
            # Memory issues with large files
            self.stats['memory_errors'] += 1 
            self.failed_files.append((image_path, f"Memory error: {str(e)}"))
            return None
            
        except Exception as e:
            # Unexpected errors
            self.stats['failed_extractions'] += 1
            self.failed_files.append((image_path, f"Unexpected error: {str(e)}"))
            return None
    
    def extract_batch(self, image_paths: List[str], progress_callback=None) -> Dict[str, Optional[Dict]]:
        """
        Extract metadata from multiple images with progress tracking
        
        Args:
            image_paths: List of image file paths
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary mapping file paths to metadata (or None if failed)
        """
        results = {}
        total_files = len(image_paths)
        
        for i, image_path in enumerate(image_paths):
            self.stats['total_processed'] += 1
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total_files, os.path.basename(image_path))
            
            # Extract metadata
            metadata = self.extract_single(image_path)
            results[image_path] = metadata
            
            # Memory management for large batches
            if i > 0 and i % 100 == 0:
                # Force garbage collection every 100 files
                import gc
                gc.collect()
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed extraction statistics"""
        success_rate = 0
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful_extractions'] / self.stats['total_processed']) * 100
            
        return {
            **self.stats,
            'success_rate_percent': round(success_rate, 2),
            'failed_files': self.failed_files
        }
    
    def reset_statistics(self):
        """Reset all statistics and failed files list"""
        self.stats = {key: 0 for key in self.stats}
        self.failed_files = []


class MetadataAnalyzer:
    """Analyzes extracted metadata to find key fields for sorting"""
    
    @staticmethod
    def extract_checkpoints(metadata: Dict[str, Any]) -> List[str]:
        """Extract all checkpoint/model names from metadata"""
        checkpoints = []
        if not metadata:
            return checkpoints
            
        for entry in metadata.values():
            inputs = entry.get('inputs', {})
            
            # Primary checkpoint field
            if 'ckpt_name' in inputs:
                checkpoints.append(inputs['ckpt_name'])
            
            # Alternative model fields
            for field in ['model_name', 'checkpoint', 'base_model']:
                if field in inputs:
                    checkpoints.append(inputs[field])
        
        return list(set(checkpoints))  # Remove duplicates
    
    @staticmethod
    def extract_loras(metadata: Dict[str, Any]) -> List[str]:
        """Extract all LoRA names from metadata"""
        loras = []
        if not metadata:
            return loras
            
        for entry in metadata.values():
            inputs = entry.get('inputs', {})
            
            # Standard LoRA field
            if 'lora_name' in inputs:
                loras.append(inputs['lora_name'])
        
        return list(set(loras))  # Remove duplicates
    
    @staticmethod
    def extract_primary_checkpoint(metadata: Dict[str, Any], image_filename: Optional[str] = None) -> Optional[str]:
        """
        Extract the primary/base checkpoint (not refiner) for sorting
        
        This is your #1 priority feature - base checkpoint sorting
        Now with filename fallback support for model name extraction
        """
        if not metadata:
            return None
        
        # First try to extract model from filename if available (ComfyUI naming pattern)
        filename_model = None
        if image_filename:
            filename_model = MetadataAnalyzer._extract_model_from_filename(image_filename)
        
        # Track checkpoints with priority order
        base_checkpoints = []
        refiner_checkpoints = []
        all_checkpoints = []

        for node_id, entry in metadata.items():
            if not isinstance(entry, dict):
                continue
                
            class_type = entry.get('class_type', '')
            inputs = entry.get('inputs', {})
            node_title = str(node_id).lower()

            # Skip non-checkpoint loading nodes
            if class_type not in ['CheckpointLoaderSimple', 'CheckpointLoader', 'UNETLoader']:
                continue

            # Get checkpoint name
            ckpt_name = None
            if 'ckpt_name' in inputs:
                ckpt_name = inputs['ckpt_name']
            elif 'unet_name' in inputs:
                ckpt_name = inputs['unet_name']
            
            if not ckpt_name:
                continue
                
            # Track all checkpoints
            all_checkpoints.append(ckpt_name)
            
            # Determine if this is explicitly a refiner
            # Be more strict about refiner detection
            is_explicit_refiner = (
                'refiner' in class_type.lower() or
                'refiner' in node_title or
                # Check if this node has explicit refiner-specific parameters
                ('start_at_step' in inputs and 'end_at_step' in inputs) or
                any(key in inputs for key in ['refiner_ckpt', 'refiner_model', 'ascore'])
            )
            
            if is_explicit_refiner:
                refiner_checkpoints.append(ckpt_name)
            else:
                # This is likely the base checkpoint
                base_checkpoints.append(ckpt_name)

        # Priority order:
        # 1. Model name from filename (highest priority)
        # 2. First base checkpoint found from workflow
        # 3. First checkpoint overall from workflow
        
        if filename_model:
            return filename_model
        elif base_checkpoints:
            return base_checkpoints[0]
        elif all_checkpoints:
            return all_checkpoints[0]
        
        return None
    
    @staticmethod
    def _extract_model_from_filename(filename: str) -> Optional[str]:
        """
        Extract model name from ComfyUI filename pattern
        
        ComfyUI filenames often contain the model name in patterns like:
        2025-10-15-182703_pieModels_elderberryPie_710452282418503.png
        """
        if not filename:
            return None
            
        # Remove file extension
        base_name = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
        
        # Split by underscores and look for model patterns
        parts = base_name.split('_')
        
        # Look for model name patterns (typically after timestamp)
        # Pattern: YYYY-MM-DD-HHMMSS_modelName_seed or similar
        if len(parts) >= 3:
            # Skip timestamp part (first part), look at subsequent parts
            for i in range(1, len(parts) - 1):  # Exclude last part (usually seed)
                part = parts[i]
                # Look for likely model names (skip common prefixes)
                if part and len(part) > 3 and part not in ['ComfyUI', 'output', 'temp']:
                    # If we find what looks like a model name, combine it with next part if it exists
                    if i + 1 < len(parts) - 1:  # Not the last part
                        next_part = parts[i + 1]
                        # Check if this looks like a model name pattern
                        if any(keyword in (part + next_part).lower() for keyword in ['model', 'mix', 'xl', 'pie', 'diffusion']):
                            return f"{part}_{next_part}"
                    return part
        
        return None
    
    @staticmethod
    def extract_sampling_params(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sampling parameters (CFG, steps, sampler, scheduler)"""
        params = {}
        if not metadata:
            return params
            
        for entry in metadata.values():
            class_type = entry.get('class_type', '')
            inputs = entry.get('inputs', {})
            
            if class_type in ['KSampler', 'KSamplerAdvanced']:
                params.update({
                    'steps': inputs.get('steps'),
                    'cfg': inputs.get('cfg'),
                    'sampler_name': inputs.get('sampler_name'),
                    'scheduler': inputs.get('scheduler'),
                    'denoise': inputs.get('denoise')
                })
                break  # Take first sampler found
        
        return {k: v for k, v in params.items() if v is not None}
    
    @staticmethod
    def extract_prompts(metadata: Dict[str, Any]) -> Dict[str, str]:
        """Extract positive and negative prompts"""
        prompts = {'positive': '', 'negative': ''}
        if not metadata:
            return prompts
            
        for entry in metadata.values():
            class_type = entry.get('class_type', '')
            inputs = entry.get('inputs', {})
            
            if class_type == 'CLIPTextEncode':
                text = inputs.get('text', '')
                if text and not prompts['positive']:
                    prompts['positive'] = text
                elif text and not prompts['negative']:
                    prompts['negative'] = text
        
        return prompts
    
    @staticmethod
    def search_metadata(metadata: Dict[str, Any], search_term: str) -> bool:
        """
        Search for any string in metadata (for your metadata search feature)
        
        Args:
            metadata: The metadata dictionary
            search_term: String to search for (case-insensitive)
            
        Returns:
            True if search term found anywhere in metadata
        """
        if not metadata or not search_term:
            return False
            
        search_term = search_term.lower()
        metadata_str = json.dumps(metadata).lower()
        
        return search_term in metadata_str


# Example usage and testing
class WorkflowTrace:
    """Link-aware extraction from ComfyUI workflow JSON.

    ComfyUI records linked node inputs as [node_id, slot] pairs, and modern
    workflows route prompts/settings through selector, pipe, and concat
    nodes. These helpers dereference links, trace conditioning back to the
    encode node that holds the text, and prefer the base sampling pass over
    refiner/detail passes. Shared by the metadata formatter and Civitai Prep.
    """

    @staticmethod
    def deref(metadata: Dict[str, Any], value: Any,
              key_hint: Optional[str] = None) -> Any:
        """Follow node links to the literal value (or None)."""
        depth = 0
        while isinstance(value, list) and len(value) == 2 and depth < 8:
            depth += 1
            node = metadata.get(str(value[0]))
            if not isinstance(node, dict):
                return None
            inputs = node.get('inputs', {})
            if not isinstance(inputs, dict):
                return None

            # String-concatenation nodes: reassemble the pieces
            if 'string_a' in inputs or 'string_b' in inputs:
                a = WorkflowTrace.deref(metadata, inputs.get('string_a'), 'text')
                b = WorkflowTrace.deref(metadata, inputs.get('string_b'), 'text')
                delim = inputs.get('delimiter')
                delim = delim if isinstance(delim, str) else ''
                parts = [str(p) for p in (a, b) if isinstance(p, (str, int, float))]
                return delim.join(parts) if parts else None

            carriers = ([key_hint] if key_hint else []) + [
                'text', 'value', 'string', 'sampler_name', 'scheduler',
                'seed', 'noise_seed', 'steps', 'cfg', 'int', 'float']
            for k in carriers:
                if k and k in inputs:
                    value = inputs[k]
                    break
            else:
                # Unique-scalar fallback, type-matched to what we're after
                want_str = key_hint in ('text', 'string')
                scalars = [v for v in inputs.values()
                           if isinstance(v, (str,) if want_str else (str, int, float))
                           and not isinstance(v, bool)
                           and (not want_str or v.strip())]
                if len(scalars) == 1:
                    value = scalars[0]
                else:
                    return None
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            if key_hint in ('text', 'string') and not isinstance(value, str):
                return None
            return value
        return None

    @classmethod
    def trace_text(cls, metadata: Dict[str, Any], link: Any,
                   role: str = '', depth: int = 0) -> Optional[Tuple[str, str]]:
        """Follow a conditioning link back to (prompt_text, encode_class).

        A node with a 'text' input is the encoder for its branch — its text
        (or nothing) is the answer. Pipe/bundle nodes with role-named inputs
        ('pos'/'neg') are followed exclusively so branches never bleed.
        """
        if not (isinstance(link, list) and len(link) == 2) or depth > 10:
            return None
        node = metadata.get(str(link[0]))
        if not isinstance(node, dict):
            return None
        inputs = node.get('inputs', {})
        if not isinstance(inputs, dict):
            return None

        if 'text' in inputs:
            t = cls.deref(metadata, inputs['text'], key_hint='text')
            if isinstance(t, str) and t.strip():
                return t, node.get('class_type', '')
            return None

        role_token = role[:3].lower() if role else ''
        role_keys = [k for k in inputs if role_token and role_token in k.lower()]
        if role_keys:
            for k in role_keys:
                found = cls.trace_text(metadata, inputs[k], role, depth + 1)
                if found:
                    return found
            return None

        for v in inputs.values():
            found = cls.trace_text(metadata, v, role, depth + 1)
            if found:
                return found
        return None

    @classmethod
    def _sampler_score(cls, metadata: Dict[str, Any], entry: Dict[str, Any],
                       pos_class: str = '') -> int:
        """Higher = more likely the base pass (vs refiner/detail pass)."""
        inputs = entry.get('inputs', {})
        score = 0
        denoise = cls.deref(metadata, inputs.get('denoise'), key_hint='denoise')
        if isinstance(denoise, (int, float)) and denoise < 1.0:
            score -= 1
        start_step = cls.deref(metadata, inputs.get('start_at_step'), key_hint='start_at_step')
        if isinstance(start_step, (int, float)) and start_step > 0:
            score -= 1
        if 'refiner' in pos_class.lower():
            score -= 2
        title = str(entry.get('_meta', {}).get('title', '')).lower()
        if 'refiner' in title:
            score -= 2
        return score

    @classmethod
    def extract_prompts(cls, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Positive/negative prompts traced from the base sampler's inputs."""
        prompts = {'positive': '', 'negative': ''}
        if not metadata:
            return prompts

        candidates = []
        for entry in metadata.values():
            if not isinstance(entry, dict):
                continue
            if entry.get('class_type', '') not in ('KSampler', 'KSamplerAdvanced'):
                continue
            inputs = entry.get('inputs', {})
            pos = cls.trace_text(metadata, inputs.get('positive'), role='positive')
            if pos is None:
                continue
            neg = cls.trace_text(metadata, inputs.get('negative'), role='negative')
            score = cls._sampler_score(metadata, entry, pos[1])
            candidates.append((score, pos[0], neg[0] if neg else ''))

        if candidates:
            candidates.sort(key=lambda c: c[0], reverse=True)
            _, prompts['positive'], prompts['negative'] = candidates[0]
        return prompts

    @classmethod
    def extract_sampling(cls, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Base-pass sampling params with all node links resolved to literals."""
        if not metadata:
            return {}

        candidates = []
        for entry in metadata.values():
            if not isinstance(entry, dict):
                continue
            if entry.get('class_type', '') not in ('KSampler', 'KSamplerAdvanced'):
                continue
            inputs = entry.get('inputs', {})
            params = {}
            for key, hint in (('steps', 'steps'), ('cfg', 'cfg'),
                              ('sampler_name', 'sampler_name'),
                              ('scheduler', 'scheduler'),
                              ('denoise', 'denoise')):
                v = cls.deref(metadata, inputs.get(key), key_hint=hint)
                if v is not None:
                    params[key] = v
            if not params:
                continue
            score = cls._sampler_score(metadata, entry)
            candidates.append((score, params))

        if not candidates:
            return {}
        candidates.sort(key=lambda c: c[0], reverse=True)
        return candidates[0][1]

    @staticmethod
    def parse_parameters_chunk(text: str) -> Dict[str, str]:
        """Parse an A1111-style 'parameters' text chunk into prompt parts.

        Nodes like ComfyUI-Image-Saver write the RUNTIME prompt here — the
        only place text from generator nodes (Florence2 captions, wildcards)
        ever lands, since workflow JSON stores only their inputs.
        """
        if not text or text.lstrip().startswith('{'):
            return {}
        lines = text.split('\n')
        neg_i = None
        settings_i = None
        for i, line in enumerate(lines):
            if neg_i is None and line.startswith('Negative prompt:'):
                neg_i = i
            if re.match(r'^Steps: \d', line):
                settings_i = i
        end = settings_i if settings_i is not None else len(lines)
        if neg_i is not None:
            positive = '\n'.join(lines[:neg_i]).strip()
            neg_lines = [lines[neg_i][len('Negative prompt:'):]] + lines[neg_i + 1:end]
            negative = '\n'.join(neg_lines).strip()
        else:
            positive = '\n'.join(lines[:end]).strip()
            negative = ''
        return {'positive': positive, 'negative': negative}

    @classmethod
    def extract_prompts_full(cls, metadata: Dict[str, Any],
                             image_path: Optional[str] = None) -> Dict[str, str]:
        """Best-available prompts: workflow tracing MERGED with the image's
        existing 'parameters' chunk.

        The chunk carries runtime-generated text (e.g. a Florence2 caption)
        the workflow JSON can't know; tracing carries the style/template text
        the chunk may lack. When both exist and differ, they are combined.
        """
        prompts = cls.extract_prompts(metadata or {})

        chunk: Dict[str, str] = {}
        if image_path:
            try:
                with Image.open(image_path) as im:
                    raw = im.info.get('parameters')
                if isinstance(raw, str):
                    chunk = cls.parse_parameters_chunk(raw)
            except Exception:
                chunk = {}

        def merge(traced: str, from_chunk: str) -> str:
            traced = (traced or '').strip()
            from_chunk = (from_chunk or '').strip()
            if not traced:
                return from_chunk
            if not from_chunk:
                return traced
            if traced.lower() in from_chunk.lower():
                return from_chunk
            if from_chunk.lower() in traced.lower():
                return traced
            return f"{traced}\n{from_chunk}"

        return {
            'positive': merge(prompts.get('positive', ''), chunk.get('positive', '')),
            'negative': chunk.get('negative', '') or prompts.get('negative', ''),
        }

    @classmethod
    def extract_seed(cls, metadata: Dict[str, Any]) -> Optional[int]:
        """Seed from the base sampler, following links to seed generators."""
        if not metadata:
            return None
        candidates = []
        for entry in metadata.values():
            if not isinstance(entry, dict):
                continue
            if entry.get('class_type', '') not in ('KSampler', 'KSamplerAdvanced'):
                continue
            inputs = entry.get('inputs', {})
            for key in ('seed', 'noise_seed'):
                v = cls.deref(metadata, inputs.get(key), key_hint=key)
                if isinstance(v, (int, float)):
                    candidates.append((cls._sampler_score(metadata, entry), int(v)))
                    break
        if candidates:
            candidates.sort(key=lambda c: c[0], reverse=True)
            return candidates[0][1]

        # Fallback: any node carrying a literal seed (seed generators,
        # image-saver nodes) when the sampler's seed link can't be resolved
        for entry in metadata.values():
            if not isinstance(entry, dict):
                continue
            inputs = entry.get('inputs', {})
            if not isinstance(inputs, dict):
                continue
            for key in ('seed', 'noise_seed'):
                v = inputs.get(key)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    return int(v)
        return None


if __name__ == "__main__":
    extractor = MetadataExtractor()
    analyzer = MetadataAnalyzer()
    
    # Test with a single file
    test_file = input("Enter path to test PNG file: ").strip().strip('"\'')
    
    if os.path.exists(test_file):
        print(f"🔍 Testing metadata extraction on: {os.path.basename(test_file)}")
        
        metadata = extractor.extract_single(test_file)
        
        if metadata:
            print("✅ Metadata extracted successfully!")
            
            # Analyze the metadata
            checkpoints = analyzer.extract_checkpoints(metadata)
            primary = analyzer.extract_primary_checkpoint(metadata)
            loras = analyzer.extract_loras(metadata)
            sampling = analyzer.extract_sampling_params(metadata)
            prompts = analyzer.extract_prompts(metadata)
            
            print(f"\n📋 Analysis Results:")
            print(f"   Primary checkpoint: {primary}")
            print(f"   All checkpoints: {checkpoints}")
            print(f"   LoRAs: {loras}")
            print(f"   Sampling: {sampling}")
            print(f"   Prompts: {prompts}")
            
        else:
            print("❌ No metadata found")
        
        # Show statistics
        stats = extractor.get_statistics()
        print(f"\n📊 Statistics: {stats}")
    else:
        print("❌ File not found")
