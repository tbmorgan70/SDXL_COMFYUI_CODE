"""Quick diagnostic script to test current metadata extraction"""
import os
import sys
import json
from pathlib import Path

# Add the sorter directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'sorter'))

try:
    from sorter.final_batch_rename_sort import extract_comfyui_metadata
    print("✅ Successfully imported metadata extractor")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_metadata_extraction(test_dir):
    """Test metadata extraction on a small batch"""
    # Clean up the path (remove quotes if present)
    test_dir = test_dir.strip('"').strip("'")
    
    if not os.path.exists(test_dir):
        print(f"❌ Directory not found: {test_dir}")
        return
    
    png_files = [f for f in os.listdir(test_dir) if f.lower().endswith('.png')]
    print(f"📁 Found {len(png_files)} PNG files in {test_dir}")
    
    if len(png_files) == 0:
        print("⚠️  No PNG files found in directory")
        return
    
    successful = 0
    failed = 0
    
    for i, png_file in enumerate(png_files[:10]):  # Test first 10 files
        file_path = os.path.join(test_dir, png_file)
        print(f"\n🔍 Testing {i+1}/10: {png_file}")
        
        try:
            metadata = extract_comfyui_metadata(file_path)
            if metadata:
                # Look for key fields
                checkpoints = []
                loras = []
                for entry in metadata.values():
                    inputs = entry.get('inputs', {})
                    if 'ckpt_name' in inputs:
                        checkpoints.append(inputs['ckpt_name'])
                    if 'lora_name' in inputs:
                        loras.append(inputs['lora_name'])
                
                print(f"  ✅ Metadata extracted")
                print(f"  📋 Checkpoints: {checkpoints}")
                print(f"  🎨 LoRAs: {loras}")
                successful += 1
            else:
                print(f"  ⚠️  No metadata found")
                failed += 1
                
        except Exception as e:
            print(f"  ❌ Extraction failed: {e}")
            failed += 1
    
    print(f"\n📊 Results: {successful} successful, {failed} failed")
    return successful, failed

if __name__ == "__main__":
    # Test with a sample directory
    test_dir = input("Enter path to test directory with PNG files: ").strip()
    test_metadata_extraction(test_dir)
