"""3.7.3: favourite crop sizes and a chosen output folder in the crop editor."""
from test_crop_editor import key, loaded, make_editor, png, pump, root  # noqa: F401

from sorters.crop_tool import (CROP_SIZE_PRESETS, DEFAULT_CROP_PRESET, FAVORITES_DIVIDER,
                               load_favorites, preset_menu_values, save_favorites,
                               step_preset)

SIZED = [k for k, v in CROP_SIZE_PRESETS.items() if isinstance(v, tuple)]
PORTRAIT = next(k for k in SIZED if CROP_SIZE_PRESETS[k][1] > CROP_SIZE_PRESETS[k][0])


# ---------------------------------------------------------------- crop_tool

def test_favorites_load_save_round_trip(tmp_path):
    path = tmp_path / "f.json"
    assert load_favorites(path) == []
    save_favorites(path, [DEFAULT_CROP_PRESET, "Custom 1200×1500"])
    assert load_favorites(path) == [DEFAULT_CROP_PRESET, "Custom 1200×1500"]


def test_favorites_ignore_bad_file_and_unknown_labels(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert load_favorites(bad) == []
    odd = tmp_path / "odd.json"
    odd.write_text('["nope", 5, "%s"]' % DEFAULT_CROP_PRESET, encoding="utf-8")
    assert load_favorites(odd) == [DEFAULT_CROP_PRESET]


def test_menu_values_put_favorites_first():
    labels = list(CROP_SIZE_PRESETS)
    assert preset_menu_values(labels, []) == labels
    out = preset_menu_values(labels, [labels[3]])
    assert out[:2] == ["★ " + labels[3], FAVORITES_DIVIDER]
    assert out[2:] == labels


# ---------------------------------------------------------------- editor

def test_output_root_puts_crops_in_chosen_folder(root, make_editor, tmp_path):
    out = tmp_path / "out"
    ed, rec = make_editor(output_root=out)
    loaded(root, ed, png(tmp_path / "a.png"))
    ed.save(advance=False)
    assert pump(root, lambda: len(rec.saved) == 1)
    assert rec.saved[0][1].path.parent == out / "cropped__1024x1024"
    assert not (tmp_path / "cropped__1024x1024").exists()


def test_star_adds_size_to_favorites_and_persists(root, make_editor, tmp_path):
    fav = tmp_path / "favs.json"
    ed, _ = make_editor(favorites_path=fav)
    assert ed.favorites == []
    ed.toggle_favorite()
    assert ed.favorites == [DEFAULT_CROP_PRESET]
    values = list(ed.preset_menu.cget("values"))
    assert values[0] == "★ " + DEFAULT_CROP_PRESET and values[1] == FAVORITES_DIVIDER
    assert ed.star_btn.cget("text") == "★"
    ed2, _ = make_editor(favorites_path=fav)          # remembered next time
    assert ed2.favorites == [DEFAULT_CROP_PRESET]
    ed2.toggle_favorite()                             # and removable
    assert ed2.favorites == [] and load_favorites(fav) == []
    assert FAVORITES_DIVIDER not in ed2.preset_menu.cget("values")
    assert ed2.star_btn.cget("text") == "☆"


def test_picking_a_starred_entry_or_the_divider(root, make_editor, tmp_path):
    ed, _ = make_editor(favorites_path=tmp_path / "f.json")
    ed.set_preset(PORTRAIT)
    ed.toggle_favorite()
    ed.set_preset(DEFAULT_CROP_PRESET)
    ed._on_preset_menu("★ " + PORTRAIT)
    assert ed.preset_label == PORTRAIT
    ed._on_preset_menu(FAVORITES_DIVIDER)
    assert ed.preset_label == PORTRAIT
    assert ed.preset_menu.get() == PORTRAIT


def test_tab_cycles_favorites_when_on_one(root, make_editor, tmp_path):
    a, b, c = SIZED[0], SIZED[5], SIZED[9]
    ed, _ = make_editor(favorites_path=tmp_path / "f.json")
    for label in (a, b, c):
        ed.set_preset(label)
        ed.toggle_favorite()
    ed.set_preset(a)
    seen = []
    for _ in range(3):
        ed.handle_key(key("Tab"))
        seen.append(ed.preset_label)
    assert seen == [b, c, a]
    ed.handle_key(key("Tab", 0x1))
    assert ed.preset_label == c
    ed.set_preset(SIZED[1])                            # not a favourite: the usual Tab
    ed.handle_key(key("Tab"))
    assert ed.preset_label == step_preset(ed._all_sizes(), SIZED[1], 1)


def test_s_key_stars_the_current_size(root, make_editor, tmp_path):
    ed, _ = make_editor(favorites_path=tmp_path / "f.json")
    assert ed.handle_key(key("s")) is True
    assert ed.favorites == [DEFAULT_CROP_PRESET]


def test_custom_size_favorite_comes_back(root, make_editor, tmp_path):
    fav = tmp_path / "f.json"
    save_favorites(fav, ["Custom 1200×1500"])
    ed, _ = make_editor(favorites_path=fav)
    ed._on_preset_menu("★ Custom 1200×1500")
    assert ed.out_size == (1200, 1500)
