"""Extract's face crop should put the face above the middle of the crop
(eyes toward the upper third), not below it."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sorter")))

from PIL import Image  # noqa: E402

from sorters.image_extractor import ImageExtractorSorter  # noqa: E402

FACE = (900, 900, 1100, 1100)   # 200 px face, centred in a 2000 px page


class FakeDetector:
    available = True

    def detect(self, img):
        return [FACE + (0.9,)]


class StubUpscaler:
    scale = 2

    def load(self):
        pass

    def upscale(self, img):
        return img.resize((img.width * 2, img.height * 2), Image.NEAREST)


def _page():
    img = Image.new("RGB", (2000, 2000), "white")
    img.paste((255, 0, 0), FACE)
    return img


def _face_centre_fraction(crop):
    px = crop.load()
    rows = [y for y in range(crop.height) for x in range(0, crop.width, 8)
            if px[x, y][0] > 200 and px[x, y][1] < 60]
    assert rows, "face not in crop"
    return (min(rows) + max(rows)) / 2 / crop.height


def _extractor(upscaler=None):
    ex = ImageExtractorSorter(None, crop_size=(512, 512), crop_mode="center",
                        face_zoom=2.2, upscaler=upscaler)
    ex.crop_mode = "face"
    ex._face_detector = FakeDetector()
    return ex


def test_face_sits_above_the_middle_of_the_crop():
    crop = _extractor()._face_crop(_page(), 512, 512)
    assert 0.35 <= _face_centre_fraction(crop) <= 0.45


def test_ai_zoomed_face_sits_above_the_middle_of_the_crop():
    ex = _extractor(StubUpscaler())
    crop = ex._face_crop(_page(), 512, 512)
    assert ex._ai_upscaled == 1
    assert 0.35 <= _face_centre_fraction(crop) <= 0.45
