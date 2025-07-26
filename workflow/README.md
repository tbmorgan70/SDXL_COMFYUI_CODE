
# 💥 THIS IS A WORK IN PROGRESS.🚀






# 💥 ultra_post_pipeline_v1.0  (ComfyUI Workflow)

July 2025 | **ComfyUI Core:** 0.3.26+

**ultra_post_pipeline_v1.0**


## 🚀 Overview

- Easy to use control panel
- Modular design for easy customization
- Built in randomization to boost creativity
- Pipeline construction to eliminate noodles
- Load Image Batch from Dir module for automating img2img
- Preview image nodes throughout the workflow
- Aesthetic post processing module
- Versitile LoRA stack
- Face and Hand Detailers
- Two upscaling options - ComfyUI_UltimateSDUpscale and "Up by Model"

## 🧱 Core Features

Ultra_post_pipeline_v1.0 was built around my creative process and the things I like to use when making art. My style is more about easy iteration with changing variables and than perfecting the ultimate prompt. I added the modules as I learned ComfyUI and Stable Diffusion. You can increment  or randomize checkpoints, LoRAs, VAEs and even upscale models. You can move things around in the pipeline. You can load up the que and leave it going. I'm already thinking about the next module.

I've also created prompt builders for randomizing customized prompt sections revolving around my current project. There's a generic version that can be easily customized (super easy with VSC) that has 10 prompt categories and 2 toggle switches for limitless variation. I've also built a sorting ultility for sorting, renaming and extracting the metadata in bulk from image folders.

I've tried to make this as intuitive as possible, and laid out in a way that is easy to troubleshoot.

Everything I work on is work in progress, I am already working ther module and some tweaks on Ultra_post_pipeline_v1.0.

Thanks for checking this out!

Below   the modules and the details of the process

	START HERE
    LORA STACK
    CONDITIONING
    SAMPLERS
    DETAILERS
    UPSCALE
    
    Optional set ups:
    Load text from file
    Load Image from directory
    Post Processing
    
   
   *
    
    
    *













### 🧠 Conditioning

- SDXL base + Refiner checkpoints
- Multi-stage prompt encoding:
  - Main positive/negative
  - Refiner positive/negative
  - Negative hardcoded for quality control

### 🧬 LoRA Stack

Up to **5 layered LoRA applications**:

1. **Style LoRA** – e.g., `ck-70s-scifi-IL`
2. **Detailer LoRA** – e.g., `WowifierXL`, `perfection style`
3. **Body Mod LoRA** – e.g., `Ass slider`, `EnvyZoom`
4. **Character LoRA** – e.g., `Dollskill_Sci_Fi_Babe`
5. **Base enhancement LoRA** – e.g., `illustrious_quality_modifiers`

### 👁️‍🗨️ Detailer System

- Two `FaceDetailer` nodes:
  - First pass: Face detail & retouch
  - Second pass: Hands + optional inpainting
- Uses `Ultralytics YOLOv8` detectors + `SAM` masks

### 🖼️ Post Processing

Custom fx stack (opt-in with reroutes):

- `ChromaticAberration`
- `Glow`
- `Sepia Tint`
- `Sharpen`, `Blur`, `Quantize`, `FilmGrain`

### 🧙‍♂️ Upscaling Modes

1. **UltimateSDUpscale** – tiled, seamless, artifact-free
2. **VAE + RealESRGAN** – anime-style crisp pass
3. Selectable via modular reroute nodes

---

## 📁 Directory Requirements

- 📂 `PROMPTS/ultra_fusion_prompts.txt`: your line-separated prompt file
- 📂 Source images directory (user-defined in loader node)
- Output images auto-save with descriptive prefixes

---

## 🛠️ Add-on Packs Required

Ensure these node packs are installed for full functionality:

- `comfyui-inspire-pack`
- `comfyui-impact-pack` & `subpack`
- `comfyui-post-processing-nodes`
- `was-node-suite-comfyui`
- `comfyui_ultimatesdupscale`
- `cg-use-everywhere` (for advanced pipes and reroutes)

---

## 🧠 Use Tips

- 🔁 Set `image_load_cap` and `start_index` in loader for controlled batching
- 🎛️ All LoRA strengths are adjustable via sliders
- 💾 Toggle or bypass reroutes for post-processing experiments
- 📦 Export pipeline with `SaveImage` or just Preview in-place

---

## 🧠 Author Notes




## 📸 Sample Projects

- `Nova Skyrift` — glitch-futurist neon synth-goth series
- `Disco Dollz` — retro-femme synthetic icon studies
