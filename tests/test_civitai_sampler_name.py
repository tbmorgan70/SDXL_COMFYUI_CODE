import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from sorters.civitai_prep import civitai_sampler_name  # noqa: E402


def test_er_sde_gets_a_display_name():
    # Krea2 workflows use er_sde + beta; this used to come out as "er_sde_beta"
    assert civitai_sampler_name("er_sde", "beta") == "ER SDE"
    assert civitai_sampler_name("er_sde", "karras") == "ER SDE Karras"


def test_known_samplers_unchanged():
    assert civitai_sampler_name("dpmpp_2m", "karras") == "DPM++ 2M Karras"
    assert civitai_sampler_name("euler_ancestral", "normal") == "Euler a"
    assert civitai_sampler_name("dpmpp_2m_sde_gpu", "exponential") == "DPM++ 2M SDE Exponential"


def test_unknown_sampler_falls_back_to_raw_name():
    assert civitai_sampler_name("res_multistep", "simple") == "res_multistep_simple"
    assert civitai_sampler_name("res_multistep", "normal") == "res_multistep"
