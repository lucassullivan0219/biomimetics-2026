"""Calibrate one drag offset dCd (added to every Cd) on ONE dataset and test it on the others.

Fit set:  UIUC DA4002 5x3.75 wind tunnel at 5039 RPM (CP, points with CT > 0.03).
Test set: wind tunnel 4031 and 6045 RPM, and the static sweep.
Objective: root-mean-square relative CP error on the fit set (thrust is already within ~6 %).

Run:  uv run python sim/calibrate_dcd.py [--snel | --cs]   (about 3 min on 8 processes)
Writes sim/out/dcd_sweep.json and prints the chosen dCd.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np

import bemt
import validate_da4002 as v

HERE = Path(__file__).parent
NCRIT = 3.0
DCDS = [round(x, 4) for x in np.arange(0.0, 0.0401, 0.0025)]
FIT_RPM = 5039


def errors(job: tuple[float, bool, bool]) -> dict:
    dcd, snel, cs = job
    coords = bemt.read_airfoil(HERE / "data" / "sda1075.dat")
    polar = bemt.neuralfoil_polar(coords, HERE / "out" / f"polar_sda1075_ncrit{NCRIT:g}.npz", n_crit=NCRIT)
    rotor = v.make_rotor(bemt.DragOffset(polar, dcd))
    rotor.snel = snel
    rotor.cs = cs
    out = {"dcd": dcd, "sets": {}}

    st = v.load_table(v.DATA / "da4002_5x3.75_static_1121md.txt")
    sims = [bemt.solve(rotor, 0.0, rpm) for rpm in st[:, 0]]
    ct = np.array([s["CT"] for s in sims]); cp = np.array([s["CP"] for s in sims])
    out["sets"]["static"] = summarize(ct, cp, st[:, 1], st[:, 2], np.ones(len(ct), bool))

    for f in sorted(v.DATA.glob("da4002_5x3.75_11*md_*.txt")):
        rpm = int(f.stem.split("_")[-1])
        d = v.load_table(f)
        n = rpm / 60
        sims = [bemt.solve(rotor, J * n * 2 * v.R, rpm) for J in d[:, 0]]
        ct = np.array([s["CT"] for s in sims]); cp = np.array([s["CP"] for s in sims])
        eta = np.array([s["eta"] for s in sims])
        r = summarize(ct, cp, d[:, 1], d[:, 2], d[:, 1] > 0.03)
        r["eta_max_meas"] = float(d[:, 3].max()); r["eta_max_sim"] = float(np.nanmax(eta))
        out["sets"][str(rpm)] = r
    return out


def summarize(ct, cp, ct_m, cp_m, mask) -> dict:
    ect = (ct[mask] - ct_m[mask]) / ct_m[mask] * 100
    ecp = (cp[mask] - cp_m[mask]) / cp_m[mask] * 100
    return {"CT_mean": float(ect.mean()), "CP_mean": float(ecp.mean()),
            "CT_rms": float(np.sqrt((ect ** 2).mean())), "CP_rms": float(np.sqrt((ecp ** 2).mean()))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snel", action="store_true", help="with Snel stall delay (factor capped at 1)")
    ap.add_argument("--cs", action="store_true", help="with Corrigan-Schillings stall delay (n 1, from 6 deg)")
    args = ap.parse_args()
    with ProcessPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(errors, [(d, args.snel, args.cs) for d in DCDS]))
    best = min(rows, key=lambda r: r["sets"][str(FIT_RPM)]["CP_rms"])
    res = {"run_date": date.today().isoformat(), "n_crit": NCRIT, "snel": args.snel, "cs": args.cs, "fit_set": f"{FIT_RPM} RPM wind tunnel CP rms",
           "chosen_dcd": best["dcd"], "rows": rows}
    (HERE / "out" / ("dcd_sweep_snel.json" if args.snel else "dcd_sweep_cs.json" if args.cs else "dcd_sweep.json")).write_text(json.dumps(res, indent=1))
    print("dCd    | fit 5039 CT/CP rms | 4031 CT/CP mean | 6045 CT/CP mean | static CT/CP mean")
    for r in rows:
        s = r["sets"]
        print(f"{r['dcd']:.4f} | {s['5039']['CT_rms']:5.1f} {s['5039']['CP_rms']:5.1f} | {s['4031']['CT_mean']:+5.1f} {s['4031']['CP_mean']:+5.1f} | "
              f"{s['6045']['CT_mean']:+5.1f} {s['6045']['CP_mean']:+5.1f} | {s['static']['CT_mean']:+5.1f} {s['static']['CP_mean']:+5.1f}")
    print("chosen dCd =", best["dcd"])


if __name__ == "__main__":
    main()
