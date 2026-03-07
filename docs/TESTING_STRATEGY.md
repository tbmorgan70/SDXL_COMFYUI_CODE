# 🧪 Testing Strategy - SDXL ComfyUI Code

**Created:** March 7, 2026  
**Status:** Active Planning - Phase 4  
**Target Coverage:** 90%  
**Current Coverage:** ~5% (limited to metadata engine)

---

## 📋 Overview

This document outlines the comprehensive testing strategy for achieving robust, production-ready code across all tools in the SDXL_COMFYUI_CODE repository.

### Goals:
1. **Achieve 90% test coverage** across all Python code
2. **Prevent regressions** through comprehensive test suites
3. **Enable confident refactoring** with safety nets
4. **Document expected behavior** through tests
5. **Support CI/CD pipeline** for automated validation

---

## 🔍 Current State Assessment

### Existing Tests (tests/ directory)

| Test File | Status | Purpose | Coverage |
|-----------|--------|---------|----------|
| `test_seed_extraction.py` | ❌ Empty | Seed value parsing | 0% |
| `test_enhanced_seeds.py` | ❌ Empty | Advanced seed handling | 0% |
| `test_extract_primary_checkpoint.py` | ✅ Implemented | Checkpoint detection | ~50% |
| `test_lora_formatting.py` | ❌ Empty | LoRA string parsing | 0% |
| `test_cfg_resolution.py` | ❌ Empty | CFG parameter extraction | 0% |
| `test_seed_edge_cases.py` | ❌ Empty | Edge case handling | 0% |

**Current Coverage Estimate:** ~5%
- ✅ Some metadata extraction (checkpoint detection)
- ❌ No sorter operations testing
- ❌ No converter testing
- ❌ No GUI testing
- ❌ No integration testing

### Gaps Identified:
1. **Empty test stubs** - 5 of 6 test files have no implementation
2. **No integration tests** - Tools tested in isolation only
3. **No functional tests** - End-to-end workflows untested
4. **No GUI tests** - User interface completely untested
5. **Missing test fixtures** - No sample data for consistent testing
6. **No CI/CD** - Manual testing only

---

## 🎯 Testing Pyramid

```
                    ┌─────────────┐
                    │   E2E Tests │  ← 10% (slowest, highest value)
                    │  (Selenium, │
                    │   Playwright)│
                    └─────────────┘
                ┌───────────────────┐
                │ Integration Tests │  ← 20% (moderate speed/value)
                │  (Cross-component)│
                └───────────────────┘
            ┌─────────────────────────┐
            │     Unit Tests          │  ← 70% (fast, focused)
            │   (Individual funcs)    │
            └─────────────────────────┘
```

### Target Distribution:
- **70% Unit Tests** - Fast, focused, comprehensive coverage
- **20% Integration Tests** - Component interaction validation
- **10% E2E Tests** - Critical workflow validation

---

## 🧩 Test Organization Structure

### Proposed Directory Layout:

```
tests/
├── __init__.py
├── conftest.py                     # Pytest configuration & fixtures
│
├── unit/                           # Unit tests (70% coverage target)
│   ├── __init__.py
│   ├── sorter/
│   │   ├── test_metadata_engine.py
│   │   ├── test_checkpoint_sorter.py
│   │   ├── test_lora_sorter.py
│   │   ├── test_color_sorter.py
│   │   └── test_image_flattener.py
│   │
│   ├── converter/
│   │   ├── test_converter_core.py
│   │   ├── test_hash_calculation.py
│   │   └── test_metadata_injection.py
│   │
│   └── lib/                        # Future unified library tests
│       ├── test_config_manager.py
│       ├── test_metadata_handler.py
│       └── test_file_operations.py
│
├── integration/                    # Integration tests (20% target)
│   ├── __init__.py
│   ├── test_sorter_converter_chain.py
│   ├── test_metadata_preservation.py
│   ├── test_workflow_chains.py
│   └── test_unified_config.py
│
├── functional/                     # End-to-end tests (10% target)
│   ├── __init__.py
│   ├── test_complete_sort_workflow.py
│   ├── test_batch_processing.py
│   └── test_gui_operations.py
│
└── fixtures/                       # Test data
    ├── sample_images/
    │   ├── comfyui_metadata.png
    │   ├── no_metadata.png
    │   └── malformed_metadata.png
    │
    ├── sample_workflows/
    │   ├── simple_workflow.json
    │   ├── complex_workflow.json
    │   └── refiner_workflow.json
    │
    ├── sample_csvs/
    │   └── test_categories.csv
    │
    └── expected_outputs/
        ├── sorted_structure/
        └── converted_metadata/
```

---

## 🔬 Test Categories & Requirements

### 1. Unit Tests (Core Focus)

**Sorter - Metadata Engine:**
```python
# tests/unit/sorter/test_metadata_engine.py

def test_extract_metadata_from_valid_png():
    """Extract ComfyUI metadata from valid PNG"""
    image_path = fixtures.get_sample_image("comfyui_metadata.png")
    metadata = MetadataExtractor.extract(image_path)
    
    assert metadata is not None
    assert "workflow" in metadata
    assert "prompt" in metadata

def test_handle_missing_metadata():
    """Gracefully handle PNG without metadata"""
    image_path = fixtures.get_sample_image("no_metadata.png")
    metadata = MetadataExtractor.extract(image_path)
    
    assert metadata is None  # Or empty dict, depending on design

def test_handle_malformed_json():
    """Handle corrupted workflow JSON"""
    image_path = fixtures.get_sample_image("malformed_metadata.png")
    # Should not raise exception
    metadata = MetadataExtractor.extract(image_path)
    
    assert metadata is not None  # Partial extraction or logged error
```

**Sorter - Checkpoint Sorter:**
```python
# tests/unit/sorter/test_checkpoint_sorter.py

def test_sort_by_checkpoint_creates_folders():
    """Verify folder structure creation"""
    sorter = CheckpointSorter(source=test_dir, output=output_dir)
    result = sorter.sort()
    
    assert (output_dir / "sdxl_base").exists()
    assert (output_dir / "pony_diffusion").exists()

def test_checkpoint_sorter_preserves_metadata():
    """Ensure .txt files move with images"""
    # Create test image with .txt file
    sorter = CheckpointSorter(source=test_dir, output=output_dir)
    result = sorter.sort()
    
    assert (output_dir / "sdxl_base" / "image001.png").exists()
    assert (output_dir / "sdxl_base" / "image001.txt").exists()

def test_checkpoint_sorter_handles_no_metadata():
    """Images without metadata sorted to no_metadata/ folder"""
    sorter = CheckpointSorter(source=test_dir, output=output_dir)
    result = sorter.sort()
    
    assert (output_dir / "no_metadata").exists()
    assert len(list((output_dir / "no_metadata").glob("*.png"))) > 0
```

**Converter - Core Functions:**
```python
# tests/unit/converter/test_converter_core.py

def test_identify_checkpoint_from_workflow():
    """Extract checkpoint name from workflow JSON"""
    workflow = load_fixture("simple_workflow.json")
    converter = CivitAIConverter()
    checkpoint = converter.identify_checkpoint(workflow)
    
    assert checkpoint == "sdxl_base.safetensors"

def test_calculate_sha256_hash():
    """Verify hash calculation accuracy"""
    test_file = fixtures.get_test_model("test_checkpoint.safetensors")
    converter = CivitAIConverter()
    hash_value = converter.calculate_hash(test_file)
    
    assert len(hash_value) == 64  # SHA256 length
    assert hash_value == "expected_hash_value"

def test_inject_civitai_metadata():
    """Add Civitai metadata without corrupting image"""
    source_image = fixtures.get_sample_image("comfyui_metadata.png")
    converter = CivitAIConverter()
    output = converter.convert(source_image)
    
    # Original metadata preserved
    original_meta = extract_metadata(source_image)
    new_meta = extract_metadata(output)
    assert original_meta["workflow"] == new_meta["workflow"]
    
    # Civitai metadata added
    assert "Hashes" in new_meta
```

---

### 2. Integration Tests (Cross-Component)

**Sorter + Converter Chain:**
```python
# tests/integration/test_sorter_converter_chain.py

def test_sort_then_convert_workflow():
    """Sort images, then convert sorted results"""
    # Step 1: Sort images
    sorter = CheckpointSorter(source=test_images, output=sorted_dir)
    sort_result = sorter.sort()
    
    assert sort_result["success"]
    
    # Step 2: Convert sorted images
    converter = CivitAIConverter()
    convert_result = converter.convert_directory(sorted_dir)
    
    assert convert_result["success"]
    # Verify folder structure preserved
    assert (sorted_dir / "sdxl_base" / "image001.png").exists()
    # Verify Civitai metadata added
    metadata = extract_metadata(sorted_dir / "sdxl_base" / "image001.png")
    assert "Hashes" in metadata
```

**Metadata Preservation Across Tools:**
```python
# tests/integration/test_metadata_preservation.py

def test_metadata_survives_sort_and_convert():
    """Ensure original ComfyUI metadata survives both operations"""
    original_image = create_test_image_with_metadata()
    original_meta = extract_metadata(original_image)
    
    # Sort
    sorter.sort()
    sorted_image = find_sorted_image(original_image.name)
    sorted_meta = extract_metadata(sorted_image)
    
    assert original_meta["workflow"] == sorted_meta["workflow"]
    
    # Convert
    converter.convert(sorted_image)
    final_meta = extract_metadata(sorted_image)
    
    assert original_meta["workflow"] == final_meta["workflow"]
    assert "Hashes" in final_meta  # Added by converter
```

---

### 3. Functional Tests (End-to-End)

**Complete Workflow:**
```python
# tests/functional/test_complete_sort_workflow.py

def test_full_sorting_workflow_gui():
    """Simulate complete user workflow through GUI"""
    # Launch GUI (automated browser/GUI testing)
    app = launch_sorter_gui()
    
    # Select source directory
    app.set_source_directory(test_images)
    
    # Choose operation
    app.select_operation("checkpoint")
    
    # Configure options
    app.set_file_operation("copy")
    app.set_create_metadata(True)
    
    # Execute
    app.click_sort_button()
    
    # Wait for completion
    app.wait_for_completion()
    
    # Verify results
    assert app.get_status() == "Complete"
    assert app.files_processed > 0
    assert output_dir.exists()
```

**Batch Processing:**
```python
# tests/functional/test_batch_processing.py

def test_sort_1000_images():
    """Performance and stability test with large batch"""
    # Create 1000 test images
    test_images = create_test_images(count=1000)
    
    sorter = CheckpointSorter(source=test_dir, output=output_dir)
    
    start_time = time.time()
    result = sorter.sort()
    elapsed = time.time() - start_time
    
    assert result["success"]
    assert result["files_processed"] == 1000
    assert result["files_failed"] == 0
    
    # Performance assertion (adjust based on hardware)
    assert elapsed < 600  # 10 minutes max for 1000 images
```

---

## 🛠️ Testing Tools & Frameworks

### Primary: pytest

**Configuration (`conftest.py`):**
```python
import pytest
from pathlib import Path
import shutil

@pytest.fixture
def temp_test_dir(tmp_path):
    """Temporary directory for test operations"""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    yield test_dir
    shutil.rmtree(test_dir, ignore_errors=True)

@pytest.fixture
def sample_image():
    """Load sample ComfyUI image"""
    return Path("tests/fixtures/sample_images/comfyui_metadata.png")

@pytest.fixture
def sample_workflow():
    """Load sample workflow JSON"""
    import json
    with open("tests/fixtures/sample_workflows/simple_workflow.json") as f:
        return json.load(f)

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "sorter": {
            "default_operation": "checkpoint",
            "create_metadata": True
        },
        "converter": {
            "calculate_hashes": False  # Faster for tests
        }
    }
```

### Additional Tools:

**Coverage Analysis:**
```bash
# Install
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

**GUI Testing (Future):**
```bash
# For Tkinter GUI
pip install pytest-tk

# For web interface
pip install pytest-selenium playwright
```

**Mocking & Fixtures:**
```bash
pip install pytest-mock
pip install faker  # Generate test data
```

---

## 📦 Test Fixtures & Sample Data

### Required Fixtures:

**1. Sample Images:**
- `comfyui_metadata.png` - Valid ComfyUI PNG with full metadata
- `no_metadata.png` - Standard PNG without metadata
- `malformed_metadata.png` - PNG with corrupted JSON
- `multiple_checkpoints.png` - Workflow with base + refiner
- `complex_loras.png` - Image with 5+ LoRAs

**2. Sample Workflows:**
- `simple_workflow.json` - Basic SDXL generation
- `complex_workflow.json` - Multiple nodes, LoRAs, ControlNet
- `refiner_workflow.json` - Base + refiner checkpoint
- `no_checkpoint_workflow.json` - Invalid/incomplete workflow

**3. Sample CSV Categories:**
- `test_bodytype.csv` - Sample category data
- `test_scene.csv` - Sample scene data
- `empty_category.csv` - Empty CSV (edge case)
- `malformed_category.csv` - Invalid CSV format

**4. Expected Outputs:**
- Sample sorted folder structures
- Sample converted metadata
- Sample log files

---

## 🚀 Implementation Plan

### Phase 4A: Foundation (Current - Q2 2026)

- [ ] Create `tests/fixtures/` directory structure
- [ ] Generate sample test data (images, workflows, CSVs)
- [ ] Configure pytest with `conftest.py`
- [ ] Implement unit tests for metadata engine (complete existing stubs)
- [ ] Achieve 25% coverage

**Priority Files:**
1. Complete `test_seed_extraction.py`
2. Complete `test_lora_formatting.py`
3. Complete `test_cfg_resolution.py`
4. Complete `test_seed_edge_cases.py`
5. Complete `test_enhanced_seeds.py`

### Phase 4B: Expansion (Q3 2026)

- [ ] Unit tests for all sorter operations
- [ ] Unit tests for converter
- [ ] Integration tests (2-3 key scenarios)
- [ ] Achieve 60% coverage

### Phase 4C: Comprehensive Coverage (Q4 2026)

- [ ] Complete unit test suite (all modules)
- [ ] Complete integration test suite
- [ ] Add functional tests for critical workflows
- [ ] GUI testing infrastructure
- [ ] Achieve 90% coverage

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`
```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: windows-latest
    
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock
    
    - name: Run tests with coverage
      run: |
        pytest tests/ --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
    
    - name: Check coverage threshold
      run: |
        pytest tests/ --cov=. --cov-fail-under=50  # Gradually increase
```

### Pre-commit Hooks

**File:** `.pre-commit-config.yaml`
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/ --cov=. --cov-fail-under=50
        language: system
        pass_filenames: false
        always_run: true
```

---

## 📊 Coverage Targets & Milestones

### Progressive Coverage Goals:

| Milestone | Target | Components | Timeline |
|-----------|--------|------------|----------|
| Phase 4A Complete | 25% | Metadata engine | Q2 2026 |
| Phase 4B Complete | 60% | Sorter + Converter | Q3 2026 |
| Phase 4C Complete | 90% | All tools + Integration | Q4 2026 |

### Per-Component Targets:

| Component | Target | Priority |
|-----------|--------|----------|
| Sorter Core | 95% | ⭐⭐⭐ High |
| Metadata Engine | 100% | ⭐⭐⭐ High |
| CivitAI Converter | 90% | ⭐⭐ Medium |
| Config Manager | 95% | ⭐⭐ Medium |
| Builder API | 80% | ⭐ Low |
| GUI | 50% | ⭐ Low |

---

## ✅ Definition of Done

A component is considered "tested" when:

- [ ] Unit tests cover all public functions
- [ ] Edge cases are tested (empty inputs, malformed data, etc.)
- [ ] Integration tests verify component interactions
- [ ] At least one functional test validates end-to-end workflow
- [ ] All tests pass consistently
- [ ] Coverage meets or exceeds target threshold
- [ ] Tests are documented and maintainable

---

## 📚 Related Documentation

- [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) - Tool integration architecture
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development setup and standards
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and components
- [CURATION_PLAN.md](../CURATION_PLAN.md) - Repository overhaul phases

---

## 💡 Best Practices

### Writing Good Tests:

1. **AAA Pattern:** Arrange, Act, Assert
2. **One Assertion Focus:** Test one thing per test
3. **Descriptive Names:** `test_checkpoint_sorter_handles_missing_metadata`
4. **Independent Tests:** No test depends on another
5. **Fast Tests:** Unit tests should run in milliseconds
6. **Reproducible:** Same input = same output, always

### Example Test Template:

```python
def test_specific_behavior_under_condition():
    """
    Clear description of what this test validates.
    Explain any non-obvious setup or assertions.
    """
    # Arrange: Set up test data and conditions
    test_data = create_test_data()
    expected_result = "expected_value"
    
    # Act: Execute the function being tested
    actual_result = function_under_test(test_data)
    
    # Assert: Verify expected behavior
    assert actual_result == expected_result
    assert len(actual_result) > 0
    # Add specific assertions as needed
```

---

**Status:** 📋 Strategy Complete - Ready for Implementation  
**Next Steps:** Begin implementing unit tests for metadata engine  
**Owner:** Development team  
**Last Updated:** March 7, 2026
