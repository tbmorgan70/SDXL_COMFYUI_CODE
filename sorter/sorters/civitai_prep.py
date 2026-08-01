"""
Civitai Prep — make Civitai recognize every resource in your images.

Phase 1 (resolve & hash): reads each image's ComfyUI workflow metadata,
identifies the checkpoint, LoRAs (including stack loaders), and VAE,
resolves them to files under the local models directory, and computes
their Civitai-compatible AutoV2 hashes (first 10 hex chars of SHA-256).
Hashes are cached persistently (civitai_hash_cache.json) keyed by
path+size+mtime; existing .civitai.info sidecars are used as free hashes.

Phase 2 (enrich): looks each hash up on Civitai's public API
(model-versions/by-hash) and caches the result as a .civitai.info sidecar
next to the model file — the same convention the ComfyUI Image Saver node
uses, so the two tools share one cache. Not-found results are remembered
so the API is never asked twice.

Phase 3 (write): rewrites each PNG with an A1111/Civitai-style
'parameters' text chunk carrying prompt, settings, Model/VAE hashes,
'Lora hashes', a 'Hashes' JSON dict, and 'Civitai resources' entries —
everything Civitai's upload parser matches resources from.
"""

import hashlib
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image
from PIL.PngImagePlugin import PngInfo

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.metadata_engine import MetadataExtractor, MetadataAnalyzer, WorkflowTrace

MODEL_EXTENSIONS = {'.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.sft'}

CIVITAI_API_BY_HASH = 'https://civitai.com/api/v1/model-versions/by-hash/{}'

# ComfyUI sampler -> Civitai/A1111 display name
# (based on civitai's constants; scheduler appended below)
CIVITAI_SAMPLER_MAP = {
    'euler_ancestral': 'Euler a', 'euler': 'Euler', 'lms': 'LMS',
    'heun': 'Heun', 'dpm_2': 'DPM2', 'dpm_2_ancestral': 'DPM2 a',
    'dpmpp_2s_ancestral': 'DPM++ 2S a', 'dpmpp_2m': 'DPM++ 2M',
    'dpmpp_sde': 'DPM++ SDE', 'dpmpp_2m_sde': 'DPM++ 2M SDE',
    'dpmpp_3m_sde': 'DPM++ 3M SDE', 'dpm_fast': 'DPM fast',
    'dpm_adaptive': 'DPM adaptive', 'ddim': 'DDIM', 'plms': 'PLMS',
    'uni_pc_bh2': 'UniPC', 'uni_pc': 'UniPC', 'lcm': 'LCM',
}


def civitai_sampler_name(sampler_name: str, scheduler: str) -> str:
    # GPU variants map to the same display name
    if sampler_name.endswith('_gpu'):
        sampler_name = sampler_name[:-4]
    name = CIVITAI_SAMPLER_MAP.get(sampler_name)
    if name is None:
        return f"{sampler_name}_{scheduler}" if scheduler and scheduler != 'normal' else (sampler_name or '')
    if scheduler == 'karras':
        name += ' Karras'
    elif scheduler == 'exponential':
        name += ' Exponential'
    return name


def http_get_json(url: str, timeout: int = 20) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SDXL-Sorter-CivitaiPrep/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise ConnectionError(f"Civitai API HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise ConnectionError(f"Civitai API unreachable: {e}")

# Workflow input keys that name a resource file
CKPT_KEYS = ('ckpt_name', 'model_name', 'checkpoint', 'base_model')
VAE_KEYS = ('vae_name',)
# Any input key containing 'lora' whose value looks like a model filename
LORA_KEY_RE = re.compile(r'lora', re.IGNORECASE)
# Strength key candidates paired to a lora key by shared numeric suffix
STRENGTH_KEY_RE = re.compile(r'(strength|weight|wt)', re.IGNORECASE)
NUM_SUFFIX_RE = re.compile(r'(\d+)\s*$')


def _looks_like_model_file(value: Any) -> bool:
    return (isinstance(value, str) and value.strip() != "" and
            Path(value).suffix.lower() in MODEL_EXTENSIONS)


def _norm_key(name: str) -> str:
    """Normalize a model name for fuzzy matching: stem, lowercase, alnum only."""
    return re.sub(r'[^a-z0-9]', '', Path(name).stem.lower())


class ModelIndex:
    """One-time recursive scan of the models directory, resolving workflow
    names (which may include subfolder prefixes) to actual files."""

    def __init__(self, models_dir: str):
        self.models_dir = Path(models_dir)
        self.by_relpath: Dict[str, Path] = {}
        self.by_stem: Dict[str, List[Path]] = {}
        self.by_norm: Dict[str, List[Path]] = {}
        self._scan()

    def _scan(self):
        if not self.models_dir.is_dir():
            return
        for f in self.models_dir.rglob('*'):
            if not f.is_file() or f.suffix.lower() not in MODEL_EXTENSIONS:
                continue
            rel = f.relative_to(self.models_dir).as_posix().lower()
            self.by_relpath[rel] = f
            self.by_stem.setdefault(f.stem.lower(), []).append(f)
            self.by_norm.setdefault(_norm_key(f.name), []).append(f)

    def resolve(self, name: str) -> Optional[Path]:
        """Resolve a workflow resource name to a model file path."""
        if not name:
            return None
        cleaned = name.replace('\\', '/').strip()

        # 1. Exact relative-path suffix match (workflow often stores 'SUB/name.safetensors')
        rel = cleaned.lower()
        for known_rel, path in self.by_relpath.items():
            if known_rel == rel or known_rel.endswith('/' + rel):
                return path

        # 2. Exact stem match
        stem = Path(cleaned).stem.lower()
        if stem in self.by_stem:
            return self.by_stem[stem][0]

        # 3. Fuzzy normalized match
        norm = _norm_key(cleaned)
        if norm and norm in self.by_norm:
            return self.by_norm[norm][0]

        # 4. Unique prefix match — filename-derived names often lack the
        #    version suffix (e.g. 'ultraRealisticByStable' vs '..._v25')
        if norm and len(norm) >= 6:
            matches = [paths[0] for key, paths in self.by_norm.items()
                       if key.startswith(norm)]
            if len(matches) == 1:
                return matches[0]

        return None

    @property
    def file_count(self) -> int:
        return len(self.by_relpath)


class HashCache:
    """Persistent AutoV2/SHA-256 cache. A file is hashed at most once;
    .civitai.info sidecars are consulted first (they already carry hashes)."""

    def __init__(self, cache_path: str):
        self.cache_path = Path(cache_path)
        try:
            self.cache: Dict[str, Dict[str, Any]] = json.loads(
                self.cache_path.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError):
            self.cache = {}
        self.dirty = False

    def _key(self, path: Path) -> str:
        st = path.stat()
        return f"{path.resolve()}|{st.st_size}|{int(st.st_mtime)}"

    def get_sha256(self, path: Path, log=None) -> Optional[str]:
        """Full SHA-256 hex for a model file (cached)."""
        try:
            key = self._key(path)
        except OSError:
            return None

        entry = self.cache.get(key)
        if entry:
            return entry['sha256']

        sha = self._from_sidecar(path)
        if sha is None:
            if log:
                log(f"  Hashing {path.name} ({path.stat().st_size / 1e9:.2f} GB)...")
            sha = self._compute(path)
            if sha is None:
                return None

        self.cache[key] = {'sha256': sha, 'name': path.name}
        self.dirty = True
        return sha

    def get_autov2(self, path: Path, log=None) -> Optional[str]:
        sha = self.get_sha256(path, log)
        return sha[:10].upper() if sha else None

    @staticmethod
    def _from_sidecar(path: Path) -> Optional[str]:
        """Read SHA256 from a .civitai.info sidecar if one exists."""
        info_path = path.with_suffix('.civitai.info')
        if not info_path.is_file():
            return None
        try:
            info = json.loads(info_path.read_text(encoding='utf-8'))
            for f in info.get('files', []):
                sha = f.get('hashes', {}).get('SHA256')
                if sha and len(sha) == 64:
                    return sha.lower()
        except Exception:
            pass
        return None

    @staticmethod
    def _compute(path: Path) -> Optional[str]:
        try:
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(1024 * 1024 * 8), b''):
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            return None

    def save(self):
        if self.dirty:
            self.cache_path.write_text(
                json.dumps(self.cache, indent=2), encoding='utf-8')
            self.dirty = False


class CivitaiLookup:
    """Phase 2: enrich a hashed model file with its Civitai listing.

    Resolution order: .civitai.info sidecar -> negative-cache -> live API.
    Successful lookups are written as .civitai.info beside the model file
    (same convention as ComfyUI-Image-Saver, so both tools share a cache);
    misses are remembered in the hash cache so the API is asked only once.
    """

    def __init__(self, hash_cache: HashCache, enabled: bool = True):
        self.hash_cache = hash_cache
        self.enabled = enabled
        self.offline = False  # trips on first connection failure

    def enrich(self, model_path: Path, autov2: str, log=None) -> Optional[Dict[str, Any]]:
        """Return {'modelName','versionName','modelVersionId','air'?} or None."""
        info = self._load_sidecar(model_path)

        if info is None and self.enabled and not self.offline:
            try:
                key = self.hash_cache._key(model_path)
            except OSError:
                key = None
            entry = self.hash_cache.cache.get(key, {}) if key else {}

            if entry.get('civitai') == 'NOT_FOUND':
                return None

            try:
                if log:
                    log(f"  Civitai lookup: {model_path.name}")
                info = http_get_json(CIVITAI_API_BY_HASH.format(autov2.upper()))
            except ConnectionError as e:
                self.offline = True
                if log:
                    log(f"  ⚠️ {e} — continuing hash-only")
                return None

            if info is None:
                if key:
                    entry['civitai'] = 'NOT_FOUND'
                    self.hash_cache.cache[key] = entry or {'civitai': 'NOT_FOUND'}
                    self.hash_cache.dirty = True
                return None

            self._save_sidecar(model_path, info, log)

        if info is None:
            return None

        result = {
            'modelName': info.get('model', {}).get('name'),
            'versionName': info.get('name'),
            'type': info.get('model', {}).get('type'),
            'modelVersionId': info.get('id'),
        }
        if 'air' in info:
            result['air'] = info['air']
        return result

    @staticmethod
    def _load_sidecar(model_path: Path) -> Optional[Dict[str, Any]]:
        info_path = model_path.with_suffix('.civitai.info')
        if not info_path.is_file():
            return None
        try:
            return json.loads(info_path.read_text(encoding='utf-8'))
        except Exception:
            return None

    @staticmethod
    def _save_sidecar(model_path: Path, info: Dict[str, Any], log=None):
        try:
            model_path.with_suffix('.civitai.info').write_text(
                json.dumps(info, indent=4), encoding='utf-8')
        except OSError as e:
            if log:
                log(f"  Could not save sidecar for {model_path.name}: {e}")


class WorkflowResources:
    """Pulls named resources (checkpoint, loras+weights, vae) out of a
    ComfyUI workflow/prompt JSON dict."""

    @staticmethod
    def extract(metadata: Dict[str, Any]) -> Dict[str, Any]:
        checkpoints: List[str] = []
        vaes: List[str] = []
        loras: Dict[str, float] = {}

        if not metadata:
            return {'checkpoints': [], 'vaes': [], 'loras': {}}

        for entry in metadata.values():
            if not isinstance(entry, dict):
                continue
            inputs = entry.get('inputs', {})
            if not isinstance(inputs, dict):
                continue

            for key in CKPT_KEYS:
                v = inputs.get(key)
                if _looks_like_model_file(v) and v not in checkpoints:
                    checkpoints.append(v)

            for key in VAE_KEYS:
                v = inputs.get(key)
                if isinstance(v, str) and v.strip() and v not in vaes:
                    vaes.append(v)

            # LoRAs: any 'lora'-ish key with a model-file value, incl. stacks
            # (lora_name, lora_name_1, lora_01, switch-guarded stacks, etc.)
            lora_fields: Dict[str, str] = {}
            for key, v in inputs.items():
                if LORA_KEY_RE.search(key) and _looks_like_model_file(v):
                    if v.lower() in ('none', 'none.safetensors'):
                        continue
                    lora_fields[key] = v

            for key, name in lora_fields.items():
                weight = WorkflowResources._find_weight(key, inputs)
                # Keep strongest weight if same lora appears twice
                if name not in loras or abs(weight) > abs(loras[name]):
                    loras[name] = weight

        return {'checkpoints': checkpoints, 'vaes': vaes, 'loras': loras}

    @staticmethod
    def _find_weight(lora_key: str, inputs: Dict[str, Any]) -> float:
        """Pair a lora field with its strength field via shared numeric suffix,
        falling back to generic strength fields, then 1.0."""
        m = NUM_SUFFIX_RE.search(lora_key)
        suffix = m.group(1) if m else None

        candidates = []
        for key, v in inputs.items():
            if not isinstance(v, (int, float)):
                continue
            if not STRENGTH_KEY_RE.search(key):
                continue
            if 'clip' in key.lower():
                continue  # prefer model strength over clip strength
            km = NUM_SUFFIX_RE.search(key)
            ksuffix = km.group(1) if km else None
            if suffix is not None and ksuffix == suffix:
                return float(v)
            if suffix is None and ksuffix is None:
                candidates.append(float(v))

        return candidates[0] if candidates else 1.0


class CivitaiPrep:
    """Phase 1: analyze a folder of images — resolve every resource to a
    local model file and produce AutoV2 hashes."""

    def __init__(self, logger, models_dir: str, cache_path: Optional[str] = None,
                 api_lookup: bool = True):
        self.logger = logger
        self.models_dir = models_dir
        self.extractor = MetadataExtractor()
        self.index = ModelIndex(models_dir)
        cache_file = cache_path or os.path.join(parent_dir, 'civitai_hash_cache.json')
        self.hash_cache = HashCache(cache_file)
        self.lookup = CivitaiLookup(self.hash_cache, enabled=api_lookup)

    def _log(self, msg: str):
        if self.logger:
            self.logger.log_info(msg)
        else:
            print(msg)

    def analyze_image(self, image_path: str, compute_hashes: bool = True,
                      enrich: bool = False) -> Dict[str, Any]:
        """Resolve, hash, and (optionally) Civitai-enrich one image's resources."""
        metadata = self.extractor.extract_single(image_path)
        resources = WorkflowResources.extract(metadata)

        # Merge workflow-traced prompts with the image's existing parameters
        # chunk (which holds runtime-generated text like Florence2 captions)
        prompts = WorkflowTrace.extract_prompts_full(metadata, image_path) \
            if metadata else {'positive': '', 'negative': ''}
        params = WorkflowTrace.extract_sampling(metadata) if metadata else {}
        seed = WorkflowTrace.extract_seed(metadata) if metadata else None

        result = {
            'image': image_path,
            'has_metadata': metadata is not None,
            'checkpoint': None,
            'vae': None,
            'loras': [],
            'embeddings': [],
            'unresolved': [],
            'prompts': prompts,
            'params': params,
            'seed': seed,
        }

        def resolve_one(name: str, kind: str, weight: Optional[float] = None):
            path = self.index.resolve(name)
            if path is None:
                result['unresolved'].append({'kind': kind, 'name': name})
                return None
            item = {'name': name, 'file': str(path), 'hash': None}
            if weight is not None:
                item['weight'] = weight
            if compute_hashes:
                item['hash'] = self.hash_cache.get_autov2(path, log=self._log)
                if item['hash'] is None:
                    result['unresolved'].append({'kind': kind, 'name': name,
                                                 'reason': 'hash failed'})
                elif enrich:
                    item['civitai'] = self.lookup.enrich(path, item['hash'], log=self._log)
            return item

        # Prefer the primary/base checkpoint (filename-hinted, refiner-aware)
        # over whichever loader happens to appear first in the workflow.
        ckpt_candidates: List[str] = []
        primary = MetadataAnalyzer.extract_primary_checkpoint(
            metadata, Path(image_path).name) if metadata else None
        if primary:
            # Workflow entries matching the primary name outrank the primary
            # string itself (they carry the exact file path + version suffix)
            primary_norm = _norm_key(primary)
            ckpt_candidates.extend(
                c for c in resources['checkpoints']
                if primary_norm and _norm_key(c).startswith(primary_norm))
            if primary not in ckpt_candidates:
                ckpt_candidates.append(primary)
        ckpt_candidates.extend(
            c for c in resources['checkpoints'] if c not in ckpt_candidates)

        for cand in ckpt_candidates:
            if self.index.resolve(cand) is not None:
                result['checkpoint'] = resolve_one(cand, 'checkpoint')
                break
        else:
            if ckpt_candidates:
                result['checkpoint'] = resolve_one(ckpt_candidates[0], 'checkpoint')
        if resources['vaes']:
            result['vae'] = resolve_one(resources['vaes'][0], 'vae')
        for name, weight in resources['loras'].items():
            item = resolve_one(name, 'lora', weight)
            if item:
                result['loras'].append(item)

        # Embeddings referenced in the prompts (embedding:name syntax)
        embed_re = re.compile(r'embedding:([^,\s\(\)\:]+)', re.IGNORECASE)
        embed_names = set()
        for ptext in (prompts.get('positive', ''), prompts.get('negative', '')):
            embed_names.update(embed_re.findall(ptext or ''))
        for name in sorted(embed_names):
            item = resolve_one(name, 'embedding')
            if item:
                result['embeddings'].append(item)

        return result

    # ------------------------------------------------------------------
    # Phase 3: parameters chunk + PNG writing
    # ------------------------------------------------------------------

    @staticmethod
    def build_parameters(analysis: Dict[str, Any], width: int, height: int) -> str:
        """Build an A1111/Civitai-style 'parameters' string from an analysis."""
        prompts = analysis.get('prompts', {})
        params = analysis.get('params', {})
        ckpt = analysis.get('checkpoint')
        vae = analysis.get('vae')
        loras = analysis.get('loras', [])

        # Linked ComfyUI inputs appear as [node_id, slot] lists — treat as absent
        def scalar(v, types=(int, float, str)):
            return v if isinstance(v, types) and not isinstance(v, bool) else None

        positive = scalar(prompts.get('positive'), (str,)) or ''
        negative = scalar(prompts.get('negative'), (str,)) or ''

        lines = [positive.strip()]
        if negative.strip():
            lines.append(f"Negative prompt: {negative.strip()}")

        fields: List[str] = []
        steps = scalar(params.get('steps'), (int, float))
        if steps is not None:
            fields.append(f"Steps: {int(steps)}")
        sampler = civitai_sampler_name(scalar(params.get('sampler_name'), (str,)) or '',
                                       scalar(params.get('scheduler'), (str,)) or '')
        if sampler:
            fields.append(f"Sampler: {sampler}")
        cfg = scalar(params.get('cfg'), (int, float))
        if cfg is not None:
            fields.append(f"CFG scale: {cfg}")
        if analysis.get('seed') is not None:
            fields.append(f"Seed: {analysis['seed']}")
        fields.append(f"Size: {width}x{height}")

        hashes: Dict[str, str] = {}
        civitai_resources: List[Dict[str, Any]] = []

        def add_resource(item: Optional[Dict[str, Any]], kind: str,
                         weight: Optional[float] = None):
            if not item or not item.get('hash'):
                return
            stem = Path(item['file']).stem
            if kind == 'model':
                fields.append(f"Model hash: {item['hash']}")
                fields.append(f"Model: {stem}")
                hashes['model'] = item['hash']
            elif kind == 'vae':
                fields.append(f"VAE hash: {item['hash']}")
                fields.append(f"VAE: {stem}")
                hashes['vae'] = item['hash']
            elif kind == 'lora':
                hashes[f"lora:{stem}"] = item['hash']
            elif kind == 'embed':
                hashes[f"embed:{stem}"] = item['hash']

            info = item.get('civitai')
            if info and info.get('modelVersionId'):
                res: Dict[str, Any] = {
                    'modelName': info.get('modelName'),
                    'versionName': info.get('versionName'),
                }
                if weight is not None:
                    res['weight'] = weight
                if info.get('air'):
                    res['air'] = info['air']
                else:
                    res['modelVersionId'] = info['modelVersionId']
                civitai_resources.append(res)

        add_resource(ckpt, 'model')
        add_resource(vae, 'vae')
        for item in loras:
            add_resource(item, 'lora', item.get('weight'))
        for item in analysis.get('embeddings', []):
            add_resource(item, 'embed')

        lora_hashes = ", ".join(
            f"{Path(i['file']).stem}: {i['hash']}" for i in loras if i.get('hash'))
        if lora_hashes:
            fields.append(f'Lora hashes: "{lora_hashes}"')
        if hashes:
            fields.append(f"Hashes: {json.dumps(hashes)}")
        if civitai_resources:
            fields.append(f"Civitai resources: {json.dumps(civitai_resources)}")

        lines.append(", ".join(fields))
        return "\n".join(lines)

    def write_png(self, image_path: str, out_path: str, params_text: str,
                  clean_level: str = 'keep') -> bool:
        """Rewrite a PNG with the Civitai parameters chunk.

        clean_level: 'keep' preserves existing text chunks (workflow/prompt);
                     'strip' keeps ONLY the new parameters chunk.
        """
        try:
            with Image.open(image_path) as img:
                img.load()
                pnginfo = PngInfo()
                if clean_level == 'keep':
                    for key, value in img.info.items():
                        if key == 'parameters' or not isinstance(value, str):
                            continue
                        pnginfo.add_text(key, value)
                pnginfo.add_text('parameters', params_text)
                img.save(out_path, format='PNG', pnginfo=pnginfo)
            return True
        except Exception as e:
            self._log(f"  ✗ Write failed for {Path(image_path).name}: {e}")
            return False

    def process_folder(self, source_dir: str, in_place: bool = False,
                       clean_level: str = 'keep', enrich: bool = True,
                       progress_callback=None) -> Dict[str, Any]:
        """Phase 3 batch: analyze every PNG and write Civitai-ready copies.

        Default writes copies into <source>/civitai_ready/ ; in_place=True
        rewrites originals (atomic per file via temp + replace).
        """
        source = Path(source_dir)
        png_files = sorted(source.glob('*.png'))
        total = len(png_files)

        out_dir = source if in_place else source / 'civitai_ready'
        out_dir.mkdir(exist_ok=True)

        self._log(f"Civitai Prep: processing {total} PNGs -> "
                  f"{'in place' if in_place else str(out_dir)}  "
                  f"(clean={clean_level}, api={'on' if enrich else 'off'})")

        stats = {'written': 0, 'skipped_no_metadata': 0, 'failed': 0,
                 'resources_linked': 0}
        unresolved_names: Dict[str, str] = {}

        for i, png in enumerate(png_files):
            if progress_callback:
                progress_callback(i, total, png.name)

            analysis = self.analyze_image(str(png), compute_hashes=True,
                                          enrich=enrich)
            for u in analysis['unresolved']:
                unresolved_names[u['name']] = u['kind']

            if not analysis['has_metadata']:
                stats['skipped_no_metadata'] += 1
                continue

            with Image.open(png) as im:
                w, h = im.size
            params_text = self.build_parameters(analysis, w, h)

            if in_place:
                tmp = png.with_suffix('.png.tmp')
                ok = self.write_png(str(png), str(tmp), params_text, clean_level)
                if ok:
                    os.replace(tmp, png)
                else:
                    tmp.unlink(missing_ok=True)
            else:
                ok = self.write_png(str(png), str(out_dir / png.name),
                                    params_text, clean_level)

            if ok:
                stats['written'] += 1
                n_linked = sum(1 for item in
                               ([analysis['checkpoint'], analysis['vae']]
                                + analysis['loras'] + analysis['embeddings'])
                               if item and item.get('hash'))
                stats['resources_linked'] += n_linked
            else:
                stats['failed'] += 1

        self.hash_cache.save()
        if progress_callback:
            progress_callback(total, total, "")

        self._log(f"Civitai Prep complete: {stats['written']}/{total} written, "
                  f"{stats['resources_linked']} resource links embedded, "
                  f"{len(unresolved_names)} unresolved resource(s)")
        for name, kind in unresolved_names.items():
            self._log(f"  ⚠️ unresolved {kind}: {name}")

        return {'stats': stats, 'unresolved': unresolved_names,
                'output_dir': str(out_dir)}

    def analyze_folder(self, source_dir: str, compute_hashes: bool = True,
                       progress_callback=None) -> Dict[str, Any]:
        """Analyze all PNGs in a folder. Returns per-image results + summary."""
        png_files = sorted(Path(source_dir).glob('*.png'))
        total = len(png_files)
        self._log(f"Civitai Prep: {total} PNGs, model index has "
                  f"{self.index.file_count} files under {self.models_dir}")

        results = []
        unresolved_names = {}
        for i, png in enumerate(png_files):
            if progress_callback:
                progress_callback(i, total, png.name)
            res = self.analyze_image(str(png), compute_hashes=compute_hashes)
            results.append(res)
            for u in res['unresolved']:
                unresolved_names[u['name']] = u['kind']

        self.hash_cache.save()
        if progress_callback:
            progress_callback(total, total, "")

        resolved_imgs = sum(1 for r in results
                            if r['has_metadata'] and not r['unresolved'])
        summary = {
            'total_images': total,
            'images_fully_resolved': resolved_imgs,
            'images_with_metadata': sum(1 for r in results if r['has_metadata']),
            'unresolved_resources': unresolved_names,
        }
        self._log(f"Civitai Prep: {resolved_imgs}/{total} images fully resolved; "
                  f"{len(unresolved_names)} distinct unresolved resource(s)")
        return {'results': results, 'summary': summary}


if __name__ == '__main__':
    # Standalone run: python civitai_prep.py <image_folder> [models_dir]
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('models', nargs='?',
                    default=r'D:\ComfyUI_windows_portable\ComfyUI\models')
    ap.add_argument('--no-hash', action='store_true', help='analysis only, skip hashing')
    ap.add_argument('--analyze-only', action='store_true', help='report, do not write PNGs')
    ap.add_argument('--no-api', action='store_true', help='skip Civitai API enrichment')
    ap.add_argument('--in-place', action='store_true', help='rewrite originals instead of civitai_ready/ copies')
    ap.add_argument('--strip', action='store_true', help='drop workflow JSON, keep only parameters chunk')
    args = ap.parse_args()

    prep = CivitaiPrep(None, args.models, api_lookup=not args.no_api)
    if args.analyze_only or args.no_hash:
        report = prep.analyze_folder(args.source, compute_hashes=not args.no_hash)
        print(json.dumps(report['summary'], indent=2))
        for r in report['results'][:5]:
            print(json.dumps(r, indent=2))
    else:
        report = prep.process_folder(
            args.source,
            in_place=args.in_place,
            clean_level='strip' if args.strip else 'keep',
            enrich=not args.no_api,
        )
        print(json.dumps(report, indent=2))
