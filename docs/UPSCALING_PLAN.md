# 🔍 Upscaling & Restoration Plan

**Last Updated:** September 26, 2026
**Sorter Version:** 3.5.0
**Status:** Phase 1 ✅ shipped · Phase 2 ✅ shipped · Phase 3 ⏳ later

Adds AI super-resolution to the Sorter for upscaling source material, with
restoration (faces, colorization, denoise) planned as a later phase.

---

## Decision: build on what's already installed

Two external projects were evaluated. **Neither is adopted wholesale** — the
existing ComfyUI setup already provides better upscaling than either ships.

| | nextgenUp | RAIV |
|---|---|---|
| What it is | Image/video/audio studio (Flask web app + Tauri desktop shell) | Japanese Windows image **viewer** that upscales while you browse |
| Launch | `pip install -r requirements.txt` → `python app.py` → `localhost:5000` (`setup.sh` is Mac/Linux only) | `install_support.bat` → `run_raiv.bat` |
| Code | Small, well-separated Python modules — MIT | One 764 KB file ("fully AI-coded") — MIT |
| Engine | ONNX Runtime, **hard-coded to CPU**; 5 MB `realesr-general-x4v3` | Bundled `realesrgan` / `realcugan-ncnn-vulkan.exe` |
| Reusable | `restore_engine.py`, `face_restore.py` (Phase 3) | Real-CUGAN (anime/illustration) — nothing else |

RAIV is a viewer, not a batch pipeline, so it does not fit this workflow.

### What was already on the machine

- **9 upscale models** in `ComfyUI/models/upscale_models`, all loadable:
  4x-UltraSharp, 4x-AnimeSharp, 4x_foolhardy_Remacri, remacri_original,
  4xLSDIRplusC, RealESRGAN_x4 / x4plus / x4plus_anime_6B (ESRGAN) and
  4xPurePhoto-Span (SPAN)
- **spandrel 0.4.1** — the loader ComfyUI itself uses
- **torch 2.7 + CUDA**, RTX 4060 (8 GB)
- onnxruntime 1.19 with CUDA and TensorRT providers (useful for Phase 3)

## Provenance notes

Recorded so they are not rediscovered the hard way:

- **nextgenUp's README says models are "never re-hosted"**, but `setup.sh`
  downloads the upscaler and GFPGAN from `huggingface.co/OwlMaster/AllFilesRope`,
  a third-party mirror, and several `model_store.py` URLs are community
  re-uploads. ONNX cannot execute code on load, so the risk is tampered
  weights rather than malware — still, prefer official sources.
- **RAIV's `.exe` files** arrive prebuilt through a third-party repo and
  cannot be verified against upstream. For Real-CUGAN, use nihui's official
  releases.
- **RAIV's `install_pyw_association.bat` edits the registry** (per-user `.pyw`
  association). Harmless but persistent. Its installer also pulls
  `novelai-sdk`, which is not needed.

---

## Measurements (RTX 4060, 8 GB)

### Speed per model — 525×768 → 2100×3072

| Model | Time | Peak VRAM |
|---|---|---|
| 4x-UltraSharp | 1.62 s | 3.1 GB |
| RealESRGAN_x4plus | 1.58 s | 3.1 GB |
| 4xPurePhoto-Span | **0.09 s** | 0.7 GB |

### Tile size — full 1183×1632 magazine page, 4x-UltraSharp

| Tile | Time | Peak VRAM |
|---|---|---|
| 256 | 8.75 s | 0.66 GB |
| **512** | **8.88 s** | 2.29 GB |
| 768 | 23.3 s | 4.82 GB |
| 1024 | 24.0 s | 8.29 GB |

### ⚠️ Windows does not report out-of-memory — it slows down

On Windows the NVIDIA driver moves an oversized tile into shared system RAM
instead of raising an error. There is no warning, just a job running 2–3×
slower. A reactive "shrink the tile on out-of-memory" strategy therefore never
fires. The tile is chosen **up front** from the VRAM that is free at the time:

| Other apps hold | fixed 512 px | 256 px | auto (shipped) |
|---|---|---|---|
| 0 GB | 8.6 s | 8.8 s | 8.6 s (512) |
| 3.0 GB | **16.0 s** | 9.3 s | 9.9 s (384) |
| 4.5 GB | **19.4 s** | 8.8 s | 9.3 s (256) |

The driver starts spilling well before free VRAM runs out (512 px spilled at
~59 % of free), so the budget is set at 40 %. The trade-off is lopsided: a
smaller tile costs ~2 %, a spilling one ~2×. This matters in practice —
**running an upscale while ComfyUI holds the card** is exactly the "others
hold 4.5 GB" row.

---

## Phase 1 — AI Upscale mode ✅

`sorter/sorters/upscaler.py`, plus a GUI mode and CLI menu option 6.

- **Target long edge** (2048 / 3072 / 4096 / custom) rather than a fixed
  multiplier. Upscales only as far as needed and lands exactly on the target;
  any overshoot is Lanczos-downscaled, which stays sharp. Images already at or
  above the target are copied unchanged.
- **Content presets** choose the model, with an ordered fallback list per
  preset so they still work with a different model collection:

  | Preset | First choice |
  |---|---|
  | General (all-round) | 4x-UltraSharp |
  | Photo (realistic) | 4xLSDIRplusC |
  | Illustration / anime | 4x-AnimeSharp |
  | Fast (draft) | 4xPurePhoto-Span |

  A specific model can override the preset.
- A second AI pass happens only when a real factor is left (≥ 2×). A
  near-miss is finished with Lanczos instead of paying for another 4×.
- **Preserves PNG metadata** (ComfyUI prompt/workflow, A1111 parameters) and
  copies `.txt` sidecars, so Civitai Prep and the metadata tools keep working
  on upscaled generations.
- PNG (lossless) or JPG q95. JPG is ~10× smaller — at 4096 px a magazine's
  worth of PNG pages runs to many gigabytes.
- Output goes to `upscaled__<size>px_<model>/` with an `_upscale_info.txt`
  manifest, matching the extractor's self-describing output.
- torch/spandrel load lazily, so GUI start-up time is unaffected.

## Phase 2 — Extract → upscale → crop ✅

The extractor gains **AI upscale when needed**. It targets the framing
problem found in 3.4: on ~150 DPI magazine scans, 95 % of Portrait face crops
at 1024 were silently widened because the faces lacked the pixels.

- Upscales **only** when a crop would otherwise be widened (or a centre crop
  would be stretched), and **only the region around the face** plus a 24 px
  margin, not the whole page — roughly 15× less work for one crop.
- Result on 21 real magazine pages at Portrait 1024:

  | | Framed wider than asked | AI-upscaled | Time |
  |---|---|---|---|
  | Without AI | 18 / 19 (95 %) | 0 | 4.9 s |
  | With AI | 5 / 19 too small, plus 3 held back on purpose (below) | 15 | 24–26 s |

### Lesson: honoring the framing exposed false face detections

With the old widening, a false detection was hidden inside a wide shot. Once
the requested framing was honored, the crop zoomed straight in on it — a hand
in a shoe ad, toy figurines on a gift page. On that sample:

| | YOLO confidence |
|---|---|
| Real faces (7) | 0.75 – 0.87 |
| False: hand, figurines | 0.39, 0.46 |

**Size did not separate them** — the hand covered 11 % of the page, the same
as a real face, while one real face covered only 3.5 %. AI zoom therefore
requires confidence ≥ 0.6 (`AI_MIN_CONFIDENCE`). Lower-confidence detections
keep the previous wide framing — no worse than before, and reported
separately in the log. The threshold comes from one magazine and is a
constant to tune as more material is processed.

The remaining 5 genuinely-too-small faces would need more than 4× of AI to
reach Portrait framing; the log recommends a wider preset or smaller crop.

---

## Phase 3 — Restoration ⏳ (later)

Port from nextgenUp (MIT), changing ONNX Runtime from
`CPUExecutionProvider` to `CUDAExecutionProvider` — a one-line change per
session, with CUDA already available.

| Tool | Model | Source to prefer | Size |
|---|---|---|---|
| Face restore | GFPGAN v1.4 (+ YuNet detect) | TencentARC official release | ~340 MB |
| Colorize | DDColor-tiny | piddnad/DDColor official | ~135 MB |
| Denoise | SCUNet | cszn/SCUNet official | ~77 MB |
| Deblur | NAFNet | opencv/deblurring_nafnet (official) | ~92 MB |

Open questions for then: whether face restoration belongs in the
extract → crop chain (restore before or after cropping), and whether
CodeFormer should be offered alongside GFPGAN (usually better on heavily
degraded faces).
