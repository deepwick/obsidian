import pytest

from deepwick_spec.palette import load_palette
from obsidian_run import LIVE, READING, hexcolor, obsidian, skip_reason

C = {name: value.lower() for name, value in load_palette().colors.items()}
SKIP = skip_reason()
pytestmark = pytest.mark.skipif(SKIP is not None, reason=SKIP or "")
R, L = READING, LIVE


VERSION_HELP = "Obsidian {} ran; copy obsidian-1.14.x.asar into ~/.config/obsidian or set DEEPWICK_OBSIDIAN_ASAR"


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    with obsidian(tmp_path_factory.mktemp("obsidian")) as running:
        version = running.version()
        if not version.startswith("1.14."):
            pytest.fail(VERSION_HELP.format(version), pytrace=False)
        yield running


@pytest.fixture
def reading(app):
    app.show("Welcome.md", "preview")
    return app


@pytest.fixture
def live(app):
    app.show("Welcome.md", "live")
    return app


def color(app, selector, prop="color"):
    return hexcolor(app.style(selector, prop)[prop])


def test_runs_tested_version(app):
    version = app.version()
    assert version.startswith("1.14."), VERSION_HELP.format(version)


def test_no_modal_on_launch(app):
    assert app.js("document.querySelectorAll('.modal-container').length") == 0


def test_window_is_tall_enough_to_render_the_whole_note(app):
    assert app.js("window.innerHeight") >= 1500


def test_surfaces(reading):
    assert hexcolor(reading.painted_background(f"{R} .markdown-preview-view")) == C["background"]
    assert hexcolor(reading.painted_background(".workspace-split.mod-left-split .nav-files-container")) == C["surface"]


def test_body_text(reading):
    assert color(reading, f"{R} .markdown-rendered p") == C["foreground"]


@pytest.mark.parametrize("level", ["h1", "h2", "h3"])
def test_headings_blue_bold(reading, level):
    style = reading.style(f"{R} .markdown-rendered {level}", "color", "font-weight")
    assert hexcolor(style["color"]) == C["blue"]
    assert int(style["font-weight"]) >= 700


@pytest.mark.parametrize(
    "selector", ["a.internal-link:not(.is-unresolved)", "a.internal-link.is-unresolved", "a.external-link"]
)
def test_links_orange(reading, selector):
    assert color(reading, f"{R} {selector}") == C["orange"]


def test_inline_code_orange(reading):
    assert color(reading, f"{R} :not(pre) > code") == C["orange"]


def test_code_block_background(reading):
    assert color(reading, f"{R} pre", "background-color") == C["surface"]


TOKENS = {
    "keyword": "blue", "string": "orange", "number": "sage", "function": "yellow",
    "class-name": "teal", "decorator": "yellow", "comment": "comment",
}


@pytest.mark.parametrize("token,name", TOKENS.items())
def test_reading_code_tokens(reading, token, name):
    assert color(reading, f"{R} pre .token.{token}") == C[name]


def test_reading_comments_italic(reading):
    assert reading.style(f"{R} pre .token.comment", "font-style")["font-style"] == "italic"


@pytest.mark.parametrize("kind,name", [("info", "blue"), ("warning", "yellow"), ("example", "magenta")])
def test_callouts(reading, kind, name):
    callout = f'{R} .callout[data-callout="{kind}"]'
    assert color(reading, f"{callout} .callout-title") == C[name]
    assert hexcolor(reading.style(callout, "--callout-color")["--callout-color"]) == C[name]


def test_tag(reading):
    style = reading.style(f"{R} a.tag", "color", "background-color")
    assert hexcolor(style["color"]) == C["teal"]
    assert hexcolor(style["background-color"]) == C["surface"]


def test_blockquote_comment_italic(reading):
    style = reading.style(f"{R} .markdown-rendered blockquote", "color", "font-style")
    assert hexcolor(style["color"]) == C["comment"]
    assert style["font-style"] == "italic"


def test_highlight(reading):
    assert color(reading, f"{R} mark", "background-color") == C["selection"]


def test_checked_task(reading):
    assert color(reading, f"{R} input.task-list-item-checkbox:checked", "background-color") == C["blue"]


def test_live_heading(live):
    style = live.style(f"{L} .cm-header-1:not(.cm-formatting)", "color", "font-weight")
    assert hexcolor(style["color"]) == C["blue"]
    assert int(style["font-weight"]) >= 700


def test_live_inline_code(live):
    assert color(live, f"{L} .cm-inline-code:not(.cm-formatting):not(.cm-hmd-indented-code)") == C["orange"]


def test_live_indented_code_is_not_orange(live):
    assert color(live, f"{L} .cm-hmd-indented-code") == C["foreground"]


LIVE_TOKENS = {
    "cm-keyword": "blue", "cm-string": "orange", "cm-number": "sage", "cm-def": "yellow",
    "cm-property": "lightBlue", "cm-meta": "yellow", "cm-comment": "comment",
}


@pytest.mark.parametrize("cls,name", LIVE_TOKENS.items())
def test_live_code_tokens(live, cls, name):
    assert color(live, f"{L} .HyperMD-codeblock .{cls}") == C[name]


def test_live_comments_italic(live):
    assert live.style(f"{L} .HyperMD-codeblock .cm-comment", "font-style")["font-style"] == "italic"
