"""Extended diagnostic for large batch processing"""
import os
import sys
import json
import time
import traceback
from pathlib import Path

# Add the sorter directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'sorter'))

try:
    from sorter.final_batch_rename_sort import extract_comfyui_metadata
    print("✅ Successfully imported metadata extractor")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def stress_test_metadata(test_dir, max_files=None):
    """Stress test metadata extraction like a real batch operation"""
    test_dir = test_dir.strip('"').strip("'")
    
    if not os.path.exists(test_dir):
        print(f"❌ Directory not found: {test_dir}")
        return
    
    png_files = [f for f in os.listdir(test_dir) if f.lower().endswith('.png')]
    total_files = len(png_files)
    
    if max_files:
        png_files = png_files[:max_files]
        print(f"📁 Testing {len(png_files)} of {total_files} PNG files")
    else:
        print(f"📁 Testing ALL {total_files} PNG files")
    
    if len(png_files) == 0:
        print("⚠️  No PNG files found in directory")
        return
    
    successful = 0
    failed = 0
    problematic_files = []
    processing_times = []
    memory_issues = []
    
    start_time = time.time()
    
    for i, png_file in enumerate(png_files):
        file_path = os.path.join(test_dir, png_file)
        file_start = time.time()
        
        # Progress indicator for large batches
        if (i + 1) % 50 == 0 or i == 0:
            print(f"\n🔄 Processing {i+1}/{len(png_files)}...")
        
        try:
            metadata = extract_comfyui_metadata(file_path)
            file_time = time.time() - file_start
            processing_times.append(file_time)
            
            if metadata:
                # Count nodes in metadata (complexity indicator)
                node_count = len(metadata)
                
                # Look for key fields
                checkpoints = []
                loras = []
                for entry in metadata.values():
                    inputs = entry.get('inputs', {})
                    if 'ckpt_name' in inputs:
                        checkpoints.append(inputs['ckpt_name'])
                    if 'lora_name' in inputs:
                        loras.append(inputs['lora_name'])
                
                successful += 1
                
                # Check for potential issues
                if file_time > 1.0:  # Slow processing
                    memory_issues.append(f"{png_file}: {file_time:.2f}s")
                if node_count > 100:  # Complex workflow
                    memory_issues.append(f"{png_file}: {node_count} nodes")
                    
            else:
                print(f"  ⚠️  No metadata: {png_file}")
                failed += 1
                problematic_files.append((png_file, "No metadata found"))
                
        except Exception as e:
            file_time = time.time() - file_start
            error_msg = str(e)
            print(f"  ❌ Failed: {png_file} - {error_msg}")
            failed += 1
            problematic_files.append((png_file, error_msg))
            
            # Print full traceback for first few errors
            if len(problematic_files) <= 3:
                print(f"     Full error: {traceback.format_exc()}")
    
    total_time = time.time() - start_time
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    print(f"\n📊 Final Results:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏱️  Total time: {total_time:.2f} seconds")
    print(f"   ⚡ Average per file: {avg_time:.3f} seconds")
    
    if problematic_files:
        print(f"\n🚨 Problematic files:")
        for filename, error in problematic_files[:10]:  # Show first 10
            print(f"   - {filename}: {error}")
        if len(problematic_files) > 10:
            print(f"   ... and {len(problematic_files) - 10} more")
    
    if memory_issues:
        print(f"\n⚠️  Performance issues:")
        for issue in memory_issues[:5]:  # Show first 5
            print(f"   - {issue}")
    
    return successful, failed, problematic_files

if __name__ == "__main__":
    test_dir = input("Enter path to test directory: ").strip()
    max_files_input = input("Max files to test (press Enter for all): ").strip()
    
    max_files = None
    if max_files_input:
        try:
            max_files = int(max_files_input)
        except ValueError:
            print("Invalid number, testing all files")
    
    stress_test_metadata(test_dir, max_files)
