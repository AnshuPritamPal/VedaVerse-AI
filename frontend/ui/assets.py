"""Bundled images, exposed as paths or inline data URIs.

prabhupada.jpg and krishna_arjuna.png come from the
Bhagavad-gita As It Is edition shipped with this project; iskcon_logo.svg is
the public-domain ISKCON logo from Wikimedia Commons.
"""

import base64
from functools import lru_cache
from pathlib import Path


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
EMBLEM_PATH = str(ASSETS_DIR / "krishna_arjuna.png")

_MIME_TYPES = {".jpg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml"}


@lru_cache(maxsize=None)
def data_uri(name: str) -> str:
    path = ASSETS_DIR / name
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{_MIME_TYPES[path.suffix]};base64,{encoded}"


@lru_cache(maxsize=None)
def iskcon_logo(color: str) -> str:
    """The ISKCON logo filled with a fixed colour, as a data URI for <img>."""
    svg = (ASSETS_DIR / "iskcon_logo.svg").read_text(encoding="utf-8")
    svg = svg.replace('fill="currentColor"', f'fill="{color}"', 1)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def themed_iskcon_logo(css_class: str = "") -> str:
    """Logo markup with one variant per theme; CSS shows the matching one."""
    return (
        f'<img class="{css_class} only-light" src="{iskcon_logo("#B4471B")}" alt="ISKCON logo">'
        f'<img class="{css_class} only-dark" src="{iskcon_logo("#F2A766")}" alt="ISKCON logo">'
    )
