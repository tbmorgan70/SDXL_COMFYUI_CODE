# ComfyUI to Civitai Metadata Converter

## Overview

This tool converts ComfyUI output images to have Civitai-compatible metadata. It extracts resource information from ComfyUI's workflow metadata and adds SHA256 hashes in the format that Civitai expects for automatic resource detection.

## What It Does

The Civitai extension for Automatic1111 adds metadata like this to generated images:
```
Hashes: {"model": "abc1234567", "lora:myLora": "def8901234", "vae": "ghi5678901"}
```

This tool:
1. **Reads ComfyUI metadata** from PNG files (workflow and prompt data)
2. **Identifies resources** used (checkpoints, LoRAs, VAEs, embeddings)
3. **Calculates SHA256 hashes** for all identified resources
4. **Adds Civitai-compatible metadata** to the images
5. **Preserves original ComfyUI data** while adding the new format

## Installation & Setup

### Requirements
- Python 3.7+
- Pillow library (`pip install pillow`)

### Quick Start
1. Download both files to your ComfyUI directory:
   - `comfyui_to_civitai_converter.py`
   - `convert_comfyui_to_civitai.bat`

2. Double-click `convert_comfyui_to_civitai.bat` for a guided conversion

### Manual Usage

```bash
python comfyui_to_civitai_converter.py /path/to/comfyui/output
```

With custom model paths:
```bash
python comfyui_to_civitai_converter.py /path/to/output \
  --checkpoints /path/to/checkpoints \
  --loras /path/to/loras \
  --vaes /path/to/vaes \
  --embeddings /path/to/embeddings
```

## Configuration

### Model Directory Structure

The converter looks for models in these default locations:
```
models/
├── checkpoints/          # .safetensors, .ckpt files
├── loras/               # LoRA files
├── vae/                 # VAE files
└── embeddings/          # Textual inversion files
```

### Supported ComfyUI Nodes

The converter recognizes these ComfyUI node types:
- **CheckpointLoaderSimple**, **CheckpointLoader** → Model hashes
- **LoraLoader**, **LoraLoaderModelOnly** → LoRA hashes  
- **VAELoader** → VAE hashes
- **Future**: Embeddings, ControlNet, Upscalers

## Examples

### Example 1: Basic Conversion
```bash
# Convert all PNG files in output directory
python comfyui_to_civitai_converter.py "C:\ComfyUI\output"
```

### Example 2: Custom Model Paths
```bash
# Specify where your models are located
python comfyui_to_civitai_converter.py "C:\ComfyUI\output" \
  --checkpoints "D:\AI\Models\Checkpoints" \
  --loras "D:\AI\Models\LoRA"
```

### Example 3: Output to Different Directory
```bash
# Create converted copies in a new directory
python comfyui_to_civitai_converter.py "C:\ComfyUI\output" \
  -o "C:\ConvertedImages"
```

## How It Works

### 1. Resource Detection
The converter parses ComfyUI's workflow JSON to find:
```json
{
  "class_type": "CheckpointLoaderSimple",
  "inputs": {
    "ckpt_name": "realismEngineSDXL_v30VAE.safetensors"
  }
}
```

### 2. Hash Calculation
For each found resource, it:
- Locates the file in your model directories
- Calculates the SHA256 hash
- Stores the first 10 characters (Civitai format)

### 3. Metadata Addition
Adds this to the PNG metadata:
```
Original ComfyUI data..., Hashes: {"model": "a1b2c3d4e5", "lora:DetailTweaker": "f6g7h8i9j0"}
```

## Troubleshooting

### "Could not find hash for..."
This means the converter found a resource name in the workflow but couldn't locate the actual file. Check:
- File still exists in the expected location
- Correct model directory paths specified
- File name matches exactly

### "No resources found"
The ComfyUI workflow might not contain recognizable resource nodes, or:
- PNG file lacks ComfyUI metadata
- Workflow uses custom nodes not yet supported
- File format is not PNG

### "Error reading metadata"
- File might be corrupted
- Not a valid PNG file
- Missing ComfyUI workflow data

## Integration with Civitai

After conversion, when you upload images to Civitai:

1. **Automatic Resource Detection**: Civitai will read the hash metadata
2. **Resource Linking**: Resources will be automatically linked to your image
3. **Prompt Enhancement**: Resource names can be hashified for portability

## Advanced Usage

### Batch Processing
```bash
# Process multiple directories
for dir in output1 output2 output3; do
    python comfyui_to_civitai_converter.py "$dir"
done
```

### Integration with Existing Workflows
```python
from comfyui_to_civitai_converter import ComfyUIToCivitaiConverter

# Create converter with your model paths
converter = ComfyUIToCivitaiConverter({
    'checkpoints': '/path/to/checkpoints',
    'loras': '/path/to/loras'
})

# Convert single image
converter.convert_image('image.png')
```

## Future Enhancements

Planned features:
- [ ] Support for more ComfyUI nodes (ControlNet, Upscalers)
- [ ] GUI interface
- [ ] Integration with ComfyUI as a custom node
- [ ] Batch processing improvements
- [ ] Configuration file support

## Contributing

Found a bug or want to add support for more ComfyUI nodes? The main areas to extend:

1. **Node Recognition**: Add new node types in `_process_workflow_node()` and `_process_prompt_node()`
2. **Resource Types**: Extend the resource scanning in `_scan_directory()`
3. **Metadata Formats**: Handle different ComfyUI metadata structures

## License

This tool is provided as-is to help bridge ComfyUI and Civitai workflows. Use at your own risk and always backup your original files.
