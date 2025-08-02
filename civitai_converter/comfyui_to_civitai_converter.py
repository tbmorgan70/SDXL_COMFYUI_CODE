#!/usr/bin/env python3
"""
ComfyUI to Civitai Metadata Converter
=====================================

This script converts ComfyUI output metadata to the format expected by Civitai.
It processes PNG files and rewrites their metadata to include SHA256 hashes 
of all resources used, making them compatible with Civitai's auto-detection system.

Usage:
    python comfyui_to_civitai_converter.py [options]

Requirements:
    pip install pillow
"""

import json
import re
import os
import hashlib
import argparse
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image
from PIL.PngImagePlugin import PngInfo


class ComfyUIToCivitaiConverter:
    def __init__(self, model_paths: Optional[Dict[str, str]] = None):
        """
        Initialize the converter with paths to your model directories.
        
        Args:
            model_paths: Dictionary mapping resource types to their directories
                        Example: {
                            'checkpoints': '/path/to/checkpoints',
                            'loras': '/path/to/loras', 
                            'vaes': '/path/to/vaes',
                            'embeddings': '/path/to/embeddings'
                        }
        """
        self.model_paths = model_paths or {}
        self.resource_cache = {}
        self.load_resources()
    
    def load_resources(self):
        """Load and hash all resources from the specified directories."""
        print("Loading and hashing resources...")
        
        # Default paths if not provided
        default_paths = {
            'checkpoints': ['models/checkpoints', 'models/Stable-diffusion'],
            'loras': ['models/loras', 'models/Lora'],
            'vaes': ['models/vae', 'models/VAE'],
            'embeddings': ['models/embeddings', 'embeddings'],
            'controlnet': ['models/controlnet', 'models/ControlNet'],
            'upscalers': ['models/upscalers', 'models/ESRGAN']
        }
        
        for resource_type, paths in default_paths.items():
            if resource_type in self.model_paths:
                paths = [self.model_paths[resource_type]]
            
            for path in paths:
                if os.path.exists(path):
                    self._scan_directory(resource_type, path)
                    break
    
    def _scan_directory(self, resource_type: str, directory: str):
        """Scan a directory for model files and calculate their hashes."""
        extensions = {
            'checkpoints': ['.safetensors', '.ckpt'],
            'loras': ['.safetensors', '.ckpt', '.pt'],
            'vaes': ['.safetensors', '.ckpt', '.pt'],
            'embeddings': ['.safetensors', '.pt', '.bin'],
            'controlnet': ['.safetensors', '.ckpt'],
            'upscalers': ['.pth', '.pt']
        }
        
        file_extensions = extensions.get(resource_type, ['.safetensors', '.ckpt', '.pt'])
        
        for ext in file_extensions:
            pattern = os.path.join(directory, f"**/*{ext}")
            for filepath in glob.glob(pattern, recursive=True):
                try:
                    file_hash = self._calculate_sha256(filepath)
                    filename = os.path.basename(filepath)
                    name = os.path.splitext(filename)[0]
                    
                    self.resource_cache[name.lower()] = {
                        'name': name,
                        'type': resource_type,
                        'hash': file_hash,
                        'path': filepath
                    }
                    print(f"Loaded {resource_type}: {name} [{file_hash[:10]}]")
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    def _calculate_sha256(self, filepath: str) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {filepath}: {e}")
            return ""
    
    def parse_comfyui_metadata(self, image_path: str) -> Tuple[Dict, str]:
        """Parse ComfyUI metadata from PNG file."""
        try:
            with Image.open(image_path) as img:
                # ComfyUI stores metadata in different ways
                metadata = {}
                original_parameters = ""
                
                # Check for workflow in metadata
                text_data = getattr(img, 'text', {})
                if 'workflow' in text_data:
                    workflow_data = json.loads(text_data['workflow'])
                    metadata['workflow'] = workflow_data
                
                # Check for prompt in metadata  
                if 'prompt' in text_data:
                    prompt_data = json.loads(text_data['prompt'])
                    metadata['prompt'] = prompt_data
                
                # Check for parameters (if exists)
                if 'parameters' in text_data:
                    original_parameters = text_data['parameters']
                
                return metadata, original_parameters
                
        except Exception as e:
            print(f"Error reading metadata from {image_path}: {e}")
            return {}, ""
    
    def extract_resources_from_comfyui(self, metadata: Dict) -> Dict[str, str]:
        """Extract resource information from ComfyUI metadata."""
        resource_hashes = {}
        
        # Process workflow data
        if 'workflow' in metadata:
            workflow = metadata['workflow']
            for node in workflow.get('nodes', []):
                self._process_workflow_node(node, resource_hashes)
        
        # Process prompt data
        if 'prompt' in metadata:
            prompt = metadata['prompt']
            for node_id, node_data in prompt.items():
                self._process_prompt_node(node_data, resource_hashes)
        
        return resource_hashes
    
    def _process_workflow_node(self, node: Dict, resource_hashes: Dict[str, str]):
        """Process a workflow node to extract resource information."""
        node_type = node.get('type', '')
        
        # Handle different node types
        if node_type in ['CheckpointLoaderSimple', 'CheckpointLoader']:
            checkpoint_name = self._extract_value_from_node(node, 'ckpt_name')
            if checkpoint_name:
                self._add_resource_hash('model', checkpoint_name, resource_hashes)
        
        elif node_type in ['LoraLoader', 'LoraLoaderModelOnly']:
            lora_name = self._extract_value_from_node(node, 'lora_name')
            if lora_name:
                self._add_resource_hash('lora', lora_name, resource_hashes)
        
        elif node_type in ['VAELoader']:
            vae_name = self._extract_value_from_node(node, 'vae_name')
            if vae_name:
                self._add_resource_hash('vae', vae_name, resource_hashes)
    
    def _process_prompt_node(self, node_data: Dict, resource_hashes: Dict[str, str]):
        """Process a prompt node to extract resource information."""
        class_type = node_data.get('class_type', '')
        inputs = node_data.get('inputs', {})
        
        # Handle different node types
        if class_type in ['CheckpointLoaderSimple', 'CheckpointLoader']:
            checkpoint_name = inputs.get('ckpt_name')
            if checkpoint_name:
                self._add_resource_hash('model', checkpoint_name, resource_hashes)
        
        elif class_type in ['LoraLoader', 'LoraLoaderModelOnly']:
            lora_name = inputs.get('lora_name')
            if lora_name:
                self._add_resource_hash('lora', lora_name, resource_hashes)
        
        elif class_type in ['VAELoader']:
            vae_name = inputs.get('vae_name')
            if vae_name:
                self._add_resource_hash('vae', vae_name, resource_hashes)
    
    def _extract_value_from_node(self, node: Dict, key: str) -> Optional[str]:
        """Extract a value from a workflow node."""
        widgets_values = node.get('widgets_values', [])
        if widgets_values:
            # This is a simplified extraction - you may need to adjust based on your workflow
            return widgets_values[0] if widgets_values else None
        return None
    
    def _add_resource_hash(self, resource_type: str, resource_name: str, resource_hashes: Dict[str, str]):
        """Add a resource hash to the collection."""
        # Remove file extension if present
        clean_name = os.path.splitext(resource_name)[0].lower()
        
        # Find matching resource
        if clean_name in self.resource_cache:
            resource = self.resource_cache[clean_name]
            short_hash = resource['hash'][:10]  # Civitai uses 10-character short hashes
            
            if resource_type == 'model':
                resource_hashes['model'] = short_hash
            elif resource_type == 'lora':
                resource_hashes[f'lora:{resource["name"]}'] = short_hash
            elif resource_type == 'vae':
                resource_hashes['vae'] = short_hash
            else:
                resource_hashes[f'{resource_type}:{resource["name"]}'] = short_hash
            
            print(f"Added {resource_type}: {resource['name']} [{short_hash}]")
        else:
            print(f"Warning: Could not find hash for {resource_type}: {resource_name}")
    
    def create_civitai_metadata(self, original_params: str, resource_hashes: Dict[str, str]) -> str:
        """Create Civitai-compatible metadata string."""
        if not resource_hashes:
            return original_params
        
        # Add hashes to parameters
        hashes_json = json.dumps(resource_hashes)
        
        if original_params:
            return f"{original_params}, Hashes: {hashes_json}"
        else:
            return f"Hashes: {hashes_json}"
    
    def convert_image(self, image_path: str, output_path: Optional[str] = None) -> bool:
        """Convert a single image to Civitai-compatible format."""
        if output_path is None:
            # Create backup and overwrite original
            backup_path = image_path + '.backup'
            if not os.path.exists(backup_path):
                os.rename(image_path, backup_path)
                image_path = backup_path
            output_path = image_path[:-7]  # Remove '.backup'
        
        try:
            # Parse ComfyUI metadata
            metadata, original_params = self.parse_comfyui_metadata(image_path)
            
            # Extract resources
            resource_hashes = self.extract_resources_from_comfyui(metadata)
            
            if not resource_hashes:
                print(f"No resources found in {image_path}")
                return False
            
            # Create new metadata
            new_parameters = self.create_civitai_metadata(original_params, resource_hashes)
            
            # Save image with new metadata
            with Image.open(image_path) as img:
                # Create new PNG info
                pnginfo = PngInfo()
                
                # Copy existing metadata
                text_data = getattr(img, 'text', {})
                for key, value in text_data.items():
                    if key != 'parameters':  # We'll replace this
                        pnginfo.add_text(key, value)
                
                # Add new parameters
                pnginfo.add_text('parameters', new_parameters)
                
                # Save image
                img.save(output_path, pnginfo=pnginfo)
            
            print(f"✓ Converted: {os.path.basename(output_path)}")
            print(f"  Added hashes: {list(resource_hashes.keys())}")
            return True
            
        except Exception as e:
            print(f"Error converting {image_path}: {e}")
            return False
    
    def convert_directory(self, input_dir: str, output_dir: Optional[str] = None, pattern: str = "*.png"):
        """Convert all PNG files in a directory."""
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        input_path = Path(input_dir)
        files = list(input_path.glob(pattern))
        
        if not files:
            print(f"No files found matching {pattern} in {input_dir}")
            return
        
        print(f"Found {len(files)} files to process")
        
        successful = 0
        for file_path in files:
            if output_dir:
                output_path = os.path.join(output_dir, file_path.name)
            else:
                output_path = None
            
            if self.convert_image(str(file_path), output_path):
                successful += 1
        
        print(f"\nCompleted: {successful}/{len(files)} files converted successfully")


def main():
    parser = argparse.ArgumentParser(description='Convert ComfyUI metadata to Civitai format')
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('--checkpoints', help='Path to checkpoints directory')
    parser.add_argument('--loras', help='Path to LoRAs directory')
    parser.add_argument('--vaes', help='Path to VAEs directory')
    parser.add_argument('--embeddings', help='Path to embeddings directory')
    parser.add_argument('--pattern', default='*.png', help='File pattern to match (default: *.png)')
    
    args = parser.parse_args()
    
    # Build model paths
    model_paths = {}
    if args.checkpoints:
        model_paths['checkpoints'] = args.checkpoints
    if args.loras:
        model_paths['loras'] = args.loras
    if args.vaes:
        model_paths['vaes'] = args.vaes
    if args.embeddings:
        model_paths['embeddings'] = args.embeddings
    
    # Create converter
    converter = ComfyUIToCivitaiConverter(model_paths)
    
    # Process input
    if os.path.isfile(args.input):
        # Single file
        converter.convert_image(args.input, args.output)
    elif os.path.isdir(args.input):
        # Directory
        converter.convert_directory(args.input, args.output, args.pattern)
    else:
        print(f"Error: {args.input} is not a valid file or directory")


if __name__ == '__main__':
    main()
