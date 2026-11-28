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
import tubercles
import validate_da4002 as v

HERE = Path(__file__).parent
OUT = HERE.parent / "site" / "bionic-rotor" / "data" / "results.json"
NCRITS = [0.5, 1, 3, 5, 9]
CHOSEN = 3
CAL_DCD = 0.0325  # from calibrate_dcd.py (BIO card on drag calibration)
POLAR_RE = 2e4  # typical mid-blade Reynolds number at 5000 RPM static


def r4(a):
    return [round(float(x), 5) for x in a]


def main() -> None:
    runs = {str(n): json.loads((HERE / "out" / f"da4002_validation_ncrit{n:g}.json").read_text()) for n in NCRITS}
    cal_key = f"{CHOSEN:g}_dcd{CAL_DCD:g}"
    runs[cal_key] = json.loads((HERE / "out" / f"da4002_validation_ncrit{CHOSEN:g}_dcd{CAL_DCD:g}.json").read_text())
    sweep = json.loads((HERE / "out" / "dcd_sweep.json").read_text())
    snel_key = f"{CHOSEN:g}_snel"
    final_key = f"{CHOSEN:g}_dcd{CAL_DCD:g}_snel"
    runs[snel_key] = json.loads((HERE / "out" / f"da4002_validation_ncrit{CHOSEN:g}_snel.json").read_text())
    runs[final_key] = json.loads((HERE / "out" / f"da4002_validation_ncrit{CHOSEN:g}_dcd{CAL_DCD:g}_snel.json").read_text())
    sweep_snel = json.loads((HERE / "out" / "dcd_sweep_snel.json").read_text())
    sweep_cs = json.loads((HERE / "out" / "dcd_sweep_cs.json").read_text())
    cs_keys = {"cs": "cs", "cs_final": f"dcd{CAL_DCD:g}_cs", "cs_n1.6": "csn1.6", "cs_aj4": "csaj4", "cs_aj8": "csaj8"}
    for k, suffix in cs_keys.items():
        runs[k] = json.loads((HERE / "out" / f"da4002_validation_ncrit{CHOSEN:g}_{suffix}.json").read_text())

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
    rotor_f = v.make_rotor(bemt.DragOffset(p3, CAL_DCD))
    rotor_f.snel = True
    s_f = bemt.solve(rotor_f, 0.0, 5000)
    rotor_c = v.make_rotor(bemt.DragOffset(p3, CAL_DCD))
    rotor_c.cs = True
    s_c = bemt.solve(rotor_c, 0.0, 5000)
    span = {
        "rpm": 5000, "V": 0,
        "r_over_R": r4([e["r"] / v.R for e in els]),
        "alpha_deg": r4([e["alpha_deg"] for e in els]),
        "re": [round(e["re"]) for e in els],
        "cl": r4([e["cl"] for e in els]),
        "cl_final": r4([e["cl"] for e in s_f["elements"]]),
        "alpha_final": r4([e["alpha_deg"] for e in s_f["elements"]]),
        "cl_cs_final": r4([e["cl"] for e in s_c["elements"]]),
        "dT_dr": r4([e["dT_dr"] for e in els]),
        "T_N": round(s["T"], 4), "CT": round(s["CT"], 5), "CP": round(s["CP"], 5),
    }

    data = {
        "generated": date.today().isoformat(),
        "tubercles": tubercle_data(p3),
        "chosen_ncrit": CHOSEN,
        "calibrated_key": cal_key,
        "calibration": sweep,
        "calibration_snel": sweep_snel,
        "calibration_cs": sweep_cs,
        "snel_key": snel_key,
        "final_key": final_key,
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


def tubercle_data(p3) -> dict:
    """Step 11 of the page: source curves, modified polars and the comparison run by tubercle_compare.py."""
    tc = json.loads((HERE / "out" / "tubercles_compare.json").read_text())
    alphas = np.arange(-6, 20.01, 0.5)
    pol = {"baseline": {}}
    cl, cd = zip(*[p3(a, POLAR_RE) for a in alphas])
    pol["baseline"] = {"cl": r4(cl), "cd": r4(cd)}
    for k in tubercles.SETTINGS:
        tp = tubercles.TuberclePolar(p3, k)
        cl, cd = zip(*[tp(a, POLAR_RE) for a in alphas])
        pol[k] = {"cl": r4(cl), "cd": r4(cd)}
    src = {"baseline": {"alpha": sorted(tubercles.BASE["cl"]), "cl": [tubercles.BASE["cl"][a] for a in sorted(tubercles.BASE["cl"])]}}
    for k, t in tubercles.SETTINGS.items():
        src[k] = {"alpha": sorted(t["cl"]), "cl": [t["cl"][a] for a in sorted(t["cl"])]}
    curves = {}
    for key, run in tc["runs"].items():
        st, s5 = run["static"], run["static5000"]
        t5 = next(t for t in run["tunnel"] if round(t["rpm"]) == 5039)
        curves[key] = {
            "static_rpm": st["rpm"], "static_T": r4(st["T"]), "static_P": r4(st["P"]),
            "J": t5["J"], "CT": r4(t5["CT"]), "CP": r4(t5["CP"]), "eta": [None if e is None else round(e, 4) for e in t5["eta"]],
            "span_r": r4(s5["r_over_R"]), "span_dT": r4(s5["dT_dr"]), "span_alpha": r4(s5["alpha"]),
        }
    return {"run_date": tc["run_date"], "settings": tc["settings"], "compare": tc["compare"],
            "polar_alpha": r4(alphas), "polars": pol, "source": src, "curves": curves}


if __name__ == "__main__":
    main()
