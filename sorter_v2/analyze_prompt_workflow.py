import json
from PIL import Image
import sys
import os

def analyze_prompt_workflow(filename):
    """Analyze prompt workflow in detail"""
    
    print(f"Analyzing: {filename}")
    img = Image.open(filename)
    
    # Extract metadata using the same method as the metadata engine
    metadata = None
    prompt_data = img.info.get('prompt')
    if prompt_data:
        metadata = json.loads(prompt_data)
    else:
        print("No metadata found")
        return

    print('\n=== PROMPT WORKFLOW ANALYSIS ===')
    
    # Find all text-related nodes
    text_nodes = {}
    for node_id, node_data in metadata.items():
        if isinstance(node_data, dict):
            class_type = node_data.get('class_type', '')
            title = node_data.get('_meta', {}).get('title', '')
            inputs = node_data.get('inputs', {})
            
            if any(keyword in class_type.lower() for keyword in ['text', 'show', 'clip']):
                text_nodes[node_id] = {
                    'class_type': class_type,
                    'title': title,
                    'inputs': inputs
                }
    
    # Print all text-related nodes
    for node_id, node_info in text_nodes.items():
        print(f"\nNode {node_id}: {node_info['class_type']} - {node_info['title']}")
        print(f"  Inputs: {node_info['inputs']}")
        
        # If this is a CLIP encode node, trace its text input
        if 'CLIPTextEncode' in node_info['class_type']:
            text_input = node_info['inputs'].get('text', '')
            print(f"  TEXT INPUT: {repr(text_input)}")
            
            # If text input is a node reference, look up that node
            if isinstance(text_input, list) and len(text_input) >= 1:
                ref_node_id = text_input[0]
                if ref_node_id in metadata:
                    ref_node = metadata[ref_node_id]
                    print(f"  REFERENCES NODE {ref_node_id}: {ref_node.get('class_type', '')} - {ref_node.get('_meta', {}).get('title', '')}")
                    print(f"  REF NODE INPUTS: {ref_node.get('inputs', {})}")
                    
                    # If the referenced node has a 'text' output, try to get it
                    if 'inputs' in ref_node:
                        ref_inputs = ref_node['inputs']
                        if 'text' in ref_inputs:
                            print(f"  ACTUAL TEXT: {repr(ref_inputs['text'])}")

if __name__ == "__main__":
    # Find any PNG file in current directory
    png_files = [f for f in os.listdir('.') if f.lower().endswith('.png')]
    if png_files:
        analyze_prompt_workflow(png_files[0])
    else:
        print("No PNG files found")
