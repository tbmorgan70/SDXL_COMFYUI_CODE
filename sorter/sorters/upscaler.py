"""
AI Upscaler — super-resolution with the models already in ComfyUI.

Models are loaded through spandrel, the same loader ComfyUI uses, so every
architecture it supports (ESRGAN, SPAN, DAT, HAT, SwinIR, OmniSR, ...) works
unchanged from models/upscale_models. Inference runs on CUDA in fp16 where
the model supports it, in tiles so a full magazine page fits in VRAM.

Tile size is chosen UP FRONT from free VRAM, not by waiting for an error: on
Windows the NVIDIA driver spills an oversized tile into shared system RAM
instead of raising out-of-memory, so the job just runs ~2.7x slower with no
warning. Measured on an RTX 4060 (8 GB) with 4x-UltraSharp on a 1183x1632
page: 512px tiles 8.9s / 2.3 GB; 768px tiles 23.3s / 4.8 GB (already spilling,
since the desktop holds part of the card); 1024px tiles 24.0s / 8.3 GB.

torch/spandrel are imported lazily: importing this module (e.g. at GUI start)
costs nothing until an upscale actually runs.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

DEFAULT_MODELS_DIR = r"D:\ComfyUI_windows_portable\ComfyUI\models\upscale_models"
MODEL_EXTENSIONS = {'.pth', '.safetensors', '.pt', '.ckpt'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff'}

# Content presets -> models to try, in order of preference. Matched by file
# stem, so the first one present in the models folder wins; this keeps the
# presets useful on machines with a different model collection.
UPSCALE_PRESETS: Dict[str, List[str]] = {
    "General (all-round)": [
        "4x-UltraSharp", "RealESRGAN_x4plus", "4x_foolhardy_Remacri",
        "remacri_original", "4xLSDIRplusC", "RealESRGAN_x4",
    ],
    "Photo (realistic)": [
        "4xLSDIRplusC", "4x_foolhardy_Remacri", "remacri_original",
        "4x-UltraSharp", "RealESRGAN_x4plus",
    ],
    "Illustration / anime": [
        "4x-AnimeSharp", "RealESRGAN_x4plus_anime_6B", "4x-UltraSharp",
    ],
    "Fast (draft)": [
        "4xPurePhoto-Span", "RealESRGAN_x4plus_anime_6B", "4x-UltraSharp",
    ],
}
DEFAULT_UPSCALE_PRESET = "General (all-round)"

# Target long-edge sizes offered in the UI
TARGET_SIZES = {
    "2048 px": 2048,
    "3072 px": 3072,
    "4096 px": 4096,
    "Custom...": "custom",
}
DEFAULT_TARGET_SIZE = "4096 px"

OUTPUT_FORMATS = {
    "PNG (lossless)": "png",
    "JPG (quality 95, ~10x smaller)": "jpg",
}


# ----------------------------------------------------------------------
# Model discovery
# ----------------------------------------------------------------------

def list_upscale_models(models_dir: str = DEFAULT_MODELS_DIR) -> List[Path]:
    """All model files in the upscale models folder (recursive)."""
    d = Path(models_dir)
    if not d.is_dir():
        return []
    return sorted((p for p in d.rglob('*')
                   if p.is_file() and p.suffix.lower() in MODEL_EXTENSIONS),
                  key=lambda p: p.name.lower())


def resolve_preset(preset: str, models_dir: str = DEFAULT_MODELS_DIR) -> Optional[Path]:
    """Model file for a content preset: its first candidate that exists,
    else any available model (a model beats no upscale), else None."""
    models = list_upscale_models(models_dir)
    by_stem = {p.stem.lower(): p for p in models}
    for cand in UPSCALE_PRESETS.get(preset, []):
        hit = by_stem.get(cand.lower())
        if hit:
            return hit
    return models[0] if models else None


# ----------------------------------------------------------------------
# Upscaler
# ----------------------------------------------------------------------

class Upscaler:
    """One loaded model, reusable across many images."""

    def __init__(self, model_path, tile: int = 512, log: Optional[Callable] = None):
        self.model_path = Path(model_path)
        self.tile = tile
        self.pad = 16                     # input-pixel overlap per tile side
        self._log = log or (lambda m: None)
        self._model = None
        self._torch = None
        self.device = None
        self.half = False
        self.scale = None
        self.arch = None

    @property
    def name(self) -> str:
        return self.model_path.stem

    def load(self):
        """Load the model onto the best device (idempotent)."""
        if self._model is not None:
            return
        try:
            import torch
            import spandrel
        except ImportError as e:
            raise RuntimeError(
                "AI upscaling needs torch and spandrel "
                "(pip install torch spandrel)") from e

        desc = spandrel.ModelLoader().load_from_file(str(self.model_path))
        if not isinstance(desc, spandrel.ImageModelDescriptor):
            raise ValueError(f"{self.model_path.name} is not an image model")

        self._torch = torch
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        desc = desc.to(self.device).eval()
        self.half = self.device == 'cuda' and bool(desc.supports_half)
        if self.half:
            desc = desc.half()
        self._model = desc
        self.scale = int(desc.scale)
        self.arch = desc.architecture.name

        where = ("GPU fp16" if self.half else "GPU fp32") if self.device == 'cuda' \
            else "CPU (slow — no CUDA GPU found)"
        self._log(f"  Upscale model: {self.model_path.name} "
                  f"({self.arch} {self.scale}x, {where})")
        if self.device == 'cuda':
            self._auto_tile()

    # Largest tile worth using: beyond 512 ESRGAN-class models get no faster,
    # and SPAN-class models gain only a few percent
    MAX_TILE = 512
    # Fraction of currently-free VRAM a tile may use. Deliberately low: the
    # Windows driver starts spilling well before free VRAM is exhausted (a
    # 512px tile spilled at ~59% of free). The trade is lopsided — a smaller
    # tile costs ~2% (256px 8.8s vs 512px 8.6s on a free card), a spilling
    # one costs ~2x (512px 19.4s vs 256px 8.8s with 4.5 GB held elsewhere).
    VRAM_BUDGET = 0.4

    def _auto_tile(self):
        """Pick the largest tile whose inference fits in free VRAM.

        Measures this model's real memory cost with two small probe tiles,
        extrapolates per-pixel, and compares against what is free right now
        — so a ComfyUI instance holding the card shrinks the tile instead of
        silently pushing every tile into system RAM.
        """
        torch = self._torch
        dtype = torch.float16 if self.half else torch.float32
        p = self.pad

        def probe(t):
            x = torch.rand(1, 3, t + 2 * p, t + 2 * p, device=self.device, dtype=dtype)
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
            base = torch.cuda.memory_allocated()
            with torch.inference_mode():
                self._model(x)
            torch.cuda.synchronize()
            used = torch.cuda.max_memory_allocated() - base
            del x
            return used

        try:
            small, large = 128, 256
            used_s, used_l = probe(small), probe(large)
            px_s, px_l = (small + 2 * p) ** 2, (large + 2 * p) ** 2
            per_px = max((used_l - used_s) / (px_l - px_s), 1.0)
            torch.cuda.empty_cache()
            free, _total = torch.cuda.mem_get_info()
            budget = self.VRAM_BUDGET * free

            chosen = 64
            for t in (512, 448, 384, 320, 256, 192, 128, 96, 64):
                if t > self.MAX_TILE:
                    continue
                estimate = used_l + per_px * ((t + 2 * p) ** 2 - px_l)
                if estimate < budget:
                    chosen = t
                    break
            self.tile = min(self.tile, chosen)
            self._log(f"  Tile size {self.tile}px "
                      f"({free / 1024**3:.1f} GB VRAM free)")
        except Exception as e:
            self._log(f"  Tile probe skipped ({e}); using {self.tile}px")

    def close(self):
        """Release the model and its VRAM."""
        if self._model is not None:
            self._model = None
            if self._torch is not None and self.device == 'cuda':
                self._torch.cuda.empty_cache()

    # --- inference ------------------------------------------------------

    def _tiled(self, arr: np.ndarray, tile: int) -> np.ndarray:
        """Run the model over an HxWx3 float32 [0,1] array in overlapping
        tiles, pasting each tile's core. Output is uint8 to keep RAM down."""
        torch = self._torch
        h, w = arr.shape[:2]
        s, pad = self.scale, self.pad
        dtype = torch.float16 if self.half else torch.float32
        src = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)   # CPU
        out = np.empty((h * s, w * s, 3), dtype=np.uint8)

        with torch.inference_mode():
            for y in range(0, h, tile):
                for x in range(0, w, tile):
                    x0, y0 = max(0, x - pad), max(0, y - pad)
                    x1, y1 = min(w, x + tile + pad), min(h, y + tile + pad)
                    t = src[:, :, y0:y1, x0:x1].to(self.device, dtype)
                    r = self._model(t)[0].float().clamp_(0, 1)
                    r = (r.permute(1, 2, 0).cpu().numpy() * 255.0 + 0.5).astype(np.uint8)

                    cx0, cy0 = (x - x0) * s, (y - y0) * s
                    cw = (min(w, x + tile) - x) * s
                    ch = (min(h, y + tile) - y) * s
                    out[y * s:y * s + ch, x * s:x * s + cw] = r[cy0:cy0 + ch, cx0:cx0 + cw]
        return out

    def _upscale_array(self, arr: np.ndarray) -> np.ndarray:
        """Tiled inference. Halving on out-of-memory is a backstop for
        drivers that do raise it; _auto_tile is the real protection."""
        torch = self._torch
        tile = self.tile
        while True:
            try:
                return self._tiled(arr, tile)
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                if tile <= 64:
                    raise
                tile //= 2
                self.tile = tile          # remember for the rest of the run
                self._log(f"  VRAM limit reached — retrying with {tile}px tiles")

    def upscale(self, img: Image.Image) -> Image.Image:
        """One pass at the model's native scale (usually 4x).
        Alpha is carried over with a Lanczos resize."""
        self.load()
        alpha = None
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            rgba = img.convert('RGBA')
            alpha = rgba.getchannel('A')
            rgb = rgba.convert('RGB')
        else:
            rgb = img.convert('RGB')

        arr = np.asarray(rgb, dtype=np.float32) / 255.0
        res = Image.fromarray(self._upscale_array(arr))
        if alpha is not None:
            res.putalpha(alpha.resize(res.size, Image.LANCZOS))
        return res

    def upscale_to(self, img: Image.Image, target_long_edge: int,
                   max_passes: int = 2) -> Tuple[Image.Image, Dict]:
        """Upscale until the long edge reaches target_long_edge, landing on
        it exactly (overshoot is Lanczos-downscaled, which stays sharp).

        Returns (image, info). info['passes'] == 0 means the source already
        met the target and was returned untouched.
        """
        info = {'passes': 0, 'lanczos_up': False,
                'source': img.size, 'result': img.size}
        if max(img.size) >= target_long_edge:
            return img, info

        self.load()
        cur = img
        if self.scale and self.scale > 1:
            while max(cur.size) < target_long_edge and info['passes'] < max_passes:
                remaining = target_long_edge / max(cur.size)
                # A second AI pass on an already-large intermediate is costly;
                # only take it when there's a real factor left to gain
                if info['passes'] > 0 and remaining < 2.0:
                    break
                cur = self.upscale(cur)
                info['passes'] += 1

        ratio = target_long_edge / max(cur.size)
        if abs(ratio - 1.0) > 1e-6:
            if ratio > 1.0:
                info['lanczos_up'] = True       # AI alone couldn't reach target
            cur = cur.resize((max(1, round(cur.width * ratio)),
                              max(1, round(cur.height * ratio))), Image.LANCZOS)
        info['result'] = cur.size
        return cur, info


# ----------------------------------------------------------------------
# Batch folder upscaling
# ----------------------------------------------------------------------

def _png_text_chunks(img: Image.Image) -> Optional[PngInfo]:
    """Carry PNG text chunks (ComfyUI prompt/workflow, A1111 parameters)
    over to the upscaled file so metadata tools still work on it."""
    texts = {k: v for k, v in img.info.items() if isinstance(v, str)}
    if not texts:
        return None
    info = PngInfo()
    for k, v in texts.items():
        info.add_text(k, v)
    return info


class UpscaleSorter:
    """Upscale every image in a folder to a target long edge."""

    def __init__(self, logger, model_path, target_long_edge: int = 4096,
                 output_dir: Optional[str] = None, output_format: str = 'png',
                 preset_label: Optional[str] = None):
        self.logger = logger
        self.target = int(target_long_edge)
        self.output_dir = output_dir
        self.output_format = output_format
        self.preset_label = preset_label
        self.upscaler = Upscaler(model_path, log=self._log)

    def _log(self, msg: str):
        if self.logger:
            self.logger.log_info(msg)
        else:
            print(msg)

    def _default_output_dir(self, source: Path) -> Path:
        return source / f"upscaled__{self.target}px_{self.upscaler.name}"

    def _save(self, img: Image.Image, src_img: Image.Image, dest: Path):
        if self.output_format == 'jpg':
            img.convert('RGB').save(dest, 'JPEG', quality=95, subsampling=0)
        else:
            img.save(dest, 'PNG', pnginfo=_png_text_chunks(src_img))

    def _write_manifest(self, out_dir: Path, source: Path, stats: Dict):
        lines = [
            "=== UPSCALE INFO ===",
            f"Source folder : {source}",
            f"Upscaled      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "--- Settings ---",
            f"Target long edge : {self.target} px",
        ]
        if self.preset_label:
            lines.append(f"Preset           : {self.preset_label}")
        lines += [
            f"Model            : {self.upscaler.model_path.name} "
            f"({self.upscaler.arch} {self.upscaler.scale}x)",
            f"Device           : {self.upscaler.device}"
            + (" fp16" if self.upscaler.half else ""),
            f"Output format    : {self.output_format.upper()}",
            "",
            "--- Results ---",
            f"Upscaled         : {stats['upscaled']}",
            f"Already large    : {stats['already_large']} (copied unchanged)",
            f"Two AI passes    : {stats['two_pass']}",
            f"Failed           : {stats['failed']}",
        ]
        (out_dir / "_upscale_info.txt").write_text("\n".join(lines) + "\n",
                                                   encoding="utf-8")

    def process_folder(self, source_dir: str, recursive: bool = False,
                       progress_callback=None) -> Dict:
        source = Path(source_dir)
        out_root = Path(self.output_dir) if self.output_dir else \
            self._default_output_dir(source)

        pattern = source.rglob('*') if recursive else source.glob('*')
        files = sorted(p for p in pattern
                       if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
                       and out_root not in p.parents)
        total = len(files)
        self._log(f"AI Upscale: {total} image(s) -> {out_root}  "
                  f"(target {self.target}px)")

        stats = {'upscaled': 0, 'already_large': 0, 'two_pass': 0, 'failed': 0}
        out_root.mkdir(parents=True, exist_ok=True)
        self.upscaler.load()

        for i, src in enumerate(files):
            if progress_callback:
                progress_callback(i, total, src.name)
            rel = src.relative_to(source)
            ext = '.jpg' if self.output_format == 'jpg' else '.png'
            dest = out_root / rel.with_suffix(ext)
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                with Image.open(src) as im:
                    im.load()
                    result, info = self.upscaler.upscale_to(im, self.target)
                    if info['passes'] == 0:
                        stats['already_large'] += 1
                        if src.suffix.lower() == ext:
                            shutil.copy2(src, dest)
                        else:
                            self._save(im, im, dest)
                    else:
                        self._save(result, im, dest)
                        stats['upscaled'] += 1
                        if info['passes'] > 1:
                            stats['two_pass'] += 1
                        self._log(f"  ✓ {rel}  {info['source'][0]}×{info['source'][1]}"
                                  f" → {info['result'][0]}×{info['result'][1]}"
                                  + (f"  ({info['passes']} passes)" if info['passes'] > 1 else ""))

                # Keep Sorter's .txt metadata sidecars with their images
                sidecar = src.with_suffix('.txt')
                if sidecar.exists():
                    shutil.copy2(sidecar, dest.with_suffix('.txt'))
            except Exception as e:
                stats['failed'] += 1
                self._log(f"  ✗ {rel}: {e}")

        if progress_callback:
            progress_callback(total, total, "")
        self._write_manifest(out_root, source, stats)
        self.upscaler.close()

        self._log(f"AI Upscale complete: {stats['upscaled']} upscaled, "
                  f"{stats['already_large']} already ≥{self.target}px, "
                  f"{stats['failed']} failed")
        return {'stats': stats, 'output_dir': str(out_root), 'total': total}
