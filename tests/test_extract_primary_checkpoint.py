import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from core.metadata_engine import MetadataAnalyzer


def _ksampler(model_link):
    return {"class_type": "KSampler",
            "inputs": {"model": model_link, "steps": 30, "cfg": 7.0, "denoise": 1.0}}


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


# --- the filename is only a hint -----------------------------------------
# Measured on 1,786 real PNGs: 266 (15%) were sorted under a fragment of the
# filename ("00013", "sampler", "Show") although 244 of those workflows named
# the real checkpoint.

def test_sequence_number_in_filename_is_not_a_checkpoint():
    metadata = {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "realModel_v2.safetensors"}},
        "9": _ksampler(["4", 0]),
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata, "ComfyUI_00013_.png")
        == "realModel_v2.safetensors"
    )


def test_save_prefix_in_filename_is_not_a_checkpoint():
    metadata = {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "realModel_v2.safetensors"}},
        "9": _ksampler(["4", 0]),
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata, "post_sampler_00007_.png")
        == "realModel_v2.safetensors"
    )


def test_filename_hint_still_wins_when_it_names_a_workflow_checkpoint():
    # Two loaders; the filename (written by Image Saver) says which one ran.
    metadata = {
        "689": {"class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "ANIME\\animosity_illustriousV10.safetensors"}},
        "1027": {"class_type": "Checkpoint Loader with Name (Image Saver)",
                 "inputs": {"ckpt_name": "ANIME\\ultraRealisticByStable_v25.safetensors"}},
    }
    name = "2026-08-01-142436_ultraRealisticByStable_v25_757337583580541_03.png"
    assert MetadataAnalyzer.extract_primary_checkpoint(metadata, name) == "ultraRealisticByStable"


def test_hint_kept_when_the_workflow_names_no_checkpoint():
    # An unrecognised loader: the filename is all there is to go on.
    metadata = {"1": {"class_type": "SomeCustomLoader", "inputs": {"path": "x"}}}
    name = "2025-10-15-182703_pieModels_elderberryPie_710452282418503.png"
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata, name)
        == "pieModels_elderberryPie"
    )


def test_sequence_number_ignored_when_the_workflow_names_no_checkpoint():
    metadata = {"1": {"class_type": "LoadImage", "inputs": {"image": "a.png"}}}
    assert MetadataAnalyzer.extract_primary_checkpoint(metadata, "ComfyUI_00009_.png") is None


# --- which of two loaders actually fed the sampler ------------------------

def test_unhinted_file_uses_the_checkpoint_feeding_the_sampler():
    metadata = {
        "689": {"class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "leftover.safetensors"}},
        "1027": {"class_type": "Checkpoint Loader with Name (Image Saver)",
                 "inputs": {"ckpt_name": "SDXL\\realOne_v10.safetensors"}},
        "20": {"class_type": "LoraLoader",
               "inputs": {"model": ["1027", 0], "clip": ["1027", 1],
                          "lora_name": "detail.safetensors"}},
        "30": _ksampler(["20", 0]),
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata, "ComfyUI_00042_.png")
        == "SDXL\\realOne_v10.safetensors"
    )


def test_base_pass_checkpoint_beats_the_refiner_pass():
    metadata = {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "refinerModel.safetensors"}},
        "2": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "baseModel.safetensors"}},
        "10": {"class_type": "KSampler",
               "inputs": {"model": ["1", 0], "steps": 8, "denoise": 0.35}},
        "11": _ksampler(["2", 0]),
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata, "ComfyUI_00001_.png")
        == "baseModel.safetensors"
    )


def test_custom_sampler_model_is_traced_through_the_guider():
    metadata = {
        "5": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_dev.safetensors"}},
        "6": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "leftover.safetensors"}},
        "7": {"class_type": "CFGGuider",
              "inputs": {"model": ["5", 0], "cfg": 3.5,
                         "positive": ["90", 0], "negative": ["91", 0]}},
        "8": {"class_type": "SamplerCustomAdvanced",
              "inputs": {"guider": ["7", 0], "noise": ["92", 0],
                         "sampler": ["93", 0], "sigmas": ["94", 0]}},
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata, "ComfyUI_00003_.png")
        == "krea2_dev.safetensors"
    )


def test_model_traced_through_a_pipe_bundle():
    metadata = {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "leftover.safetensors"}},
        "2": {"class_type": "Checkpoint Loader with Name (Image Saver)",
              "inputs": {"ckpt_name": "piped.safetensors"}},
        "836": {"class_type": "easy pipeIn",
                "inputs": {"model": ["2", 0], "pos": ["50", 0], "neg": ["51", 0]}},
        "837": {"class_type": "easy pipeOut", "inputs": {"pipe": ["836", 0]}},
        "16": {"class_type": "KSamplerAdvanced",
               "inputs": {"model": ["837", 1], "start_at_step": 0, "steps": 30}},
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata, "ComfyUI_00004_.png")
        == "piped.safetensors"
    )


def test_checkpoint_name_supplied_by_a_name_node_is_followed():
    # "easy ckptNames" holds the name; the loader only links to it.
    metadata = {
        "3": {"class_type": "easy ckptNames", "inputs": {"ckpt_name": "named.safetensors"}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ["3", 0]}},
        "9": _ksampler(["4", 0]),
    }
    assert (
        MetadataAnalyzer.extract_primary_checkpoint(metadata, "ComfyUI_00005_.png")
        == "named.safetensors"
    )


def test_checkpoint_that_fed_the_sampler_beats_a_filename_naming_another():
    # Checkpoint-comparison workflows save every image under one name
    metadata = {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "REALISM\\artaixRealismSDXL_v30.safetensors"}},
        "2": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "REALISM\\midnight_v50.safetensors"}},
        "9": _ksampler(["2", 0]),
    }
    name = "2026-09-02-101500_artaixRealismSDXL_v30_123456789_01.png"
    assert (MetadataAnalyzer.extract_primary_checkpoint(metadata, name)
            == "REALISM\\midnight_v50.safetensors")


def test_hint_kept_when_it_agrees_with_the_sampler():
    # Same model either way: keep the hint so existing folder names don't change
    metadata = {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "SDXL\\ultraRealisticByStable_v25.safetensors"}},
        "9": _ksampler(["1", 0]),
    }
    name = "2026-08-01-142436_ultraRealisticByStable_v25_757337583580541_03.png"
    assert MetadataAnalyzer.extract_primary_checkpoint(metadata, name) == "ultraRealisticByStable"
