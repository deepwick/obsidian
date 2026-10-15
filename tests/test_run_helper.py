import pytest

from obsidian_run import find_asar, hexcolor


def test_hexcolor():
    assert hexcolor("rgb(86, 156, 214)") == "#569cd6"
    assert hexcolor("rgba(86, 156, 214, 1)") == "#569cd6"
    assert hexcolor("rgba(86, 156, 214, 0.5)") == "#569cd6/0.5"
    assert hexcolor(" #569CD6 ") == "#569cd6"
    with pytest.raises(ValueError):
        hexcolor("color(srgb 0.3 0.6 0.8)")


def test_find_asar_picks_the_newest_version(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPWICK_OBSIDIAN_ASAR", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    config = tmp_path / "obsidian"
    config.mkdir()
    for version in ("1.9.10", "1.14.4", "1.13.7"):
        (config / f"obsidian-{version}.asar").write_bytes(b"")
    (config / "obsidian-notes.asar").write_bytes(b"")
    assert find_asar() == config / "obsidian-1.14.4.asar"


def test_find_asar_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPWICK_OBSIDIAN_ASAR", str(tmp_path / "custom.asar"))
    assert find_asar() == tmp_path / "custom.asar"


def test_find_asar_none(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPWICK_OBSIDIAN_ASAR", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert find_asar() is None
