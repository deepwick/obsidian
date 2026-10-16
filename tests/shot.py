"""Write screenshot.png (1280x800) and thumbnail.png (512x288) off-screen.

Run from the repo root: PYTHONPATH=../spec python3 tests/shot.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from obsidian_run import READING, REPO, WS, obsidian  # noqa: E402


def main() -> int:
    (WS / ".shot").mkdir(exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="obsidian-shot.", dir=WS / ".shot"))
    try:
        shot = REPO / "screenshot.png"
        with obsidian(base, size=(1280, 800), out=shot, delay=30) as app:
            app.show("Welcome.md", "preview")
            app.wait(f"document.querySelector('{READING} pre .token.keyword')")
            app.js("document.activeElement && document.activeElement.blur()")
    finally:
        shutil.rmtree(base, ignore_errors=True)
    subprocess.run(
        ["magick", str(shot), "-crop", "1280x720+0+0", "+repage", "-resize", "512x288", str(REPO / "thumbnail.png")],
        check=True,
    )
    print(subprocess.run(["magick", "identify", str(shot), str(REPO / "thumbnail.png")],
                         capture_output=True, text=True, check=True).stdout, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
