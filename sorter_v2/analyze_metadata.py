import json
from PIL import Image
import sys
import os

# Get the filename as argument
if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    # Find any PNG file in current directory
    png_files = [f for f in os.listdir('.') if f.lower().endswith('.png')]
    if png_files:
        filename = png_files[0]
    else:
        print("No PNG files found")
        exit(1)

print(f"Analyzing: {filename}")
img = Image.open(filename)
print('=== METADATA STRUCTURE ===')

# Extract metadata using the same method as the metadata engine
metadata = None
prompt_data = img.info.get('prompt')
if prompt_data:
    metadata = json.loads(prompt_data)
else:
    # Try other fields
    for field in ['parameters', 'workflow', 'extra_pnginfo']:
        data = img.info.get(field)
        if data:
            try:
                if isinstance(data, str):
                    metadata = json.loads(data)
                else:
                    metadata = data
                break
            except (json.JSONDecodeError, TypeError):
                continue

if not metadata:
    print("No metadata found in image")
    exit(1)

print('\nAll node types:')
for node_id, node_data in metadata.items():
    if isinstance(node_data, dict):
        class_type = node_data.get('class_type', 'Unknown')
        title = node_data.get('_meta', {}).get('title', 'No title')
        print(f'{node_id}: {class_type} - {title}')

print('\nUpscaling related nodes:')
for node_id, node_data in metadata.items():
    if isinstance(node_data, dict):
        class_type = node_data.get('class_type', 'Unknown')
        title = node_data.get('_meta', {}).get('title', 'No title')
        if ('upscale' in class_type.lower() or 'upscale' in title.lower() or 
            class_type in ['ImageUpscaleWithModel', 'UpscaleModelLoader']):
            print(f'UPSCALE NODE {node_id}: {class_type} - {title}')
            inputs = node_data.get('inputs', {})
            print(f'  Inputs: {inputs}')
            print()

print('\nLatent/Image size nodes:')
for node_id, node_data in metadata.items():
    if isinstance(node_data, dict):
        class_type = node_data.get('class_type', 'Unknown')
        title = node_data.get('_meta', {}).get('title', 'No title')
        if ('latent' in class_type.lower() or 'empty' in class_type.lower() or 
            'width' in str(node_data.get('inputs', {})) or 'height' in str(node_data.get('inputs', {}))):
            print(f'SIZE NODE {node_id}: {class_type} - {title}')
            inputs = node_data.get('inputs', {})
            print(f'  Inputs: {inputs}')
            print()
