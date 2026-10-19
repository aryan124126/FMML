"""Builds hub/team_hub.html from hub/src (shell.html + styles.css + the app-*.js files, in order).

Run: python hub/build.py   (then publish hub/team_hub.html to the Team Hub artifact)
"""
from pathlib import Path

SRC = Path(__file__).parent / "src"
PARTS = ["app-core.js", "app-calendar.js", "app-review.js", "app-analytics.js", "app-more.js"]


def build() -> Path:
    shell = (SRC / "shell.html").read_text(encoding="utf-8")
    css = (SRC / "styles.css").read_text(encoding="utf-8")
    js = "\n".join(f"// ===== {name} =====\n" + (SRC / name).read_text(encoding="utf-8") for name in PARTS)
    out = Path(__file__).parent / "team_hub.html"
    out.write_text(shell.replace("/*STYLES*/", css).replace("/*APP*/", js), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build())
