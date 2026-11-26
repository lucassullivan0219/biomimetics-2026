"""Collect everything the public page charts into site/bionic-rotor/data/results.json.

Run after validate_da4002.py has been run for n_crit 0.5, 1, 3, 5, 9:
    uv run python sim/export_site_data.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np

import bemt
import validate_da4002 as v

HERE = Path(__file__).parent
OUT = HERE.parent / "site" / "bionic-rotor" / "data" / "results.json"
NCRITS = [0.5, 1, 3, 5, 9]
CHOSEN = 3
POLAR_RE = 2e4  # typical mid-blade Reynolds number at 5000 RPM static


def r4(a):
    return [round(float(x), 5) for x in a]


def main() -> None:
    runs = {str(n): json.loads((HERE / "out" / f"da4002_validation_ncrit{n:g}.json").read_text()) for n in NCRITS}

    g = v.load_table(v.DATA / "da4002_5x3.75_geom.txt")
    coords = bemt.read_airfoil(HERE / "data" / "sda1075.dat")

    polars = {}
    alphas = np.arange(-6, 20.01, 0.5)
    for n in (9, CHOSEN):
        p = bemt.neuralfoil_polar(coords, HERE / "out" / f"polar_sda1075_ncrit{n:g}.npz", n_crit=float(n))
        cl, cd = zip(*[p(a, POLAR_RE) for a in alphas])
        polars[str(n)] = {"alpha": r4(alphas), "cl": r4(cl), "cd": r4(cd)}

    p3 = bemt.neuralfoil_polar(coords, HERE / "out" / f"polar_sda1075_ncrit{CHOSEN:g}.npz", n_crit=float(CHOSEN))
    rotor = v.make_rotor(p3)
    s = bemt.solve(rotor, 0.0, 5000)
    els = s["elements"]
    span = {
        "rpm": 5000, "V": 0,
        "r_over_R": r4([e["r"] / v.R for e in els]),
        "alpha_deg": r4([e["alpha_deg"] for e in els]),
        "re": [round(e["re"]) for e in els],
        "cl": r4([e["cl"] for e in els]),
        "dT_dr": r4([e["dT_dr"] for e in els]),
        "T_N": round(s["T"], 4), "CT": round(s["CT"], 5), "CP": round(s["CP"], 5),
    }

    data = {
        "generated": date.today().isoformat(),
        "chosen_ncrit": CHOSEN,
        "polar_re": POLAR_RE,
        "geometry": {"r_over_R": r4(g[:, 0]), "c_over_R": r4(g[:, 1]), "beta_deg": r4(g[:, 2])},
        "airfoil": {"x": r4(coords[:, 0]), "y": r4(coords[:, 1])},
        "polars": polars,
        "spanwise": span,
        "runs": runs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size/1024:.1f} KB); static 5000 RPM T={span['T_N']} N CT={span['CT']}")


if __name__ == "__main__":
    main()
