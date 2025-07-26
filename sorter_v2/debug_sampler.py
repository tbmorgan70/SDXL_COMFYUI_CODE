"""
Debug script to examine sampler metadata
"""
from PIL import Image
import json

def debug_sampler_metadata():
    # Load one of the original images to see the raw metadata
    img_path = r"D:\ComfyUI_windows_portable\ComfyUI\output\test_batch6\[test_bacth5] Gen 01 $0003.png"
    
    try:
        print("🔍 Loading image metadata...")
        img = Image.open(img_path)
        workflow_data = img.info.get('workflow')
        
        if workflow_data:
            workflow = json.loads(workflow_data)
            print(f"\n📊 Found {len(workflow)} nodes in workflow")
            
            # Look for sampler nodes
            sampler_nodes = []
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict):
                    class_type = node_data.get('class_type', '')
                    if 'sampler' in class_type.lower():
                        title = node_data.get('_meta', {}).get('title', 'No Title')
                        inputs = node_data.get('inputs', {})
                        sampler_nodes.append({
                            'node_id': node_id,
                            'class_type': class_type,
                            'title': title,
                            'inputs': inputs
                        })
            
            print(f"\n🎯 Found {len(sampler_nodes)} sampler nodes:")
            for i, sampler in enumerate(sampler_nodes, 1):
                print(f"\n--- Sampler {i} ---")
                print(f"Node ID: {sampler['node_id']}")
                print(f"Class Type: {sampler['class_type']}")
                print(f"Title: {sampler['title']}")
                print(f"Inputs:")
                for key, value in sampler['inputs'].items():
                    print(f"  {key}: {value}")
                    
                # Determine what we think this is
                title_lower = sampler['title'].lower()
                inputs = sampler['inputs']
                is_refiner = (
                    'refiner' in title_lower or
                    ('start_at_step' in inputs and inputs.get('start_at_step', 0) > 0)
                )
                print(f"Detected as: {'REFINER' if is_refiner else 'BASE'}")
        else:
            print("❌ No workflow data found in image")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    debug_sampler_metadata()
