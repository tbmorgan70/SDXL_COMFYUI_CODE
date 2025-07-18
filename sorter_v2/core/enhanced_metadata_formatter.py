"""
Enhanced Metadata Formatter for Sorter 2.0

Creates comprehensive, beautifully formatted metadata text files
with all ComfyUI workflow information in a readable format.
"""

import json
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

class EnhancedMetadataFormatter:
    """Creates comprehensive, formatted metadata text files"""
    
    def __init__(self):
        self.separator = "=" * 50
        
    def format_metadata_to_text(self, metadata: Dict[str, Any], image_path: str) -> str:
        """
        Convert metadata to comprehensive formatted text
        
        Args:
            metadata: Full ComfyUI metadata dictionary
            image_path: Path to the image file
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Header
        lines.append(self._format_header(image_path))
        lines.append("")
        
        # Core Models Section
        lines.extend(self._format_models_section(metadata))
        lines.append("")
        
        # LoRAs Section
        lines.extend(self._format_loras_section(metadata))
        lines.append("")
        
        # VAE Section
        lines.extend(self._format_vae_section(metadata))
        lines.append("")
        
        # Prompts Section
        lines.extend(self._format_prompts_section(metadata))
        lines.append("")
        
        # Sampling Parameters
        lines.extend(self._format_sampling_section(metadata))
        lines.append("")
        
        # Refiner Parameters (if present)
        refiner_section = self._format_refiner_section(metadata)
        if refiner_section:
            lines.extend(refiner_section)
            lines.append("")
        
        # Image Parameters
        lines.extend(self._format_image_parameters(metadata))
        lines.append("")
        
        # Upscaling Section
        upscale_section = self._format_upscaling_section(metadata)
        if upscale_section:
            lines.extend(upscale_section)
            lines.append("")
        
        # Post-Processing Section
        postprocess_section = self._format_postprocessing_section(metadata)
        if postprocess_section:
            lines.extend(postprocess_section)
            lines.append("")
        
        # Advanced Settings
        lines.extend(self._format_advanced_section(metadata))
        lines.append("")
        
        # Technical Details
        lines.extend(self._format_technical_section(metadata))
        
        return "\n".join(lines)
    
    def _format_header(self, image_path: str) -> str:
        """Format file header with generation info"""
        filename = os.path.basename(image_path)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""=== COMFYUI METADATA REPORT ===
File: {filename}
Generated: {timestamp}
{self.separator}"""
    
    def _format_models_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format models and checkpoints section"""
        lines = ["=== MODELS & CHECKPOINTS ==="]
        
        base_models = []
        refiner_models = []
        other_models = []
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            title = node_data.get('_meta', {}).get('title', '')
            
            if 'ckpt_name' in inputs:
                model_name = inputs['ckpt_name']
                if 'refiner' in title.lower() or 'refiner' in class_type.lower():
                    refiner_models.append(f"Refiner Model: {model_name}")
                else:
                    base_models.append(f"Base Model: {model_name}")
            
            # Detect other model types
            for model_field in ['model_name', 'checkpoint']:
                if model_field in inputs:
                    model_value = inputs[model_field]
                    if model_value not in [m.split(': ', 1)[1] for m in base_models + refiner_models]:
                        other_models.append(f"Additional Model: {model_value}")
        
        # Add models to output
        lines.extend(base_models)
        lines.extend(refiner_models)
        lines.extend(other_models)
        
        if not (base_models or refiner_models or other_models):
            lines.append("No models detected")
        
        return lines
    
    def _format_loras_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format LoRAs section with strengths"""
        lines = ["=== LORAS ==="]
        
        loras = []
        lora_count = 1
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            if class_type == 'LoraLoader' and 'lora_name' in inputs:
                lora_name = inputs['lora_name']
                model_strength = inputs.get('strength_model', 1.0)
                clip_strength = inputs.get('strength_clip', 1.0)
                
                lora_info = f"LoRA {lora_count}: {lora_name}"
                if model_strength != 1.0 or clip_strength != 1.0:
                    lora_info += f" (Model: {model_strength}, CLIP: {clip_strength})"
                
                loras.append(lora_info)
                lora_count += 1
        
        if loras:
            lines.extend(loras)
        else:
            lines.append("No LoRAs used")
        
        return lines
    
    def _format_vae_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format VAE section"""
        lines = ["=== VAE ==="]
        
        vae_models = []
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            if class_type == 'VAELoader' and 'vae_name' in inputs:
                vae_models.append(f"VAE Model: {inputs['vae_name']}")
        
        if vae_models:
            lines.extend(vae_models)
        else:
            lines.append("Default VAE (from checkpoint)")
        
        return lines
    
    def _format_prompts_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format prompts section"""
        lines = ["=== PROMPTS ==="]
        
        positive_prompts = []
        negative_prompts = []
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            title = node_data.get('_meta', {}).get('title', '').lower()
            
            if class_type in ['CLIPTextEncode', 'CLIPTextEncodeSDXL', 'CLIPTextEncodeSDXLRefiner'] and 'text' in inputs:
                # Handle both string and list formats for prompt text
                text_data = inputs['text']
                if isinstance(text_data, list):
                    prompt_text = ' '.join(str(item).strip() for item in text_data if item).strip()
                else:
                    prompt_text = str(text_data).strip()
                
                if not prompt_text:
                    continue
                    
                # Determine if positive or negative
                if 'negative' in title or 'neg' in title:
                    negative_prompts.append(prompt_text)
                else:
                    positive_prompts.append(prompt_text)
        
        # Add positive prompts
        if positive_prompts:
            lines.append("POSITIVE:")
            for i, prompt in enumerate(positive_prompts, 1):
                if len(positive_prompts) > 1:
                    lines.append(f"  {i}. {prompt}")
                else:
                    lines.append(f"  {prompt}")
        else:
            lines.append("POSITIVE: None")
        
        lines.append("")
        
        # Add negative prompts
        if negative_prompts:
            lines.append("NEGATIVE:")
            for i, prompt in enumerate(negative_prompts, 1):
                if len(negative_prompts) > 1:
                    lines.append(f"  {i}. {prompt}")
                else:
                    lines.append(f"  {prompt}")
        else:
            lines.append("NEGATIVE: None")
        
        return lines
    
    def _format_sampling_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format sampling parameters section"""
        lines = ["=== SAMPLING PARAMETERS ==="]
        
        sampling_params = {}
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            title = node_data.get('_meta', {}).get('title', '').lower()
            
            if 'sampler' in class_type.lower() and 'refiner' not in title:
                # Primary sampler (not refiner)
                if 'steps' in inputs:
                    sampling_params['Steps'] = inputs['steps']
                if 'cfg' in inputs:
                    sampling_params['CFG Scale'] = inputs['cfg']
                if 'sampler_name' in inputs:
                    sampling_params['Sampler'] = inputs['sampler_name']
                if 'scheduler' in inputs:
                    sampling_params['Scheduler'] = inputs['scheduler']
                if 'denoise' in inputs:
                    sampling_params['Denoise'] = inputs['denoise']
                if 'noise_seed' in inputs:
                    sampling_params['Seed'] = inputs['noise_seed']
        
        # Add parameters to output
        for param, value in sampling_params.items():
            lines.append(f"{param}: {value}")
        
        if not sampling_params:
            lines.append("No sampling parameters detected")
        
        return lines
    
    def _format_refiner_section(self, metadata: Dict[str, Any]) -> Optional[List[str]]:
        """Format refiner parameters if present"""
        lines = ["=== REFINER PARAMETERS ==="]
        
        refiner_params = {}
        has_refiner = False
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            title = node_data.get('_meta', {}).get('title', '').lower()
            
            if 'refiner' in title or ('sampler' in class_type.lower() and 'refiner' in title):
                has_refiner = True
                if 'steps' in inputs:
                    refiner_params['Refiner Steps'] = inputs['steps']
                if 'cfg' in inputs:
                    refiner_params['Refiner CFG'] = inputs['cfg']
                if 'start_at_step' in inputs:
                    refiner_params['Start at Step'] = inputs['start_at_step']
                if 'end_at_step' in inputs:
                    refiner_params['End at Step'] = inputs['end_at_step']
                if 'denoise' in inputs:
                    refiner_params['Refiner Denoise'] = inputs['denoise']
        
        if not has_refiner:
            return None
        
        # Add parameters to output
        for param, value in refiner_params.items():
            lines.append(f"{param}: {value}")
        
        if not refiner_params:
            lines.append("Refiner enabled but no parameters detected")
        
        return lines
    
    def _format_image_parameters(self, metadata: Dict[str, Any]) -> List[str]:
        """Format image generation parameters"""
        lines = ["=== IMAGE PARAMETERS ==="]
        
        width = None
        height = None
        batch_size = None
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            # Look for latent size parameters
            if 'EmptyLatent' in class_type or 'LatentSize' in class_type:
                if 'width' in inputs:
                    width = inputs['width']
                if 'height' in inputs:
                    height = inputs['height']
                if 'batch_size' in inputs:
                    batch_size = inputs['batch_size']
        
        if width and height:
            lines.append(f"Dimensions: {width} x {height}")
            aspect_ratio = round(width / height, 2)
            lines.append(f"Aspect Ratio: {aspect_ratio}")
        
        if batch_size and batch_size > 1:
            lines.append(f"Batch Size: {batch_size}")
        
        if not (width or height):
            lines.append("No image parameters detected")
        
        return lines
    
    def _format_upscaling_section(self, metadata: Dict[str, Any]) -> Optional[List[str]]:
        """Format upscaling parameters if present"""
        lines = ["=== UPSCALING ==="]
        
        upscale_info = {}
        has_upscaling = False
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            if 'Upscale' in class_type:
                has_upscaling = True
                
                if class_type == 'ImageUpscaleWithModel':
                    upscale_info['Method'] = 'Model-based Upscaling'
                elif class_type == 'ImageScaleBy':
                    upscale_info['Method'] = 'Scale by Factor'
                    if 'scale_by' in inputs:
                        upscale_info['Scale Factor'] = inputs['scale_by']
                elif class_type == 'LatentUpscaleBy':
                    upscale_info['Method'] = 'Latent Upscaling'
                    if 'scale_by' in inputs:
                        upscale_info['Scale Factor'] = inputs['scale_by']
                
                if 'upscale_method' in inputs:
                    upscale_info['Upscale Method'] = inputs['upscale_method']
            
            # Look for upscale model loaders
            if class_type == 'UpscaleModelLoader':
                if 'model_name' in inputs:
                    upscale_info['Upscale Model'] = inputs['model_name']
        
        if not has_upscaling:
            return None
        
        # Add parameters to output
        for param, value in upscale_info.items():
            lines.append(f"{param}: {value}")
        
        if not upscale_info:
            lines.append("Upscaling enabled but no parameters detected")
        
        return lines
    
    def _format_postprocessing_section(self, metadata: Dict[str, Any]) -> Optional[List[str]]:
        """Format post-processing effects if present"""
        lines = ["=== POST-PROCESSING ==="]
        
        postprocess_effects = []
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            title = node_data.get('_meta', {}).get('title', '')
            
            # Face detailing
            if 'FaceDetailer' in class_type:
                postprocess_effects.append("Face Enhancement: Enabled")
            
            # Other common post-processing
            if 'ColorCorrect' in class_type:
                postprocess_effects.append("Color Correction: Enabled")
            
            if 'Sharpen' in class_type:
                postprocess_effects.append("Sharpening: Enabled")
            
            if 'Blur' in class_type:
                postprocess_effects.append("Blur Effect: Enabled")
        
        if not postprocess_effects:
            return None
        
        lines.extend(postprocess_effects)
        return lines
    
    def _format_advanced_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format advanced/technical settings"""
        lines = ["=== ADVANCED SETTINGS ==="]
        
        advanced_settings = []
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            # CLIP settings
            if 'CLIPSetLastLayer' in class_type:
                if 'stop_at_clip_layer' in inputs:
                    advanced_settings.append(f"CLIP Skip: {inputs['stop_at_clip_layer']}")
            
            # Memory optimizations
            if 'tiled_encode' in inputs and inputs['tiled_encode']:
                advanced_settings.append("Tiled Encoding: Enabled")
            
            if 'tiled_decode' in inputs and inputs['tiled_decode']:
                advanced_settings.append("Tiled Decoding: Enabled")
        
        if advanced_settings:
            lines.extend(advanced_settings)
        else:
            lines.append("Default settings used")
        
        return lines
    
    def _format_technical_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format technical workflow information"""
        lines = ["=== TECHNICAL INFO ==="]
        
        total_nodes = len(metadata)
        lines.append(f"Workflow Nodes: {total_nodes}")
        
        # Count node types
        node_types = {}
        for node_data in metadata.values():
            if isinstance(node_data, dict):
                class_type = node_data.get('class_type', 'Unknown')
                node_types[class_type] = node_types.get(class_type, 0) + 1
        
        lines.append(f"Node Types: {len(node_types)}")
        
        # Show most common node types
        if node_types:
            sorted_types = sorted(node_types.items(), key=lambda x: x[1], reverse=True)
            lines.append("Common Nodes:")
            for node_type, count in sorted_types[:5]:  # Top 5
                lines.append(f"  {node_type}: {count}")
        
        return lines
