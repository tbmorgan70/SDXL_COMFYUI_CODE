# Sorter 2.0 Developer Documentation

## Architecture Overview

Sorter 2.0 follows a modular architecture designed for maintainability, extensibility, and reliability. The system is built around single-threaded processing with optional GUI threading for responsiveness.

## Directory Structure

```
sorter_v2/
├── main.py                 # Command-line interface
├── gui.py                  # Modern CustomTkinter GUI
├── gui_standard.py         # Standard tkinter GUI
├── requirements.txt        # Python dependencies
├── core/                   # Core system modules
│   ├── __init__.py
│   ├── metadata_engine.py  # ComfyUI PNG metadata extraction
│   └── diagnostics.py      # Logging and statistics
├── sorters/                # Sorting algorithm modules
│   ├── __init__.py
│   ├── checkpoint_sorter.py    # Sort by AI model checkpoint
│   ├── metadata_search.py      # Search and filter by metadata
│   ├── color_sorter.py          # Color-based image analysis
│   └── image_flattener.py       # Flat structure organization
└── ui/                     # User interface components
    └── __init__.py
```

## Core Modules

### MetadataEngine (`core/metadata_engine.py`)

**Purpose:** Extract and parse ComfyUI PNG metadata from images.

**Key Classes:**
- `MetadataEngine`: Main class for metadata operations

**Key Methods:**
```python
def extract_metadata(self, image_path: str) -> dict
def get_checkpoint_name(self, metadata: dict) -> str
def search_metadata(self, metadata: dict, search_terms: list) -> bool
```

**Technical Details:**
- Uses PIL/Pillow for PNG metadata extraction
- Parses JSON-encoded ComfyUI workflow data
- Handles various metadata formats and versions
- Graceful degradation for images without metadata

**Extension Points:**
- Add new metadata parsers by extending `extract_metadata()`
- Support additional image formats by modifying `SUPPORTED_EXTENSIONS`

### Diagnostics System (`core/diagnostics.py`)

**Purpose:** Comprehensive logging, progress tracking, and statistics collection.

**Key Classes:**
- `SortLogger`: Thread-safe logging with session management
- `SortStatistics`: Operation metrics and performance tracking

**Key Features:**
- Session-based log files with timestamps
- CSV export for statistical analysis
- Progress callbacks for GUI integration
- Operation timing and success/failure tracking

**Threading Model:**
- Thread-safe logging using file locks
- Progress callbacks designed for GUI thread communication
- No internal threading - safe for single or multi-threaded use

## Sorting Modules

### Checkpoint Sorter (`sorters/checkpoint_sorter.py`)

**Algorithm:**
1. Scan source directory for supported image files
2. Extract metadata from each image
3. Identify base checkpoint from workflow data
4. Create destination folders for each unique checkpoint
5. Copy images to appropriate checkpoint folders

**Performance Characteristics:**
- O(n) time complexity where n = number of images
- Memory usage: ~1KB per image for metadata storage
- Disk usage: 2x original collection size (copies, doesn't move)

**Error Handling:**
- Graceful handling of corrupted images
- Fallback categories for images without metadata
- Duplicate filename resolution with numeric suffixes

### Metadata Search (`sorters/metadata_search.py`)

**Search Algorithm:**
- Full-text search across all metadata fields
- Case-insensitive string matching
- Support for multiple search terms (AND logic)
- Regular expression support for advanced queries

**Filtering Options:**
- Checkpoint name filtering
- Sampling method filtering
- Custom field filtering
- Date range filtering (if metadata contains timestamps)

**Performance:**
- Indexed search for large collections
- Lazy loading for memory efficiency
- Parallel processing option for multi-core systems

### Color Sorter (`sorters/color_sorter.py`)

**Color Analysis Algorithm:**
1. Convert images to RGB color space
2. Calculate dominant colors using k-means clustering
3. Map colors to predefined categories
4. Support for custom color definitions

**Color Categories:**
- Basic: Red, Green, Blue, Yellow, Purple, Orange, Pink, Brown
- Advanced: Light/Dark variants, saturation levels
- Custom: User-defined color ranges and HSV mappings

**Technical Implementation:**
- Uses PIL for image processing
- NumPy for efficient color calculations
- Configurable color distance algorithms
- Memory-efficient processing for large images

### Image Flattener (`sorters/image_flattener.py`)

**Flattening Strategy:**
1. Analyze source directory structure
2. Generate descriptive prefixes from metadata
3. Create unique filenames avoiding collisions
4. Organize into flat directory structure

**Naming Convention:**
- `[checkpoint]_[sampler]_[steps]_[original_name]`
- Configurable prefix templates
- Automatic conflict resolution

## User Interface Architecture

### GUI Threading Model

**Design Philosophy:**
- Backend operations run in worker threads
- GUI remains responsive during long operations
- Progress updates via callback system
- No shared state between threads

**Implementation:**
```python
def start_sort_thread(self, operation_func):
    """Start sorting operation in background thread"""
    thread = threading.Thread(target=self.run_sort_with_progress, 
                             args=(operation_func,))
    thread.daemon = True
    thread.start()

def run_sort_with_progress(self, operation_func):
    """Run operation with progress callbacks"""
    try:
        operation_func(progress_callback=self.update_progress)
        self.operation_complete()
    except Exception as e:
        self.operation_error(str(e))
```

### Standard vs Modern GUI

**Standard GUI (`gui_standard.py`):**
- Uses built-in tkinter and ttk
- No external dependencies
- Cross-platform compatibility
- Classic appearance with modern functionality

**Modern GUI (`gui.py`):**
- Uses CustomTkinter for enhanced appearance
- Dark/light theme support
- Modern rounded buttons and styling
- Requires additional dependency

**Shared Functionality:**
- Identical core features and capabilities
- Same progress tracking and logging
- Compatible with all backend modules

## Extension Guidelines

### Adding New Sorting Methods

1. Create new module in `sorters/` directory
2. Implement required interface:
   ```python
   class NewSorter:
       def __init__(self, metadata_engine, logger):
           self.metadata_engine = metadata_engine
           self.logger = logger
       
       def sort_images(self, source_dir, dest_dir, progress_callback=None):
           # Implementation here
           pass
   ```

3. Add to main menu in `main.py`
4. Add GUI integration in both GUI files

### Adding New Metadata Extractors

1. Extend `MetadataEngine.extract_metadata()`
2. Add new file format to `SUPPORTED_EXTENSIONS`
3. Implement format-specific parsing logic
4. Add tests for new format support

### Custom Color Categories

1. Modify color definitions in `color_sorter.py`
2. Add new color mapping functions
3. Update GUI color selection options
4. Test with representative image samples

## Testing Guidelines

### Unit Testing
- Test each sorter module independently
- Mock file system operations for speed
- Verify error handling and edge cases
- Test with various metadata formats

### Integration Testing
- Test complete workflows end-to-end
- Verify GUI and command-line interfaces
- Test with real image collections
- Performance testing with large datasets

### Performance Benchmarks
- Target: 1000 images processed in under 2 minutes
- Memory usage should remain under 500MB for large collections
- GUI responsiveness during operations
- Progress tracking accuracy

## Deployment Considerations

### System Requirements
- Python 3.7+ (tested through 3.11)
- 4GB RAM minimum, 8GB recommended for large collections
- Storage: 2x source collection size for operations
- Modern CPU recommended for color analysis

### Packaging Options
1. **Source Distribution:** Direct Python execution
2. **PyInstaller:** Single executable for end users
3. **Docker:** Containerized deployment for servers
4. **Virtual Environment:** Isolated dependency management

### Configuration Management
- Environment variables for default paths
- Configuration files for user preferences
- Command-line arguments for automation
- GUI settings persistence

## Security Considerations

### File System Security
- Input validation for all file paths
- Protection against directory traversal attacks
- Proper permission handling
- Safe temporary file creation

### Metadata Security
- Sanitize metadata before processing
- Handle malformed metadata gracefully
- Protect against XML/JSON injection attacks
- Validate image file integrity

## Troubleshooting for Developers

### Common Development Issues

**Import Errors:**
- Verify Python path includes sorter_v2 directory
- Check all __init__.py files are present
- Ensure dependencies are installed

**GUI Threading Issues:**
- Always use progress_callback for GUI updates
- Never update GUI elements from worker threads
- Use queue.Queue for thread communication if needed

**Memory Leaks:**
- Close file handles properly
- Clear large data structures after use
- Monitor memory usage during development

### Debugging Tools

**Logging:**
- Enable verbose logging: `logger.set_level(logging.DEBUG)`
- Check log files in session directories
- Use progress callbacks for operation tracking

**Profiling:**
- Use cProfile for performance analysis
- Monitor file I/O with system tools
- Track memory usage with memory_profiler

**Testing:**
- Use small test image collections
- Verify operations with known metadata
- Test error conditions and edge cases

## Future Development Roadmap

### Planned Features
1. **Database Integration:** SQLite for metadata indexing
2. **Plugin System:** Dynamic loading of custom sorters
3. **Web Interface:** Browser-based operation for remote use
4. **Batch Scripting:** Automated workflow execution
5. **Cloud Storage:** Support for cloud-based image collections

### Architecture Improvements
1. **Async Processing:** Non-blocking I/O for better performance
2. **Distributed Processing:** Multi-machine support for large collections
3. **Caching System:** Metadata caching for faster repeated operations
4. **Configuration UI:** Graphical configuration management

### Performance Optimizations
1. **Parallel Processing:** Multi-core utilization for color analysis
2. **Memory Optimization:** Streaming processing for massive collections
3. **Database Indexing:** Fast metadata queries
4. **Progressive Loading:** Lazy loading for GUI responsiveness
