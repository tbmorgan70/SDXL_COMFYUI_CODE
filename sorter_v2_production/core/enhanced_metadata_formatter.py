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
        Convert metadata to comprehensive formatted text (matching original working format)
        
        Args:
            metadata: Full ComfyUI metadata dictionary
            image_path: Path to the image file
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Models Section
        lines.extend(self._format_models_section(metadata))
        lines.append("")
        
        # LoRAs Section
        lines.extend(self._format_loras_section(metadata))
        lines.append("")
        
        # Positive Prompt Section
        lines.extend(self._format_positive_prompt_section(metadata))
        lines.append("")
        
        # Negative Prompt Section
        lines.extend(self._format_negative_prompt_section(metadata))
        lines.append("")
        lines.append("")
        lines.append("")
        
        # Sampling Parameters
        lines.extend(self._format_sampling_section(metadata))
        lines.append("")
        
        # Image Parameters
        lines.extend(self._format_image_parameters(metadata))
        lines.append("")
        
        # Upscaling Section
        upscale_section = self._format_upscaling_section(metadata)
        if upscale_section:
            lines.extend(upscale_section)
        
        return "\n".join(lines)
    
    def get_base_model(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract base model name for grouping (ignoring refiner models)"""
        # Use the same method as MetadataAnalyzer for consistency
        from .metadata_engine import MetadataAnalyzer
        return MetadataAnalyzer.extract_primary_checkpoint(metadata)
    
    def get_lora_stack_signature(self, metadata: Dict[str, Any]) -> str:
        """Create a signature string representing the LoRA stack for grouping (improved version)"""
        loras = []
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            if class_type == 'LoraLoader' and 'lora_name' in inputs:
                lora_name = inputs['lora_name']
                # Use just the base name for cleaner grouping
                loras.append(lora_name)
        
        # Sort to ensure consistent signatures regardless of order in metadata
        loras = sorted(set(loras))
        return ",".join(loras) if loras else ""
    
    def get_grouping_signature(self, metadata: Dict[str, Any]) -> str:
        """Create a complete grouping signature matching the older working version"""
        base_model = self.get_base_model(metadata)
        loras = []
        
        # Extract all LoRAs
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            if class_type == 'LoraLoader' and 'lora_name' in inputs:
                loras.append(inputs['lora_name'])
        
        # Remove duplicates and sort
        loras = sorted(set(loras))
        
        # Create signature like: "base_model | lora1,lora2,lora3" 
        base_part = base_model or 'None'
        lora_part = ','.join(loras) if loras else ''
        
        if lora_part:
            return f"{base_part} | {lora_part}"
        else:
            return base_part
    
    def _format_header(self, image_path: str) -> str:
        """Format file header with generation info"""
        filename = os.path.basename(image_path)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""=== COMFYUI METADATA REPORT ===
File: {filename}
Generated: {timestamp}
{self.separator}"""
    
    def _format_models_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format models section to match original working format"""
        lines = ["=== MODELS ==="]
        
        # Use the same extraction method as MetadataAnalyzer for consistency
        from .metadata_engine import MetadataAnalyzer
        base_model = MetadataAnalyzer.extract_primary_checkpoint(metadata)
        vae = None
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            # Find VAE
            if class_type == 'VAELoader' and 'vae_name' in inputs:
                vae = inputs['vae_name']
        
        if base_model:
            # Extract just the filename from the path
            base_model_name = base_model.split('\\')[-1] if '\\' in base_model else base_model.split('/')[-1]
            lines.append(f"Base Model: {base_model_name}")
        
        if vae:
            # Extract just the filename from the path
            vae_name = vae.split('\\')[-1] if '\\' in vae else vae.split('/')[-1]
            lines.append(f"VAE: {vae_name}")
        
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
                # Extract just the filename from the path
                lora_filename = lora_name.split('\\')[-1] if '\\' in lora_name else lora_name.split('/')[-1]
                model_strength = inputs.get('strength_model', 1.0)
                clip_strength = inputs.get('strength_clip', 1.0)
                
                lora_info = f"LoRA {lora_count}: {lora_filename}"
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
    
    def _format_positive_prompt_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format positive prompt section with support for node references and base model priority"""
        lines = ["=== POSITIVE PROMPT ==="]
        
        positive_prompt = None
        base_model_prompt = None
        refiner_prompt = None
        
        # First pass: categorize prompts by base vs refiner
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            title = node_data.get('_meta', {}).get('title', '').lower()
            
            if class_type in ['CLIPTextEncode', 'CLIPTextEncodeSDXL', 'CLIPTextEncodeSDXLRefiner'] and 'text' in inputs:
                # Skip negative prompts
                if 'negative' in title or 'neg' in title:
                    continue
                
                # Determine if this is a refiner node
                is_refiner = (
                    'refiner' in class_type.lower() or 
                    'refiner' in title or
                    'ascore' in inputs or  # Common refiner parameter
                    'width' in inputs  # SDXL refiner often has width/height
                )
                
                # Extract text (direct or via node reference)
                text_data = inputs['text']
                extracted_text = None
                
                if isinstance(text_data, str) and text_data.strip():
                    extracted_text = text_data.strip()
                elif isinstance(text_data, list) and len(text_data) >= 1:
                    ref_node_id = text_data[0]
                    extracted_text = self._resolve_text_node_reference(metadata, ref_node_id)
                
                if extracted_text:
                    if is_refiner:
                        refiner_prompt = extracted_text
                    else:
                        base_model_prompt = extracted_text
        
        # Prioritize base model prompt over refiner prompt
        positive_prompt = base_model_prompt or refiner_prompt
        
        if positive_prompt:
            lines.append(positive_prompt)
        
        return lines
    
    def _resolve_text_node_reference(self, metadata: Dict[str, Any], node_id: str) -> Optional[str]:
        """Resolve a text node reference to get the actual text content"""
        if node_id not in metadata:
            return None
        
        node_data = metadata[node_id]
        if not isinstance(node_data, dict):
            return None
        
        class_type = node_data.get('class_type', '')
        inputs = node_data.get('inputs', {})
        
        # String Literal nodes (common in ComfyUI workflows) - CRITICAL FIX
        if 'String Literal' in class_type:
            if 'string' in inputs:
                return str(inputs['string']).strip()
        
        # ShowText nodes store the actual text in text_0 field
        elif 'ShowText' in class_type:
            if 'text_0' in inputs:
                return str(inputs['text_0']).strip()
            elif 'text' in inputs:
                # If text is another reference, resolve it recursively (with depth limit)
                text_data = inputs['text']
                if isinstance(text_data, list) and len(text_data) >= 1:
                    return self._resolve_text_node_reference(metadata, text_data[0])
                elif isinstance(text_data, str):
                    return text_data.strip()
        
        # Text Load Line From File nodes
        elif 'Text Load Line From File' in class_type:
            # These nodes don't store the actual loaded text in metadata,
            # they just have the file path and index
            return None
        
        # Other text nodes
        elif 'text' in inputs:
            text_data = inputs['text']
            if isinstance(text_data, str):
                return text_data.strip()
            elif isinstance(text_data, list):
                return ' '.join(str(item).strip() for item in text_data if item).strip()
        
        return None
    
    def _format_negative_prompt_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format negative prompt section"""
        lines = ["=== NEGATIVE PROMPT ==="]
        
        negative_prompt = None
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            title = node_data.get('_meta', {}).get('title', '').lower()
            
            if class_type in ['CLIPTextEncode', 'CLIPTextEncodeSDXL', 'CLIPTextEncodeSDXLRefiner'] and 'text' in inputs:
                # Only negative prompts
                if 'negative' in title or 'neg' in title:
                    # Extract text (direct or via node reference)
                    text_data = inputs['text']
                    extracted_text = None
                    
                    if isinstance(text_data, str) and text_data.strip():
                        extracted_text = text_data.strip()
                    elif isinstance(text_data, list) and len(text_data) >= 1:
                        ref_node_id = text_data[0]
                        extracted_text = self._resolve_text_node_reference(metadata, ref_node_id)
                    
                    if extracted_text:
                        negative_prompt = extracted_text
                        break
        
        if negative_prompt:
            lines.append(negative_prompt)
        
        return lines
    
    def _format_sampling_section(self, metadata: Dict[str, Any]) -> List[str]:
        """Format sampling parameters section to match original format (prioritize base KSampler over refiner)"""
        lines = ["=== SAMPLING PARAMETERS ==="]
        
        base_steps = None
        base_cfg = None
        base_sampler_name = None
        base_scheduler = None
        
        refiner_steps = None
        refiner_cfg = None
        refiner_sampler_name = None
        refiner_scheduler = None
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            title = node_data.get('_meta', {}).get('title', '').lower()
            
            # Look for KSampler nodes (focus on actual sampler data)
            if 'sampler' in class_type.lower():
                # Simplified refiner detection based on debug findings:
                # If start_at_step > 0, it's a refiner sampler
                is_refiner = False
                
                if 'refiner' in title:
                    is_refiner = True
                elif 'start_at_step' in inputs and inputs.get('start_at_step', 0) > 0:
                    is_refiner = True
                
                if is_refiner:
                    # This is a refiner sampler
                    if 'steps' in inputs:
                        refiner_steps = inputs['steps']
                    if 'cfg' in inputs:
                        refiner_cfg = inputs['cfg']
                    if 'sampler_name' in inputs:
                        refiner_sampler_name = inputs['sampler_name']
                    if 'scheduler' in inputs:
                        refiner_scheduler = inputs['scheduler']
                else:
                    # This is a base sampler - prioritize this for steps
                    if 'steps' in inputs:
                        base_steps = inputs['steps']
                    if 'cfg' in inputs:
                        base_cfg = inputs['cfg']
                    if 'sampler_name' in inputs:
                        base_sampler_name = inputs['sampler_name']
                    if 'scheduler' in inputs:
                        base_scheduler = inputs['scheduler']
        
        # Use base sampler parameters, fall back to refiner if no base found
        steps = base_steps if base_steps is not None else refiner_steps
        cfg = base_cfg if base_cfg is not None else refiner_cfg
        sampler_name = base_sampler_name if base_sampler_name else refiner_sampler_name
        scheduler = base_scheduler if base_scheduler else refiner_scheduler
        
        # Add parameters in specific order
        if steps is not None:
            lines.append(f"Steps: {steps}")
        if cfg is not None:
            lines.append(f"Cfg: {cfg}")
        if sampler_name:
            lines.append(f"Sampler Name: {sampler_name}")
        if scheduler:
            lines.append(f"Scheduler: {scheduler}")
        
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
        """Format image generation parameters to match original format"""
        lines = ["=== IMAGE PARAMETERS ==="]
        
        width = None
        height = None
        
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            # Look for SDXL Empty Latent Size Picker (most common)
            if 'SDXLEmptyLatentSizePicker' in class_type:
                resolution = inputs.get('resolution', '')
                if 'x' in resolution:
                    # Parse resolution like "896x1152 (0.78)"
                    try:
                        size_part = resolution.split(' ')[0]  # Get "896x1152"
                        width, height = map(int, size_part.split('x'))
                        break
                    except (ValueError, IndexError):
                        pass
            
            # Fallback: Look for standard latent size parameters
            elif 'EmptyLatent' in class_type or 'LatentSize' in class_type:
                if 'width' in inputs:
                    width = inputs['width']
                if 'height' in inputs:
                    height = inputs['height']
            
            # Also check SDXL refiner encode nodes which contain final dimensions
            elif class_type == 'CLIPTextEncodeSDXLRefiner':
                if 'width' in inputs and 'height' in inputs:
                    refiner_width = inputs['width']
                    refiner_height = inputs['height']
                    # Only use if we haven't found dimensions yet
                    if not width and not height:
                        width = refiner_width
                        height = refiner_height
        
        if width and height:
            lines.append(f"Width: {width}")
            lines.append(f"Height: {height}")
            aspect_ratio = round(width / height, 2)
            lines.append(f"Resolution: {width}x{height} ({aspect_ratio})")
        
        return lines
    
    def _format_upscaling_section(self, metadata: Dict[str, Any]) -> Optional[List[str]]:
        """Format upscaling parameters to match original format"""
        lines = ["=== UPSCALING ==="]
        
        method = None
        upscale_model = None
        upscale_by = None
        
        # First pass: collect upscale model loaders
        upscale_models = {}
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            if class_type == 'UpscaleModelLoader':
                if 'model_name' in inputs:
                    upscale_models[node_id] = inputs['model_name']
        
        # Second pass: find upscaling methods and link to models
        for node_id, node_data in metadata.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            # Method 1: ImageUpscaleWithModel (simple upscale)
            if class_type == 'ImageUpscaleWithModel':
                method = 'ImageUpscaleWithModel'
                # Look for connected upscale model
                if 'upscale_model' in inputs:
                    model_ref = inputs['upscale_model']
                    if isinstance(model_ref, list) and len(model_ref) >= 1:
                        model_node_id = model_ref[0]
                        if model_node_id in upscale_models:
                            upscale_model = upscale_models[model_node_id]
                break
            
            # Method 2: UltimateSDUpscale (SD-based upscaling)
            elif class_type == 'UltimateSDUpscale':
                method = 'UltimateSDUpscale'
                # Get upscale factor
                if 'upscale_by' in inputs:
                    upscale_by = inputs['upscale_by']
                # Look for connected upscale model
                if 'upscale_model' in inputs:
                    model_ref = inputs['upscale_model']
                    if isinstance(model_ref, list) and len(model_ref) >= 1:
                        model_node_id = model_ref[0]
                        if model_node_id in upscale_models:
                            upscale_model = upscale_models[model_node_id]
                break
        
        # Check if we have upscaling info
        if method or upscale_model:
            if method:
                lines.append(f"Method: {method}")
            if upscale_model:
                lines.append(f"Upscale Model: {upscale_model}")
            if upscale_by and upscale_by != 1.0:
                lines.append(f"Upscale Factor: {upscale_by}x")
            return lines
        
        return None
    
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
