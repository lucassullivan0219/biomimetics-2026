"""Download the UIUC Propeller Database files for the baseline prop (DA4002 5x3.75).

Source: UIUC Propeller Data Site, Volume 2, https://m-selig.ae.illinois.edu/props/volume-2/propDB-volume-2.html
The files are not committed (see .gitignore); run `uv run python sim/fetch_uiuc.py` to get them.
"""
from pathlib import Path
from urllib.request import urlopen

BASE = "https://m-selig.ae.illinois.edu/props/volume-2/data/"
FILES = [
    "da4002_5x3.75_geom.txt",
    "da4002_5x3.75_static_1121md.txt",
    "da4002_5x3.75_1123md_4031.txt",
    "da4002_5x3.75_1124md_5039.txt",
    "da4002_5x3.75_1125md_6045.txt",
]
OUT = Path(__file__).parent / "data" / "uiuc"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        dest = OUT / name
        if dest.exists():
            print(f"have {name}")
            continue
        with urlopen(BASE + name, timeout=30) as r:
            dest.write_bytes(r.read())
        print(f"got  {name}")


if __name__ == "__main__":
    main()
