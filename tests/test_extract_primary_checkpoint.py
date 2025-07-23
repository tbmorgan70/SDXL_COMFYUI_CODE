import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sorter_v2.core.metadata_engine import MetadataAnalyzer


def test_base_and_refiner_nodes():
    metadata = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "baseModel.safetensors"},
            "_meta": {"title": "Load Checkpoint"},
        },
        "2": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "refinerModel.safetensors"},
            "_meta": {"title": "Refiner"},
        },
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata)
        == "baseModel.safetensors"
    )


def test_base_ckpt_field():
    metadata = {
        "1": {
            "class_type": "KSamplerAdvanced",
            "inputs": {
                "refiner_ckpt": "refiner.safetensors",
                "base_ckpt": "baseModel.safetensors",
                "start_at_step": 0.5,
            },
            "_meta": {"title": "Refiner Sampler"},
        }
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata)
        == "baseModel.safetensors"
    )


def test_refiner_fallback():
    metadata = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "refinerOnly.safetensors"},
            "_meta": {"title": "Refiner"},
        }
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata)
        == "refinerOnly.safetensors"
    )
