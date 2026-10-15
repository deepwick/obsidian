"""Run Obsidian off-screen (workspace tools/vshot) with an isolated profile and drive it over CDP."""

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from deepwick_spec.cdp import CDPSession, connect

REPO = Path(__file__).resolve().parents[1]
WS = REPO.parent
VSHOT = WS / "tools" / "vshot"
FIXTURE = Path(__file__).with_name("vault")
VAULT_ID = "decafbaddecafbad"
READING = ".workspace-leaf.mod-active .markdown-reading-view"
LIVE = ".workspace-leaf.mod-active .markdown-source-view.is-live-preview"
_ASAR = re.compile(r"obsidian-(\d+(?:\.\d+)*)\.asar")
_RGB = re.compile(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)")
_CRASHERS = re.compile(r"obsidian|electron|chrome|kwin|spectacle", re.I)


def hexcolor(css: str) -> str:
    css = css.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", css):
        return css.lower()
    match = _RGB.fullmatch(css)
    if not match:
        raise ValueError(f"not an rgb() color: {css!r}")
    r, g, b, alpha = match.groups()
    out = "#%02x%02x%02x" % (int(r), int(g), int(b))
    return out if alpha is None or float(alpha) == 1 else f"{out}/{alpha}"


def _is_appimage(path: Path) -> bool:
    with path.open("rb") as f:
        f.seek(8)
        return f.read(3) == b"AI\x02"


def _extract(appimage: Path) -> Path:
    dest = WS / ".shot" / "obsidian-app" / str(int(appimage.stat().st_mtime))
    binary = dest / "squashfs-root" / "obsidian"
    if binary.is_file():
        return binary
    tmp = dest.with_name(dest.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    subprocess.run([str(appimage), "--appimage-extract"], cwd=tmp, check=True, capture_output=True, timeout=600)
    shutil.rmtree(dest, ignore_errors=True)
    tmp.rename(dest)
    return binary


def find_obsidian() -> Path | None:
    raw = os.environ.get("DEEPWICK_OBSIDIAN") or shutil.which("obsidian")
    if not raw:
        return None
    path = Path(raw).resolve()
    if not path.is_file():
        return None
    return _extract(path) if _is_appimage(path) else path


def find_asar() -> Path | None:
    if raw := os.environ.get("DEEPWICK_OBSIDIAN_ASAR"):
        return Path(raw)
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "obsidian"
    found = []
    for path in config.glob("obsidian-*.asar"):
        if match := _ASAR.fullmatch(path.name):
            found.append((tuple(int(part) for part in match.group(1).split(".")), path))
    return max(found)[1] if found else None


def skip_reason() -> str | None:
    if not VSHOT.is_file():
        return "needs the workspace's tools/vshot"
    for tool in ("kwin_wayland", "spectacle", "dbus-run-session"):
        if not shutil.which(tool):
            return f"needs {tool}"
    if not (os.environ.get("DEEPWICK_OBSIDIAN") or shutil.which("obsidian")):
        return "needs Obsidian (put it on PATH or set DEEPWICK_OBSIDIAN)"
    return None


def build_profile(base: Path, *, theme: bool, scheme: str, size: tuple[int, int]) -> Path:
    config = base / "config" / "obsidian"
    config.mkdir(parents=True)
    if asar := find_asar():
        shutil.copy2(asar, config / asar.name)
    vault = base / "Deepwick"
    shutil.copytree(FIXTURE, vault)
    theme_dir = vault / ".obsidian" / "themes" / "Deepwick"
    theme_dir.mkdir(parents=True)
    for name in ("theme.css", "manifest.json"):
        shutil.copy2(REPO / name, theme_dir / name)
    appearance = {"cssTheme": "Deepwick" if theme else "", "theme": scheme}
    (vault / ".obsidian" / "appearance.json").write_text(json.dumps(appearance))
    registry = {
        "vaults": {VAULT_ID: {"path": str(vault), "ts": int(time.time() * 1000), "open": True}},
        "updateDisabled": True,
    }
    (config / "obsidian.json").write_text(json.dumps(registry))
    width, height = size
    window = {"x": 0, "y": 0, "width": width, "height": height, "isMaximized": True}
    (config / f"{VAULT_ID}.json").write_text(json.dumps(window))
    return vault


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def new_coredumps(since: float) -> list[str]:
    if not shutil.which("coredumpctl"):
        return []
    out = subprocess.run(
        ["coredumpctl", "list", "--no-legend", "--no-pager", f"--since=@{int(since)}"],
        capture_output=True, text=True,
    ).stdout
    return [line for line in out.splitlines() if _CRASHERS.search(line)]


class Obsidian:
    def __init__(self, session: CDPSession):
        self.cdp = session

    def js(self, expression: str):
        return self.cdp.evaluate(expression)

    def wait(self, condition: str, timeout: float = 30) -> None:
        message = json.dumps(f"timed out waiting for {condition}")
        self.js(
            f"""new Promise((resolve, reject) => {{
              const end = Date.now() + {int(timeout * 1000)};
              const tick = () => {{
                let ok = false;
                try {{ ok = !!({condition}); }} catch (e) {{}}
                if (ok) resolve(true);
                else if (Date.now() > end) reject(new Error({message}));
                else setTimeout(tick, 100);
              }};
              tick();
            }})"""
        )

    def version(self) -> str:
        return self.js("require('electron').ipcRenderer.sendSync('version')")

    def show(self, path: str, mode: str) -> None:
        """Open path in the active leaf. mode is "preview" (reading view) or "live" (Live Preview)."""
        state = {"mode": "preview"} if mode == "preview" else {"mode": "source", "source": False}
        self.js(
            f"""(async () => {{
              const file = app.vault.getAbstractFileByPath({json.dumps(path)});
              if (!file) throw new Error('no such note: ' + {json.dumps(path)});
              const leaf = app.workspace.getLeaf(false);
              await leaf.openFile(file, {{ state: {json.dumps(state)} }});
              app.workspace.setActiveLeaf(leaf, {{ focus: true }});
            }})()"""
        )
        expected = "preview" if mode == "preview" else "source"
        self.wait(f"app.workspace.activeLeaf.view.getMode() === '{expected}'")
        self.wait(f"document.querySelector({json.dumps(READING if mode == 'preview' else LIVE)})")

    def style(self, selector: str, *props: str) -> dict[str, str]:
        self.wait(f"document.querySelector({json.dumps(selector)})")
        return self.js(
            f"""(() => {{
              const cs = getComputedStyle(document.querySelector({json.dumps(selector)}));
              return Object.fromEntries({json.dumps(list(props))}.map(p => [p, cs.getPropertyValue(p).trim()]));
            }})()"""
        )

    def painted_background(self, selector: str) -> str:
        """Background of the nearest element, from selector upward, that paints one."""
        self.wait(f"document.querySelector({json.dumps(selector)})")
        return self.js(
            f"""(() => {{
              for (let el = document.querySelector({json.dumps(selector)}); el; el = el.parentElement) {{
                const bg = getComputedStyle(el).backgroundColor;
                if (bg && bg !== 'transparent' && !/, 0\\)$/.test(bg)) return bg;
              }}
              throw new Error('no painted background above ' + {json.dumps(selector)});
            }})()"""
        )


@contextmanager
def obsidian(base: Path, *, theme=True, scheme="obsidian", size=(1280, 2400), out: Path | None = None, delay=120):
    """Yield a running Obsidian. With out, vshot screenshots it `delay` s after launch and the run ends
    on its own; without, the run is stopped (SIGTERM to vshot) when the block exits."""
    binary = find_obsidian()
    if binary is None:
        raise RuntimeError("Obsidian not found (put it on PATH or set DEEPWICK_OBSIDIAN)")
    build_profile(base, theme=theme, scheme=scheme, size=size)
    port = _free_port()
    started = time.time()
    env = {**os.environ, "SHOT_XDG": str(base), "SHOT_DELAY": str(delay), "SHOT_SIZE": f"{size[0]}x{size[1]}"}
    shot = out or base / "unused.png"
    proc = subprocess.Popen(
        [str(VSHOT), str(shot), "--", str(binary), "--no-sandbox", "--ozone-platform=wayland",
         f"--remote-debugging-port={port}"],
        env=env,
    )
    try:
        with connect(port, timeout=60) as session:
            app = Obsidian(session)
            app.wait("window.app && app.workspace && app.workspace.layoutReady", timeout=60)
            yield app
            if out is not None and time.time() - started > delay - 2:
                raise RuntimeError(f"Obsidian was not ready within {delay}s of launch; raise delay")
    finally:
        if out is None and proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=delay + 90)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    if out is not None and not out.is_file():
        raise RuntimeError(f"vshot did not write {out} (see {base}/app.log, {base}/kwin.log)")
    if dumps := new_coredumps(started):
        raise RuntimeError("the Obsidian run left coredumps:\n" + "\n".join(dumps))
