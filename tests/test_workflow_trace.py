import contextlib
import io
import json
import os
import sys

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from core.metadata_engine import WorkflowTrace  # noqa: E402
from sorters.civitai_prep import CivitaiPrep, WorkflowResources  # noqa: E402

REAL_KREA2_PNG = (r"D:\ComfyUI_windows_portable\ComfyUI\output\2026-10-01"
                  r"\RLY-KREA2-Basic_Workflow-v001-Upscaled-Sharp_00001_.png")

LION = ("A national geographic photo of a lion. Closeup of the lion's face, "
        "lion roaring and showing teeth. Extreme detail.")


def node(class_type, title=None, **inputs):
    return {"class_type": class_type, "inputs": inputs,
            "_meta": {"title": title or class_type}}


# ------------------------------------------------------------ graph fixtures

def krea2_graph():
    """Mirror of the user's KREA2 workflow: two SamplerCustomAdvanced passes
    (base txt2img, then latent-upscale at denoise 0.38), CFGGuider with a
    ConditioningZeroOut negative, prompt text from PrimitiveStringMultiline,
    loaders inside a subgraph ("439:436"-style ids)."""
    return {
        "442": node("PrimitiveStringMultiline", "Positive Prompt", value=LION),
        "439:436": node("UNETLoader", unet_name="krea2Turbo.safetensors",
                        weight_dtype="default"),
        "439:437": node("CLIPLoader", clip_name="qwen3vl.safetensors", type="krea2"),
        "439:438": node("VAELoader", vae_name="qwen_image_vae.safetensors"),
        "284": node("Lora Loader Stack (rgthree)",
                    lora_01="None", strength_01=1.0, lora_02="None", strength_02=0.8,
                    model=["439:436", 0], clip=["439:437", 0]),
        "294": node("ModelSamplingAuraFlow", shift=4.5, model=["284", 0]),
        "446": node("SDXL Empty Latent Image (rgthree)",
                    dimensions=" 832 x 1216  (portrait)", batch_size=1),
        # base pass
        "280": node("CLIPTextEncode", "Positive", text=["442", 0], clip=["284", 1]),
        "272": node("ConditioningZeroOut", "Negative (Zeroed)", conditioning=["280", 0]),
        "274": node("CFGGuider", cfg=1.0, model=["294", 0],
                    positive=["280", 0], negative=["272", 0]),
        "277": node("BasicScheduler", scheduler="beta", steps=4, denoise=1.0,
                    model=["294", 0]),
        "278": node("KSamplerSelect", sampler_name="er_sde"),
        "444": node("RandomNoise", noise_seed=556122404112518),
        "279": node("SamplerCustomAdvanced", noise=["444", 0], guider=["274", 0],
                    sampler=["278", 0], sigmas=["277", 0], latent_image=["446", 0]),
        # upscale pass (listed after the base pass is fine either way; ids sort
        # the second pass's helper nodes FIRST in the real file)
        "260": node("ConditioningZeroOut", "Negative (Zeroed)", conditioning=["267", 0]),
        "261": node("RandomNoise", noise_seed=743718985150642),
        "262": node("KSamplerSelect", sampler_name="er_sde"),
        "264": node("CFGGuider", cfg=1.0, model=["294", 0],
                    positive=["267", 0], negative=["260", 0]),
        "265": node("BasicScheduler", scheduler="simple", steps=5, denoise=0.38,
                    model=["294", 0]),
        "267": node("CLIPTextEncode", "Positive", text=["442", 0], clip=["284", 1]),
        "271": node("LatentUpscaleBy", upscale_method="bicubic", scale_by=1.36,
                    samples=["279", 0]),
        "450": node("SamplerCustomAdvanced", noise=["261", 0], guider=["264", 0],
                    sampler=["262", 0], sigmas=["265", 0], latent_image=["271", 0]),
    }


def krea2_graph_upscale_first():
    """Same graph with the upscale pass's nodes inserted first, as in the real
    file's key order — base-pass selection must not depend on dict order."""
    g = krea2_graph()
    order = ["260", "261", "262", "264", "265", "267", "271", "450"]
    return {**{k: g[k] for k in order}, **{k: v for k, v in g.items() if k not in order}}


def flux_basic_guider_graph():
    return {
        "1": node("UNETLoader", unet_name="flux1-dev.safetensors", weight_dtype="default"),
        "2": node("DualCLIPLoader", clip_name1="t5.safetensors", clip_name2="clip_l.safetensors"),
        "6": node("CLIPTextEncode", text="a red fox in snow", clip=["2", 0]),
        "26": node("FluxGuidance", guidance=3.5, conditioning=["6", 0]),
        "22": node("BasicGuider", model=["1", 0], conditioning=["26", 0]),
        "16": node("KSamplerSelect", sampler_name="euler"),
        "17": node("BasicScheduler", scheduler="simple", steps=20, denoise=1.0,
                   model=["1", 0]),
        "25": node("RandomNoise", noise_seed=42),
        "5": node("EmptySD3LatentImage", width=1024, height=1024, batch_size=1),
        "13": node("SamplerCustomAdvanced", noise=["25", 0], guider=["22", 0],
                   sampler=["16", 0], sigmas=["17", 0], latent_image=["5", 0]),
    }


def cfg_guider_with_negative_graph():
    return {
        "1": node("CheckpointLoaderSimple", ckpt_name="sdxl.safetensors"),
        "10": node("PrimitiveString", value="portrait of an astronaut"),
        "2": node("CLIPTextEncode", text=["10", 0], clip=["1", 1]),
        "3": node("CLIPTextEncode", text="blurry, lowres", clip=["1", 1]),
        "4": node("CFGGuider", cfg=6.5, model=["1", 0],
                  positive=["2", 0], negative=["3", 0]),
        "5": node("KSamplerSelect", sampler_name="dpmpp_2m"),
        "6": node("KarrasScheduler", steps=30, sigma_max=14.6, sigma_min=0.03, rho=7.0),
        "7": node("RandomNoise", noise_seed=1234),
        "8": node("EmptyLatentImage", width=1024, height=1024, batch_size=1),
        "9": node("SamplerCustomAdvanced", noise=["7", 0], guider=["4", 0],
                  sampler=["5", 0], sigmas=["6", 0], latent_image=["8", 0]),
    }


def dual_cfg_guider_graph():
    return {
        "1": node("CheckpointLoaderSimple", ckpt_name="sdxl.safetensors"),
        "2": node("CLIPTextEncode", text="a castle on a hill", clip=["1", 1]),
        "3": node("CLIPTextEncode", text="oil painting style", clip=["1", 1]),
        "4": node("CLIPTextEncode", text="ugly, deformed", clip=["1", 1]),
        "5": node("DualCFGGuider", model=["1", 0], cond1=["2", 0], cond2=["3", 0],
                  negative=["4", 0], cfg_conds=5.0, cfg_cond2_negative=2.0),
        "6": node("KSamplerSelect", sampler_name="euler_ancestral"),
        "7": node("BasicScheduler", scheduler="normal", steps=25, denoise=1.0,
                  model=["1", 0]),
        "8": node("RandomNoise", noise_seed=99),
        "9": node("EmptyLatentImage", width=1024, height=1024, batch_size=1),
        "10": node("SamplerCustomAdvanced", noise=["8", 0], guider=["5", 0],
                   sampler=["6", 0], sigmas=["7", 0], latent_image=["9", 0]),
    }


def sampler_custom_graph():
    """SamplerCustom (non-advanced) holds conditioning, cfg and seed itself."""
    return {
        "1": node("CheckpointLoaderSimple", ckpt_name="sdxl.safetensors"),
        "2": node("CLIPTextEncode", text="a lighthouse at dusk", clip=["1", 1]),
        "3": node("CLIPTextEncode", text="text, watermark", clip=["1", 1]),
        "4": node("KSamplerSelect", sampler_name="dpmpp_2m_sde"),
        "5": node("BasicScheduler", scheduler="karras", steps=28, denoise=1.0,
                  model=["1", 0]),
        "6": node("EmptyLatentImage", width=1024, height=1024, batch_size=1),
        "7": node("SamplerCustom", model=["1", 0], add_noise=True, noise_seed=777,
                  cfg=7.0, positive=["2", 0], negative=["3", 0],
                  sampler=["4", 0], sigmas=["5", 0], latent_image=["6", 0]),
    }


def split_sigmas_graph():
    """Flux-style two-stage run: one schedule split in two; the low-sigma half
    is a continuation pass and must not be taken as the base pass."""
    return {
        "1": node("UNETLoader", unet_name="flux1-dev.safetensors", weight_dtype="default"),
        "2": node("CLIPTextEncode", text="base prompt", clip=["1", 1]),
        "3": node("CLIPTextEncode", text="detail prompt", clip=["1", 1]),
        "4": node("BasicGuider", model=["1", 0], conditioning=["3", 0]),
        "5": node("BasicGuider", model=["1", 0], conditioning=["2", 0]),
        "6": node("BasicScheduler", scheduler="simple", steps=24, denoise=1.0,
                  model=["1", 0]),
        "7": node("SplitSigmas", step=16, sigmas=["6", 0]),
        "8": node("KSamplerSelect", sampler_name="euler"),
        "9": node("RandomNoise", noise_seed=5),
        "10": node("DisableNoise"),
        "11": node("EmptySD3LatentImage", width=1024, height=1024, batch_size=1),
        # continuation pass listed first
        "20": node("SamplerCustomAdvanced", noise=["10", 0], guider=["4", 0],
                   sampler=["8", 0], sigmas=["7", 1], latent_image=["21", 0]),
        "21": node("SamplerCustomAdvanced", noise=["9", 0], guider=["5", 0],
                   sampler=["8", 0], sigmas=["7", 0], latent_image=["11", 0]),
    }


# ------------------------------------------------- custom-sampler: prompts

@pytest.mark.parametrize("graph_fn", [krea2_graph, krea2_graph_upscale_first])
def test_krea2_prompt_traced_through_guider_and_primitive(graph_fn):
    prompts = WorkflowTrace.extract_prompts(graph_fn())
    assert prompts["positive"] == LION
    # ConditioningZeroOut of the positive is an empty negative, not a copy
    assert prompts["negative"] == ""


def test_basic_guider_positive_and_no_negative_leak():
    prompts = WorkflowTrace.extract_prompts(flux_basic_guider_graph())
    assert prompts == {"positive": "a red fox in snow", "negative": ""}


def test_cfg_guider_real_negative():
    prompts = WorkflowTrace.extract_prompts(cfg_guider_with_negative_graph())
    assert prompts == {"positive": "portrait of an astronaut",
                       "negative": "blurry, lowres"}


def test_dual_cfg_guider_uses_cond1_and_negative():
    prompts = WorkflowTrace.extract_prompts(dual_cfg_guider_graph())
    assert prompts == {"positive": "a castle on a hill", "negative": "ugly, deformed"}


def test_sampler_custom_direct_conditioning():
    prompts = WorkflowTrace.extract_prompts(sampler_custom_graph())
    assert prompts == {"positive": "a lighthouse at dusk", "negative": "text, watermark"}


def test_split_sigmas_continuation_pass_not_taken_as_base():
    assert WorkflowTrace.extract_prompts(split_sigmas_graph())["positive"] == "base prompt"
    assert WorkflowTrace.extract_seed(split_sigmas_graph()) == 5
    assert WorkflowTrace.extract_sampling(split_sigmas_graph())["steps"] == 24


# ------------------------------------------------ custom-sampler: settings

@pytest.mark.parametrize("graph_fn", [krea2_graph, krea2_graph_upscale_first])
def test_krea2_base_pass_settings(graph_fn):
    g = graph_fn()
    assert WorkflowTrace.extract_sampling(g) == {
        "steps": 4, "cfg": 1.0, "sampler_name": "er_sde",
        "scheduler": "beta", "denoise": 1.0}
    assert WorkflowTrace.extract_seed(g) == 556122404112518


def test_basic_guider_settings_have_no_cfg():
    g = flux_basic_guider_graph()
    assert WorkflowTrace.extract_sampling(g) == {
        "steps": 20, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}
    assert WorkflowTrace.extract_seed(g) == 42


def test_karras_scheduler_node_reports_karras():
    g = cfg_guider_with_negative_graph()
    assert WorkflowTrace.extract_sampling(g) == {
        "steps": 30, "cfg": 6.5, "sampler_name": "dpmpp_2m", "scheduler": "karras"}
    assert WorkflowTrace.extract_seed(g) == 1234


def test_dual_cfg_guider_cfg():
    assert WorkflowTrace.extract_sampling(dual_cfg_guider_graph())["cfg"] == 5.0


def test_sampler_custom_settings():
    g = sampler_custom_graph()
    assert WorkflowTrace.extract_sampling(g) == {
        "steps": 28, "cfg": 7.0, "sampler_name": "dpmpp_2m_sde",
        "scheduler": "karras", "denoise": 1.0}
    assert WorkflowTrace.extract_seed(g) == 777


def test_settings_linked_through_primitives():
    g = krea2_graph()
    g["900"] = node("PrimitiveInt", value=9)
    g["901"] = node("PrimitiveFloat", value=2.5)
    g["902"] = node("PrimitiveInt", value=31337)
    g["277"]["inputs"]["steps"] = ["900", 0]
    g["274"]["inputs"]["cfg"] = ["901", 0]
    g["444"]["inputs"]["noise_seed"] = ["902", 0]
    params = WorkflowTrace.extract_sampling(g)
    assert params["steps"] == 9 and params["cfg"] == 2.5
    assert WorkflowTrace.extract_seed(g) == 31337


# ---------------------------------------- KSampler family (regression guard)

def test_ksampler_simple():
    g = {
        "4": node("CheckpointLoaderSimple", ckpt_name="sdxl.safetensors"),
        "6": node("CLIPTextEncode", text="a cat", clip=["4", 1]),
        "7": node("CLIPTextEncode", text="a dog", clip=["4", 1]),
        "3": node("KSampler", seed=11, steps=20, cfg=7.0, sampler_name="euler",
                  scheduler="normal", denoise=1.0, model=["4", 0],
                  positive=["6", 0], negative=["7", 0], latent_image=["5", 0]),
    }
    assert WorkflowTrace.extract_prompts(g) == {"positive": "a cat", "negative": "a dog"}
    assert WorkflowTrace.extract_sampling(g) == {
        "steps": 20, "cfg": 7.0, "sampler_name": "euler",
        "scheduler": "normal", "denoise": 1.0}
    assert WorkflowTrace.extract_seed(g) == 11


def test_ksampler_zeroed_negative_is_empty():
    g = {
        "6": node("CLIPTextEncode", text="a cat", clip=["4", 1]),
        "7": node("ConditioningZeroOut", conditioning=["6", 0]),
        "3": node("KSampler", seed=1, steps=8, cfg=1.0, sampler_name="euler",
                  scheduler="simple", denoise=1.0, positive=["6", 0],
                  negative=["7", 0]),
    }
    assert WorkflowTrace.extract_prompts(g) == {"positive": "a cat", "negative": ""}


def test_ksampler_base_plus_refiner_prefers_base():
    g = {
        "10": node("KSamplerAdvanced", "Refiner", noise_seed=2, steps=30, cfg=5.0,
                   sampler_name="euler", scheduler="normal", start_at_step=24,
                   end_at_step=30, positive=["21", 0], negative=["22", 0]),
        "11": node("KSamplerAdvanced", "Base", noise_seed=1, steps=30, cfg=7.0,
                   sampler_name="dpmpp_2m", scheduler="karras", start_at_step=0,
                   end_at_step=24, positive=["31", 0], negative=["32", 0]),
        "21": node("CLIPTextEncodeSDXLRefiner", text="refiner pos", ascore=6.0),
        "22": node("CLIPTextEncodeSDXLRefiner", text="refiner neg", ascore=2.5),
        "31": node("CLIPTextEncode", text="base pos"),
        "32": node("CLIPTextEncode", text="base neg"),
    }
    assert WorkflowTrace.extract_prompts(g) == {"positive": "base pos", "negative": "base neg"}
    assert WorkflowTrace.extract_sampling(g)["cfg"] == 7.0
    assert WorkflowTrace.extract_seed(g) == 1


def test_ksampler_pipe_selector_and_concat():
    g = {
        "1": node("PrimitiveString", value="masterpiece"),
        "2": node("PrimitiveString", value="a fox"),
        "3": node("StringConcatenate", string_a=["1", 0], string_b=["2", 0],
                  delimiter=", "),
        "4": node("CLIPTextEncode", text=["3", 0]),
        "5": node("CLIPTextEncode", text="bad hands"),
        "6": node("ToBasicPipe", positive=["4", 0], negative=["5", 0], model=["9", 0]),
        "7": node("FromBasicPipe", basic_pipe=["6", 0]),
        "8": node("Seed (rgthree)", seed=555),
        "12": node("KSampler Config (rgthree)", steps_total=25, cfg=6.0,
                   sampler_name="dpmpp_2m", scheduler="karras"),
        "9": node("KSampler", seed=["8", 0], steps=30, cfg=["12", 0],
                  sampler_name=["12", 0], scheduler=["12", 0], denoise=1.0,
                  positive=["7", 1], negative=["7", 2]),
    }
    assert WorkflowTrace.extract_prompts(g) == {"positive": "masterpiece, a fox",
                                                "negative": "bad hands"}
    params = WorkflowTrace.extract_sampling(g)
    assert params["cfg"] == 6.0 and params["sampler_name"] == "dpmpp_2m"
    assert params["scheduler"] == "karras"
    assert WorkflowTrace.extract_seed(g) == 555


# ------------------------------------------- Civitai Prep end to end (synthetic)

def _png_with_prompt(path, graph, size=(64, 96)):
    info = PngInfo()
    info.add_text("prompt", json.dumps(graph))
    Image.new("RGB", size, (40, 40, 40)).save(path, pnginfo=info)


def _quiet_prep(models_dir, cache_path):
    with contextlib.redirect_stdout(io.StringIO()):
        return CivitaiPrep(None, str(models_dir), cache_path=str(cache_path),
                           api_lookup=False)


def test_rgthree_lora_stack_resources():
    g = krea2_graph()
    g["284"]["inputs"].update(lora_01="style\\filmGrain.safetensors", strength_01=0.65,
                              lora_02="None", lora_03="detailTweaker.safetensors",
                              strength_03=1.2)
    res = WorkflowResources.extract(g)
    assert res["loras"] == {"style\\filmGrain.safetensors": 0.65,
                            "detailTweaker.safetensors": 1.2}
    assert res["checkpoints"] == ["krea2Turbo.safetensors"]
    assert res["vaes"] == ["qwen_image_vae.safetensors"]


def test_civitai_parameters_for_custom_sampler_png(tmp_path):
    models = tmp_path / "models"
    (models / "loras" / "style").mkdir(parents=True)
    (models / "diffusion_models").mkdir()
    (models / "loras" / "style" / "filmGrain.safetensors").write_bytes(b"lora-a")
    (models / "loras" / "detailTweaker.safetensors").write_bytes(b"lora-b")
    (models / "diffusion_models" / "krea2Turbo.safetensors").write_bytes(b"unet")

    g = krea2_graph()
    g["284"]["inputs"].update(lora_01="style\\filmGrain.safetensors", strength_01=0.65,
                              lora_03="detailTweaker.safetensors", strength_03=1.2)
    png = tmp_path / "krea2_00001_.png"
    _png_with_prompt(png, g)

    prep = _quiet_prep(models, tmp_path / "cache.json")
    with contextlib.redirect_stdout(io.StringIO()):
        a = prep.analyze_image(str(png), compute_hashes=True)
    assert a["prompts"] == {"positive": LION, "negative": ""}
    assert a["seed"] == 556122404112518
    assert {i["name"]: i["weight"] for i in a["loras"]} == {
        "style\\filmGrain.safetensors": 0.65, "detailTweaker.safetensors": 1.2}

    text = CivitaiPrep.build_parameters(a, 64, 96)
    first, settings = text.split("\n")
    assert first == LION
    assert "Negative prompt" not in text
    assert settings.startswith("Steps: 4, Sampler: ER SDE, CFG scale: 1.0, "
                               "Seed: 556122404112518, Size: 64x96")
    assert "Model: krea2Turbo" in settings
    assert 'Lora hashes: "filmGrain: ' in settings and "detailTweaker: " in settings


# ------------------------------------------------------- the user's real file

@pytest.mark.skipif(not os.path.isfile(REAL_KREA2_PNG), reason="real KREA2 PNG not present")
def test_real_krea2_png(tmp_path):
    prep = _quiet_prep(tmp_path, tmp_path / "cache.json")
    with contextlib.redirect_stdout(io.StringIO()):
        a = prep.analyze_image(REAL_KREA2_PNG, compute_hashes=False)
    assert a["prompts"] == {"positive": LION, "negative": ""}
    assert a["params"] == {"steps": 4, "cfg": 1.0, "sampler_name": "er_sde",
                           "scheduler": "beta", "denoise": 1.0}
    assert a["seed"] == 556122404112518

    with Image.open(REAL_KREA2_PNG) as im:
        w, h = im.size
    text = CivitaiPrep.build_parameters(a, w, h)
    assert text.startswith(LION + "\n")
    assert f"Steps: 4, Sampler: ER SDE, CFG scale: 1.0, Seed: 556122404112518, Size: {w}x{h}" in text
