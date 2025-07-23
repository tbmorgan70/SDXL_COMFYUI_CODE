"""
Quick test for the enhanced metadata formatter
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_metadata_formatter import EnhancedMetadataFormatter
from core.metadata_engine import MetadataExtractor

def test_formatter_with_sample():
    """Test the formatter with a sample image"""
    
    # Get sample image from user
    sample_image = input("Enter path to a sample PNG image: ").strip().strip('"\'')
    
    if not os.path.exists(sample_image):
        print("❌ File not found")
        return
    
    if not sample_image.lower().endswith('.png'):
        print("❌ Please provide a PNG image file (you provided a .txt file)")
        print("💡 Try using one of these PNG files:")
        print("   [new_pipeline_batch1] Gen 17 $0073.png")
        print("   [new_pipeline_batch1] Gen 19 $0089.png")
        return
    
    print(f"🔍 Testing metadata extraction and formatting for: {os.path.basename(sample_image)}")
    
    # Extract metadata
    extractor = MetadataExtractor()
    metadata = extractor.extract_single(sample_image)
    
    if not metadata:
        print("❌ No metadata found in image")
        return
    
    print("✅ Metadata extracted successfully")
    
    # Format metadata
    formatter = EnhancedMetadataFormatter()
    formatted_text = formatter.format_metadata_to_text(metadata, sample_image)
    
    print("\n" + "=" * 60)
    print("FORMATTED METADATA:")
    print("=" * 60)
    print(formatted_text)
    print("=" * 60)
    
    # Test grouping methods
    base_model = formatter.get_base_model(metadata)
    lora_stack = formatter.get_lora_stack_signature(metadata)
    
    print(f"\n🔍 GROUPING INFO:")
    print(f"Base Model: {base_model}")
    print(f"LoRA Stack Signature: {lora_stack}")
    
    # Offer to save test file
    save_test = input("\nSave formatted text to file? (y/n): ").lower() == 'y'
    if save_test:
        output_path = os.path.splitext(sample_image)[0] + "_test_format.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        print(f"✅ Saved to: {output_path}")

if __name__ == "__main__":
    test_formatter_with_sample()
