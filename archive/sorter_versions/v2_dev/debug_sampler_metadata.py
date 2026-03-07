"""
Debug script to examine sampler metadata in PNG files
"""

import sys
import os
import json
from PIL import Image

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_sampler_metadata():
    """Debug sampler metadata extraction"""
    
    # Use one of the test images
    img_path = r"D:\ComfyUI_windows_portable\ComfyUI\output\test_batch6\[test_batch6] Gen 01 $0001.png"
    
    if not os.path.exists(img_path):
        print(f"❌ Image not found: {img_path}")
        return
    
    print(f"🔍 Analyzing metadata from: {os.path.basename(img_path)}")
    print("=" * 60)
    
    try:
        # Load image and extract metadata
        img = Image.open(img_path)
        
        # Check both workflow and prompt data
        workflow_data = img.info.get('workflow')
        prompt_data = img.info.get('prompt')
        
        print("📋 METADATA SOURCES:")
        print(f"   Workflow data: {'✅ Found' if workflow_data else '❌ Not found'}")
        print(f"   Prompt data: {'✅ Found' if prompt_data else '❌ Not found'}")
        
        # Try prompt data first (this is usually where the actual execution data is)
        if prompt_data:
            print("\n� ANALYZING PROMPT DATA:")
            print("=" * 60)
            
            prompt = json.loads(prompt_data)
            
            sampler_count = 0
            
            for node_id, node_data in prompt.items():
                if not isinstance(node_data, dict):
                    continue
                    
                class_type = node_data.get('class_type', '')
                inputs = node_data.get('inputs', {})
                
                print(f"\n📝 NODE {node_id}")
                print(f"   Class Type: {class_type}")
                
                # Look for sampler nodes
                if 'sampler' in class_type.lower() or 'ksampler' in class_type.lower():
                    sampler_count += 1
                    print(f"   🎯 *** SAMPLER NODE #{sampler_count} ***")
                    
                    # Show all inputs
                    print(f"   Inputs:")
                    for key, value in inputs.items():
                        print(f"     {key}: {value}")
                    
                    # Check for refiner indicators
                    is_refiner_indicators = []
                    
                    if 'start_at_step' in inputs:
                        start_step = inputs['start_at_step']
                        if start_step > 0:
                            is_refiner_indicators.append(f"start_at_step = {start_step} (> 0)")
                    
                    if 'end_at_step' in inputs:
                        end_step = inputs['end_at_step']
                        is_refiner_indicators.append(f"end_at_step = {end_step}")
                    
                    if is_refiner_indicators:
                        print(f"   🔴 DETECTED AS REFINER:")
                        for indicator in is_refiner_indicators:
                            print(f"     - {indicator}")
                    else:
                        print(f"   🟢 DETECTED AS BASE SAMPLER")
                
                print("-" * 40)
            
            print(f"\n✅ Prompt analysis complete. Found {sampler_count} sampler node(s)")
        
        # Also check workflow data if available
        elif workflow_data:
            print("\n🔍 ANALYZING WORKFLOW DATA:")
            print("=" * 60)
            
            workflow = json.loads(workflow_data)
            print(f"Found {len(workflow)} nodes in workflow")
            
            for node_id, node_data in workflow.items():
                if not isinstance(node_data, dict):
                    continue
                    
                class_type = node_data.get('class_type', '')
                print(f"Node {node_id}: {class_type}")
        
        else:
            print("❌ No workflow or prompt data found")
            
    except Exception as e:
        print(f"❌ Error analyzing metadata: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_sampler_metadata()
