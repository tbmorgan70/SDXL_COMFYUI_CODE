"""
Sorter 2.0 - Enhanced Diagnostics & Logging System

Provides comprehensive logging, batch statistics, and diagnostics
for large-scale image sorting operations.

Features:
- Real-time progress tracking
- Detailed operation statistics  
- Error categorization and reporting
- Performance metrics
- Export capabilities for analysis
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import csv

class SortLogger:
    """Enhanced logging system for sorting operations"""
    
    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir or os.getcwd()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        
        # Create logs directory
        self.logs_path = os.path.join(self.log_dir, "sort_logs")
        os.makedirs(self.logs_path, exist_ok=True)
        
        # Log files
        self.main_log = os.path.join(self.logs_path, f"sort_{self.session_id}.log")
        self.stats_file = os.path.join(self.logs_path, f"stats_{self.session_id}.json")
        self.errors_file = os.path.join(self.logs_path, f"errors_{self.session_id}.csv")
        
        # Statistics tracking
        self.stats = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'total_files_found': 0,
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'files_moved': 0,
            'files_copied': 0,
            'folders_created': 0,
            'metadata_extractions': 0,
            'metadata_failures': 0,
            'sort_operations': {},
            'performance': {},
            'errors': []
        }
        
        # Progress tracking
        self.current_operation = ""
        self.progress_callback: Optional[Callable] = None
        
        # Initialize log file
        self._write_log("=== Sorter 2.0 Session Started ===")
        self._write_log(f"Session ID: {self.session_id}")
        self._write_log(f"Log Directory: {self.logs_path}")
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback function for progress updates"""
        self.progress_callback = callback
    
    def start_operation(self, operation_name: str, total_items: int = 0):
        """Start a new operation with progress tracking"""
        self.current_operation = operation_name
        self.stats['sort_operations'][operation_name] = {
            'start_time': time.time(),
            'total_items': total_items,
            'completed_items': 0,
            'errors': 0,
            'status': 'running'
        }
        
        self._write_log(f"\n--- Starting: {operation_name} ---")
        if total_items > 0:
            self._write_log(f"Total items to process: {total_items}")
    
    def update_progress(self, completed: int, total: int, current_item: str = ""):
        """Update progress for current operation"""
        if self.current_operation in self.stats['sort_operations']:
            op_stats = self.stats['sort_operations'][self.current_operation]
            op_stats['completed_items'] = completed
            
            # Call progress callback if set
            if self.progress_callback:
                self.progress_callback(completed, total, current_item)
            
            # Log milestone progress
            if completed > 0 and completed % 50 == 0:
                self._write_log(f"Progress: {completed}/{total} - {current_item}")
    
    def log_config(self, key: str, value: str):
        """Log configuration setting"""
        self._write_log(f"{key}: {value}")
    
    def log_info(self, message: str):
        """Log info message"""
        self._write_log(message)
    
    def log_error(self, message: str, file_path: str = "", operation: str = ""):
        """Log error message with optional context"""
        error_record = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'error_type': 'ERROR',
            'message': message,
            'file': file_path,
            'operation': operation or self.current_operation
        }
        
        self.stats['errors'].append(error_record)
        self._write_error_csv(error_record)
        self._write_log(f"ERROR: {message}")
    
    def log_file_operation(self, operation: str, source: str, target: str = ""):
        """Log file operation (COPIED, MOVED, etc.)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if target:
            self._write_log(f"[{timestamp}] {operation}: {source} -> {target}")
        else:
            self._write_log(f"[{timestamp}] {operation}: {source}")
    
    def log_folder_operation(self, operation: str, folder_path: str):
        """Log folder operation (Created, Removed, etc.)"""
        self._write_log(f"[FOLDER] {operation}: {folder_path}")
        if operation.lower() in ['created', 'create']:
            self.stats['folders_created'] += 1
    
    def start_phase(self, phase_name: str):
        """Start a new phase within the current operation"""
        self._write_log(f"--- Starting: {phase_name} ---")
    
    def end_phase(self, phase_name: str):
        """End the current phase"""
        self._write_log(f"--- Completed: {phase_name} ---")
        phase_duration = time.time() - (self.stats['sort_operations'].get(self.current_operation, {}).get('start_time', time.time()))
        self._write_log(f"Duration: {phase_duration:.2f} seconds")
        # Add items processed count if relevant
        op_stats = self.stats['sort_operations'].get(self.current_operation, {})
        items_processed = op_stats.get('completed_items', 0)
        self._write_log(f"Items processed: {items_processed}")
    
    def end_operation(self, operation_name: str):
        """End the current operation"""
        if operation_name in self.stats['sort_operations']:
            op_stats = self.stats['sort_operations'][operation_name]
            op_stats['end_time'] = time.time()
            op_stats['duration'] = op_stats['end_time'] - op_stats['start_time']
            op_stats['status'] = 'completed'
        
        self._write_log(f"--- Completed: {operation_name} ---")
        if operation_name in self.stats['sort_operations']:
            duration = self.stats['sort_operations'][operation_name]['duration']
            items = self.stats['sort_operations'][operation_name]['completed_items']
            self._write_log(f"Duration: {duration:.2f} seconds")
            self._write_log(f"Items processed: {items}")
        
        self.current_operation = ""

    def log_folder_operation(self, operation: str, folder_path: str):
        """Log folder creation/deletion operations"""
        self._write_log(f"[FOLDER] {operation}: {folder_path}")
        self.stats['folders_created'] += 1
    
    def log_file_operation(self, operation: str, source_path: str, target_path: str = ""):
        """Log file operations (copy, move, etc.)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if target_path:
            self._write_log(f"[{timestamp}] {operation}: {source_path} -> {target_path}")
        else:
            self._write_log(f"[{timestamp}] {operation}: {source_path}")
        
        # Update operation counts
        if self.current_operation in self.stats['sort_operations']:
            op_stats = self.stats['sort_operations'][self.current_operation]
            op_stats['completed_items'] = op_stats.get('completed_items', 0) + 1
    
    def start_phase(self, phase_name: str):
        """Start a new phase within current operation"""
        self._write_log(f"--- Starting: {phase_name} ---")
    
    def end_phase(self, phase_name: str):
        """End current phase"""
        self._write_log(f"--- Completed: {phase_name} ---")
        duration = time.time() - self.stats['sort_operations'].get(self.current_operation, {}).get('start_time', time.time())
        self._write_log(f"Duration: {duration:.2f} seconds")
        
    def end_operation(self, operation_name: str):
        """End current operation"""
        if operation_name in self.stats['sort_operations']:
            op_stats = self.stats['sort_operations'][operation_name]
            op_stats['end_time'] = time.time()
            op_stats['duration'] = op_stats['end_time'] - op_stats.get('start_time', op_stats['end_time'])
            op_stats['status'] = 'completed'
            
        self._write_log(f"--- Completed: {operation_name} ---")
        self._write_log(f"Duration: {op_stats.get('duration', 0):.2f} seconds")
        self._write_log(f"Items processed: {op_stats.get('completed_items', 0)}")
    
    def complete_operation(self, success: bool = True):
        """Complete the current operation"""
        if self.current_operation in self.stats['sort_operations']:
            op_stats = self.stats['sort_operations'][self.current_operation]
            op_stats['end_time'] = time.time()
            op_stats['duration'] = op_stats['end_time'] - op_stats['start_time']
            op_stats['status'] = 'completed' if success else 'failed'
            
            self._write_log(f"--- Completed: {self.current_operation} ---")
            self._write_log(f"Duration: {op_stats['duration']:.2f} seconds")
            self._write_log(f"Items processed: {op_stats['completed_items']}")
    
    def log_file_operation(self, operation: str, source: str, destination: str = "", success: bool = True):
        """Log individual file operations"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if success:
            if operation == "move":
                self.stats['files_moved'] += 1
                self._write_log(f"[{timestamp}] MOVED: {os.path.basename(source)} -> {destination}")
            elif operation == "copy":
                self.stats['files_copied'] += 1
                self._write_log(f"[{timestamp}] COPIED: {os.path.basename(source)} -> {destination}")
            elif operation == "rename":
                self._write_log(f"[{timestamp}] RENAMED: {os.path.basename(source)} -> {os.path.basename(destination)}")
            
            self.stats['files_successful'] += 1
        else:
            self.stats['files_failed'] += 1
            self.log_error(f"File operation failed: {operation}", source, "File operation error")
    
    def log_metadata_extraction(self, file_path: str, success: bool, metadata_size: int = 0):
        """Log metadata extraction results"""
        if success:
            self.stats['metadata_extractions'] += 1
            self._write_log(f"[META] ✅ {os.path.basename(file_path)} - {metadata_size} nodes")
        else:
            self.stats['metadata_failures'] += 1
            self._write_log(f"[META] ❌ {os.path.basename(file_path)} - extraction failed")
    
    def log_error(self, error_message: str, file_path: str = "", error_type: str = "General"):
        """Log errors with categorization"""
        timestamp = datetime.now().isoformat()
        error_record = {
            'timestamp': timestamp,
            'error_type': error_type,
            'message': error_message,
            'file_path': file_path,
            'operation': self.current_operation
        }
        
        self.stats['errors'].append(error_record)
        self._write_log(f"[ERROR] {error_type}: {error_message}")
        
        if file_path:
            self._write_log(f"        File: {file_path}")
        
        # Write to error CSV
        self._write_error_csv(error_record)
    
    def log_folder_created(self, folder_path: str):
        """Log folder creation"""
        self.stats['folders_created'] += 1
        self._write_log(f"[FOLDER] Created: {folder_path}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        current_time = time.time()
        total_duration = current_time - self.start_time
        
        summary = {
            **self.stats,
            'end_time': datetime.now().isoformat(),
            'total_duration_seconds': total_duration,
            'total_duration_formatted': self._format_duration(total_duration),
            'success_rate': self._calculate_success_rate(),
            'performance_metrics': self._calculate_performance_metrics()
        }
        
        return summary
    
    def save_session(self):
        """Save session statistics to JSON file"""
        summary = self.get_summary()
        
        with open(self.stats_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self._write_log(f"\n=== Session Summary ===")
        self._write_log(f"Files processed: {summary['files_processed']}")
        self._write_log(f"Success rate: {summary['success_rate']:.1f}%")
        self._write_log(f"Total duration: {summary['total_duration_formatted']}")
        self._write_log(f"Statistics saved: {self.stats_file}")
        
        return summary
    
    def export_results(self, export_path: str):
        """Export detailed results for analysis"""
        summary = self.get_summary()
        
        # Create export directory
        os.makedirs(export_path, exist_ok=True)
        
        # Export summary
        summary_file = os.path.join(export_path, f"summary_{self.session_id}.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Export operation details
        if summary['sort_operations']:
            ops_file = os.path.join(export_path, f"operations_{self.session_id}.csv")
            with open(ops_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Operation', 'Duration', 'Items', 'Status'])
                
                for op_name, op_data in summary['sort_operations'].items():
                    writer.writerow([
                        op_name,
                        f"{op_data.get('duration', 0):.2f}s",
                        op_data.get('completed_items', 0),
                        op_data.get('status', 'unknown')
                    ])
        
        self._write_log(f"Results exported to: {export_path}")
        return export_path
    
    def _write_log(self, message: str):
        """Write message to log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        with open(self.main_log, 'a', encoding='utf-8') as f:
            f.write(log_line)
        
        # Also print to console
        print(message)
    
    def _write_error_csv(self, error_record: Dict[str, str]):
        """Write error to CSV file"""
        file_exists = os.path.exists(self.errors_file)
        
        with open(self.errors_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['Timestamp', 'Type', 'Message', 'File', 'Operation'])
            
            writer.writerow([
                error_record['timestamp'],
                error_record['error_type'],
                error_record['message'],
                error_record['file_path'],
                error_record['operation']
            ])
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total = self.stats['files_successful'] + self.stats['files_failed']
        if total == 0:
            return 100.0
        return (self.stats['files_successful'] / total) * 100
    
    def _calculate_performance_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        total_duration = time.time() - self.start_time
        
        metrics = {
            'files_per_second': 0,
            'average_operation_time': 0,
            'metadata_success_rate': 0
        }
        
        if total_duration > 0:
            metrics['files_per_second'] = self.stats['files_processed'] / total_duration
        
        # Calculate metadata success rate
        total_meta = self.stats['metadata_extractions'] + self.stats['metadata_failures']
        if total_meta > 0:
            metrics['metadata_success_rate'] = (self.stats['metadata_extractions'] / total_meta) * 100
        
        return metrics
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"


# Example usage
if __name__ == "__main__":
    # Test the logging system
    logger = SortLogger()
    
    # Simulate a sorting operation
    logger.start_operation("Test Sort", 10)
    
    for i in range(10):
        logger.update_progress(i + 1, f"test_file_{i}.png")
        logger.log_file_operation("move", f"test_file_{i}.png", "sorted/folder/", success=True)
        time.sleep(0.1)  # Simulate processing time
    
    logger.complete_operation(success=True)
    
    # Save and show summary
    summary = logger.save_session()
    print(f"\n📊 Session Summary: {json.dumps(summary, indent=2)}")
