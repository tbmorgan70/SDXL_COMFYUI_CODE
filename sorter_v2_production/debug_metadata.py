"""
Debug script to investigate prompt extraction issues
Run this to see what metadata is actually being extracted from your images
"""

import os
import sys
import json
from pathlib import Path

# Add the production folder to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.metadata_engine import MetadataExtractor, MetadataAnalyzer
from core.enhanced_metadata_formatter import EnhancedMetadataFormatter

def debug_image_metadata(image_path):
    """Debug what metadata is actually extracted from an image"""
    
    print(f"🔍 Debugging metadata extraction for: {os.path.basename(image_path)}")
    print("=" * 60)
    
    # Step 1: Raw metadata extraction
    extractor = MetadataExtractor()
    raw_metadata = extractor.extract_single(image_path)
    
    if not raw_metadata:
        print("❌ No metadata found!")
        return
    
    print("✅ Raw metadata extracted successfully")
    print(f"📊 Metadata keys: {list(raw_metadata.keys())}")
    
    # Step 2: Look for text nodes
    print("\n🔍 SEARCHING FOR TEXT NODES:")
    text_nodes = []
    
    for node_id, node_data in raw_metadata.items():
        if not isinstance(node_data, dict):
            continue
            
        class_type = node_data.get('class_type', '')
        inputs = node_data.get('inputs', {})
        title = node_data.get('_meta', {}).get('title', '')
        
        # Find any nodes that might contain text
        if 'text' in inputs or 'CLIPTextEncode' in class_type:
            text_nodes.append({
                'node_id': node_id,
                'class_type': class_type,
                'title': title,
                'inputs': inputs
            })
    
    print(f"📝 Found {len(text_nodes)} potential text nodes:")
    for i, node in enumerate(text_nodes):
        print(f"\n--- Text Node {i+1} ---")
        print(f"ID: {node['node_id']}")
        print(f"Type: {node['class_type']}")
        print(f"Title: {node['title']}")
        
        if 'text' in node['inputs']:
            text_content = node['inputs']['text']
            if isinstance(text_content, str):
                print(f"Text (direct): {text_content[:100]}{'...' if len(text_content) > 100 else ''}")
            elif isinstance(text_content, list):
                print(f"Text (reference): {text_content}")
            else:
                print(f"Text (other): {type(text_content)} - {text_content}")
    
    # Step 3: Test our formatter
    print("\n🎯 TESTING ENHANCED FORMATTER:")
    formatter = EnhancedMetadataFormatter()
    formatted_text = formatter.format_metadata_to_text(raw_metadata, image_path)
    
    print("--- Formatted Output ---")
    print(formatted_text[:500] + "..." if len(formatted_text) > 500 else formatted_text)
    
    # Step 4: Save debug info
    debug_file = f"debug_metadata_{os.path.basename(image_path)}.json"
    with open(debug_file, 'w') as f:
        json.dump(raw_metadata, f, indent=2)
    
    print(f"\n💾 Full metadata saved to: {debug_file}")

if __name__ == "__main__":
    print("🚀 Metadata Debug Tool")
    print("Drag and drop an image file here, or enter the full path:")
    
    image_path = input("Image path: ").strip().strip('"')
    
    if os.path.exists(image_path):
        debug_image_metadata(image_path)
    else:
        print(f"❌ File not found: {image_path}")
