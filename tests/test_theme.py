import json
import re
from pathlib import Path

from deepwick_spec.palette import load_palette

REPO = Path(__file__).resolve().parents[1]
PALETTE = load_palette()
C = {name: value.lower() for name, value in PALETTE.colors.items()}

EXPECTED = {
    "--color-base-00": "background", "--color-base-05": "background",
    "--color-base-10": "surface", "--color-base-20": "surface",
    "--color-base-25": "overlay", "--color-base-30": "overlay", "--color-base-35": "overlay",
    "--color-base-40": "muted", "--color-base-50": "muted",
    "--color-base-60": "comment", "--color-base-70": "comment",
    "--color-base-100": "foreground",
    "--background-primary": "background", "--background-primary-alt": "surface",
    "--background-secondary": "surface", "--background-secondary-alt": "overlay",
    "--background-modifier-border": "overlay", "--background-modifier-border-hover": "muted",
    "--background-modifier-border-focus": "blue",
    "--background-modifier-hover": "overlay", "--background-modifier-active-hover": "overlay",
    "--background-modifier-form-field": "background",
    "--background-modifier-error": "red", "--background-modifier-success": "green",
    "--titlebar-background": "surface", "--titlebar-background-focused": "surface",
    "--tab-container-background": "surface",
    "--text-normal": "foreground", "--text-muted": "comment", "--text-faint": "muted",
    "--text-accent": "blue", "--text-accent-hover": "lightBlue",
    "--text-on-accent": "background", "--text-on-accent-inverted": "background",
    "--text-selection": "selection",
    "--text-error": "red", "--text-warning": "yellow", "--text-success": "green",
    "--caret-color": "foreground",
    "--color-accent": "blue", "--color-accent-1": "lightBlue", "--color-accent-2": "lightBlue",
    "--interactive-normal": "overlay", "--interactive-hover": "selection",
    "--interactive-accent": "blue", "--interactive-accent-hover": "lightBlue",
    "--color-red": "red", "--color-orange": "orange", "--color-yellow": "yellow",
    "--color-green": "green", "--color-cyan": "cyan", "--color-blue": "blue",
    "--color-purple": "magenta", "--color-pink": "rose",
    **{f"--h{n}-color": "blue" for n in range(1, 7)},
    "--inline-title-color": "blue",
    "--bold-color": "foreground", "--italic-color": "foreground",
    "--link-color": "orange", "--link-external-color": "orange",
    "--link-color-hover": "gold", "--link-external-color-hover": "gold",
    "--link-unresolved-color": "orange",
    "--blockquote-color": "comment", "--blockquote-border-color": "muted",
    "--hr-color": "muted", "--list-marker-color": "muted",
    "--tag-color": "teal", "--tag-color-hover": "teal",
    "--tag-background": "surface", "--tag-background-hover": "overlay",
    "--text-highlight-bg": "selection",
    "--checkbox-color": "blue", "--checkbox-color-hover": "lightBlue",
    "--checkbox-border-color": "muted", "--checkbox-marker-color": "background",
    "--table-border-color": "overlay", "--table-header-background": "surface",
    "--table-header-color": "foreground",
    "--code-background": "surface", "--code-normal": "foreground",
    "--code-keyword": "blue", "--code-function": "yellow", "--code-property": "lightBlue",
    "--code-string": "orange", "--code-value": "sage", "--code-comment": "comment",
    "--code-operator": "foreground", "--code-punctuation": "muted", "--code-tag": "blue",
    "--code-important": "rose",
    "--callout-default": "blue", "--callout-info": "blue", "--callout-todo": "blue",
    "--callout-tip": "teal", "--callout-summary": "teal", "--callout-important": "teal",
    "--callout-success": "green", "--callout-question": "gold", "--callout-warning": "yellow",
    "--callout-fail": "red", "--callout-error": "red", "--callout-bug": "red",
    "--callout-example": "magenta", "--callout-quote": "comment",
    "--graph-line": "overlay", "--graph-node": "comment", "--graph-node-focused": "blue",
    "--graph-node-tag": "teal", "--graph-node-attachment": "green",
    "--graph-node-unresolved": "muted", "--graph-text": "foreground",
}
RGB = {
    "--color-red-rgb": "red", "--color-orange-rgb": "orange", "--color-yellow-rgb": "yellow",
    "--color-green-rgb": "green", "--color-cyan-rgb": "cyan", "--color-blue-rgb": "blue",
    "--color-purple-rgb": "magenta", "--color-pink-rgb": "rose",
}
OTHER = {
    **{f"--h{n}-weight": "700" for n in range(1, 7)},
    "--inline-title-weight": "700",
    "--accent-h": "207", "--accent-s": "61%", "--accent-l": "59%",
}


def css() -> str:
    return re.sub(r"/\*.*?\*/", "", (REPO / "theme.css").read_text(encoding="utf-8"), flags=re.S)


def rules() -> list[tuple[str, str]]:
    return [(sel.strip(), body) for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css())]


def variables() -> dict[str, str]:
    blocks = [body for sel, body in rules() if sel == ".theme-dark"]
    assert len(blocks) == 1, "expected exactly one bare .theme-dark block"
    return {name: value.strip() for name, value in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", blocks[0])}


def test_manifest():
    manifest = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == {
        "name": "Deepwick",
        "version": "1.0.0",
        "minAppVersion": "1.14.0",
        "author": "Deepwick",
        "authorUrl": "https://github.com/deepwick",
    }
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])


def test_color_variables():
    v = variables()
    for name, color in EXPECTED.items():
        assert v.get(name, "").lower() == C[color], f"{name}: {v.get(name)} != {color}"


def test_rgb_variables_match_their_colors():
    v = variables()
    for name, color in RGB.items():
        r, g, b = (int(C[color][i : i + 2], 16) for i in (1, 3, 5))
        assert v.get(name) == f"{r}, {g}, {b}", f"{name}: {v.get(name)}"


def test_other_variables():
    v = variables()
    for name, value in OTHER.items():
        assert v.get(name) == value, f"{name}: {v.get(name)} != {value}"


def test_no_unexpected_variables():
    assert set(variables()) == set(EXPECTED) | set(RGB) | set(OTHER)


def test_accent_hsl_is_blue():
    r, g, b = (int(C["blue"][i : i + 2], 16) / 255 for i in (1, 3, 5))
    hi, lo = max(r, g, b), min(r, g, b)
    light = (hi + lo) / 2
    sat = (hi - lo) / (1 - abs(2 * light - 1))
    hue = 60 * (((r - g) / (hi - lo)) + 4)  # Blue's max channel is b
    assert (round(hue), round(sat * 100), round(light * 100)) == (207, 61, 59)


def test_only_dark_mode_selectors():
    for selector, _ in rules():
        for part in selector.split(","):
            assert part.strip().startswith(".theme-dark"), f"selector outside .theme-dark: {part.strip()}"


def test_store_guidelines():
    text = css()
    for banned in ("!important", "url(", "@"):
        assert banned not in text, f"theme.css contains {banned!r}"
