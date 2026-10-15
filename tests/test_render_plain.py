import time
from pathlib import Path

import pytest

from deepwick_spec.palette import load_palette
from obsidian_run import READING, hexcolor, obsidian, skip_reason

C = {name: value.lower() for name, value in load_palette().colors.items()}
SKIP = skip_reason()
pytestmark = pytest.mark.skipif(SKIP is not None, reason=SKIP or "")


def processes_using(path: Path) -> list[str]:
    hits = []
    for environ in Path("/proc").glob("[0-9]*/environ"):
        try:
            if str(path).encode() in environ.read_bytes():
                hits.append(environ.parent.name)
        except OSError:
            pass
    return hits


def test_without_theme_is_not_deepwick(tmp_path):
    with obsidian(tmp_path, theme=False) as app:
        app.show("Welcome.md", "preview")
        assert hexcolor(app.style(f"{READING} .markdown-rendered h1", "color")["color"]) != C["blue"]
        assert hexcolor(app.painted_background(f"{READING} .markdown-preview-view")) != C["background"]


def test_light_mode_is_not_deepwick(tmp_path):
    with obsidian(tmp_path, scheme="moonstone") as app:
        app.show("Welcome.md", "preview")
        assert app.js("document.body.classList.contains('theme-light')")
        assert hexcolor(app.painted_background(f"{READING} .markdown-preview-view")) != C["background"]
        assert hexcolor(app.style(f"{READING} .markdown-rendered h1", "color")["color"]) != C["blue"]


def test_aborted_run_leaves_nothing_behind(tmp_path):
    with pytest.raises(RuntimeError, match="boom"):
        with obsidian(tmp_path):
            raise RuntimeError("boom")
    deadline = time.monotonic() + 10
    while processes_using(tmp_path) and time.monotonic() < deadline:
        time.sleep(0.5)
    assert processes_using(tmp_path) == []
