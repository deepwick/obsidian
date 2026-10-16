import json

import pytest

from obsidian_run import build_profile, find_asar, hexcolor


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
    asar = tmp_path / "obsidian-1.9.14.asar"
    asar.write_bytes(b"")
    monkeypatch.setenv("DEEPWICK_OBSIDIAN_ASAR", str(asar))
    assert find_asar() == asar


@pytest.mark.parametrize("name", ["custom.asar", "obsidian-latest.asar", "missing/obsidian-1.9.14.asar"])
def test_find_asar_env_override_must_be_a_versioned_file(tmp_path, monkeypatch, name):
    path = tmp_path / name
    if "missing" not in name:
        path.write_bytes(b"")
    monkeypatch.setenv("DEEPWICK_OBSIDIAN_ASAR", str(path))
    with pytest.raises(ValueError, match=r"obsidian-X\.Y\.Z\.asar"):
        find_asar()


def test_build_profile_turns_sync_off(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPWICK_OBSIDIAN_ASAR", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "none"))
    vault = build_profile(tmp_path / "p", theme=True, scheme="obsidian", size=(800, 600))
    assert json.loads((vault / ".obsidian" / "core-plugins.json").read_text())["sync"] is False


def test_find_asar_none(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPWICK_OBSIDIAN_ASAR", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert find_asar() is None
