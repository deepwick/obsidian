"""Write screenshot.png (1280x800) and thumbnail.png (512x288) off-screen.

Run from the repo root: PYTHONPATH=../spec python3 tests/shot.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from obsidian_run import READING, REPO, obsidian  # noqa: E402

BASE = Path("/tmp/deepwick/obsidian-shot")


def main() -> int:
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    shot = REPO / "screenshot.png"
    with obsidian(BASE, size=(1280, 800), out=shot, delay=30) as app:
        app.show("Welcome.md", "preview")
        app.wait(f"document.querySelector('{READING} pre .token.keyword')")
        app.js("document.activeElement && document.activeElement.blur()")
    subprocess.run(
        ["magick", str(shot), "-crop", "1280x720+0+0", "+repage", "-resize", "512x288", str(REPO / "thumbnail.png")],
        check=True,
    )
    print(subprocess.run(["magick", "identify", str(shot), str(REPO / "thumbnail.png")],
                         capture_output=True, text=True, check=True).stdout, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
