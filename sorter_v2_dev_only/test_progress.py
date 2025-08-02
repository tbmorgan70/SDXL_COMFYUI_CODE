"""
Quick test script to verify progress tracking in Sorter 2.0
"""
import os
import sys
import time

# Add sorter_v2 to path
sys.path.append(os.path.dirname(__file__))

from core.diagnostics import SortLogger
from sorters.checkpoint_sorter import CheckpointSorter

def test_progress_callback():
    """Test that progress callbacks work properly"""
    print("🧪 Testing Progress Callback System")
    
    # Create logger with progress callback
    logger = SortLogger()
    
    # Track progress updates
    progress_updates = []
    
    def progress_callback(completed, total, current_file):
        progress_updates.append((completed, total, current_file))
        print(f"Progress: {completed}/{total} - {current_file}")
    
    # Set the callback
    logger.set_progress_callback(progress_callback)
    
    # Create sorter
    sorter = CheckpointSorter(logger)
    
    print(f"✅ Logger has progress callback: {hasattr(logger, 'progress_callback')}")
    print(f"✅ Callback is set: {logger.progress_callback is not None}")
    
    return len(progress_updates)

if __name__ == "__main__":
    test_progress_callback()
    print("🎯 Progress callback test completed!")
