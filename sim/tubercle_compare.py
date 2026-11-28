"""Compare tubercle settings with the baseline DA4002 5x3.75 at equal RPM (card BIO-20261128-1116).

Each setting is run with the current model (n_crit 3, dCd 0.0325, Snel) and the uncorrected one
(n_crit 3 only), at the UIUC static RPMs, 5000 RPM static, and the UIUC tunnel J points.
Runs in parallel processes.

Run:  uv run python sim/tubercle_compare.py
Writes sim/out/tubercles_compare.json and tubercles_compare.png.
"""
from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import bemt
import tubercles
import validate_da4002 as v

HERE = Path(__file__).parent
OUT = HERE / "out"
NCRIT = 3.0
DCD = 0.0325
MODELS = {"current": {"dcd": DCD, "snel": True}, "uncorrected": {"dcd": 0.0, "snel": False}}
SETTINGS = ["baseline", *tubercles.SETTINGS]
STATIC_RPM = 5000.0


def build(setting: str, model: str) -> bemt.Rotor:
    coords = bemt.read_airfoil(HERE / "data" / "sda1075.dat")
    p = bemt.neuralfoil_polar(coords, OUT / f"polar_sda1075_ncrit{NCRIT:g}.npz", n_crit=NCRIT)
    if setting != "baseline":
        p = tubercles.TuberclePolar(p, setting)
    m = MODELS[model]
    rotor = v.make_rotor(bemt.DragOffset(p, m["dcd"]) if m["dcd"] else p)
    rotor.snel = m["snel"]
    return rotor


def run(job: tuple[str, str]) -> dict:
    setting, model = job
    rotor = build(setting, model)
    st = v.load_table(v.DATA / "da4002_5x3.75_static_1121md.txt")
    static = [bemt.solve(rotor, 0.0, rpm) for rpm in st[:, 0]]
    s5 = bemt.solve(rotor, 0.0, STATIC_RPM)
    res = {
        "setting": setting, "model": model,
        "static": {"rpm": st[:, 0].tolist(), "T": [s["T"] for s in static], "P": [s["P"] for s in static],
                   "CT": [s["CT"] for s in static], "CP": [s["CP"] for s in static]},
        "static5000": {"T": s5["T"], "P": s5["P"], "CT": s5["CT"], "CP": s5["CP"],
                        "r_over_R": [e["r"] / v.R for e in s5["elements"]],
                        "alpha": [e["alpha_deg"] for e in s5["elements"]],
                        "cl": [e["cl"] for e in s5["elements"]], "cd": [e["cd"] for e in s5["elements"]],
                        "dT_dr": [e["dT_dr"] for e in s5["elements"]]},
        "tunnel": [],
    }
    for f in sorted(v.DATA.glob("da4002_5x3.75_11*md_*.txt")):
        rpm = float(f.stem.split("_")[-1])
        d = v.load_table(f)
        n = rpm / 60
        sims = [bemt.solve(rotor, J * n * 2 * v.R, rpm) for J in d[:, 0]]
        res["tunnel"].append({
            "rpm": rpm, "J": d[:, 0].tolist(),
            "CT": [s["CT"] for s in sims], "CP": [s["CP"] for s in sims],
            "eta": [None if np.isnan(s["eta"]) else s["eta"] for s in sims],
        })
    return res


def pct(a, b) -> float:
    return float((a - b) / b * 100)


def compare(runs: dict) -> dict:
    out = {}
    for model in MODELS:
        base = runs[("baseline", model)]
        for setting in SETTINGS[1:]:
            r = runs[(setting, model)]
            row = {
                "static5000_T_pct": pct(r["static5000"]["T"], base["static5000"]["T"]),
                "static5000_P_pct": pct(r["static5000"]["P"], base["static5000"]["P"]),
                "static5000_T_N": r["static5000"]["T"], "static5000_P_W": r["static5000"]["P"],
                "base_static5000_T_N": base["static5000"]["T"], "base_static5000_P_W": base["static5000"]["P"],
                # figure of merit-like hover measure: thrust^1.5 / power, relative
                "static5000_T15_over_P_pct": pct(r["static5000"]["T"] ** 1.5 / r["static5000"]["P"],
                                                 base["static5000"]["T"] ** 1.5 / base["static5000"]["P"]),
                "static_T_pct_by_rpm": [pct(a, b) for a, b in zip(r["static"]["T"], base["static"]["T"])],
                "tunnel": [],
            }
            for tr, tb in zip(r["tunnel"], base["tunnel"]):
                ct, cb = np.array(tr["CT"]), np.array(tb["CT"])
                cp, cpb = np.array(tr["CP"]), np.array(tb["CP"])
                mask = cb > 0.03
                eta = np.array([np.nan if e is None else e for e in tr["eta"]], dtype=float)
                etab = np.array([np.nan if e is None else e for e in tb["eta"]], dtype=float)
                row["tunnel"].append({
                    "rpm": tr["rpm"],
                    "CT_pct_mean": float(np.mean((ct[mask] - cb[mask]) / cb[mask]) * 100),
                    "CT_pct_min": float(np.min((ct[mask] - cb[mask]) / cb[mask]) * 100),
                    "CP_pct_mean": float(np.mean((cp[mask] - cpb[mask]) / cpb[mask]) * 100),
                    "eta_max": float(np.nanmax(eta)), "eta_max_base": float(np.nanmax(etab)),
                    "eta_max_pct": pct(np.nanmax(eta), np.nanmax(etab)),
                })
            row["tunnel_CT_pct_mean_all"] = float(np.mean([t["CT_pct_mean"] for t in row["tunnel"]]))
            row["tunnel_CP_pct_mean_all"] = float(np.mean([t["CP_pct_mean"] for t in row["tunnel"]]))
            row["eta_max_pct_mean"] = float(np.mean([t["eta_max_pct"] for t in row["tunnel"]]))
            row["worst_thrust_pct"] = float(min([row["static5000_T_pct"], *row["static_T_pct_by_rpm"],
                                                 *[t["CT_pct_min"] for t in row["tunnel"]]]))
            row["pass_5pct_static"] = row["static5000_T_pct"] > -5
            out[f"{model}/{setting}"] = row
    return out


def plot(runs: dict, path: Path) -> None:
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    for i, model in enumerate(MODELS):
        for k, setting in enumerate(SETTINGS):
            r = runs[(setting, model)]
            ls = "-" if setting == "baseline" else "--"
            col = "k" if setting == "baseline" else f"C{k}"
            t = r["tunnel"][1]  # 5039 RPM
            ax[i, 0].plot(t["J"], t["CT"], ls, color=col, label=setting)
            ax[i, 1].plot(t["J"], t["CP"], ls, color=col)
            ax[i, 2].plot(t["J"], [np.nan if e is None else e for e in t["eta"]], ls, color=col)
        ax[i, 0].set(title=f"{model}: CT vs J (5039 RPM)", xlabel="J")
        ax[i, 1].set(title=f"{model}: CP vs J", xlabel="J")
        ax[i, 2].set(title=f"{model}: eta vs J", xlabel="J", ylim=(0, 0.8))
        ax[i, 0].legend(fontsize=8)
    for a in ax.flat:
        a.grid(alpha=0.3)
    fig.suptitle(f"DA4002 5x3.75 with tubercle polars (Hansen et al. 2010 ratios) [SIM {date.today().isoformat()}]")
    fig.tight_layout()
    fig.savefig(path, dpi=110)


def main() -> None:
    jobs = [(s, m) for s in SETTINGS for m in MODELS]
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        results = list(ex.map(run, jobs))
    runs = {(r["setting"], r["model"]): r for r in results}
    cmp_ = compare(runs)
    data = {"run_date": date.today().isoformat(), "n_crit": NCRIT, "dcd": DCD, "static_rpm": STATIC_RPM,
            "settings": tubercles.summary(), "compare": cmp_,
            "runs": {f"{m}/{s}": runs[(s, m)] for s, m in jobs}}
    OUT.mkdir(exist_ok=True)
    (OUT / "tubercles_compare.json").write_text(json.dumps(data, indent=1))
    plot(runs, OUT / "tubercles_compare.png")
    for k, r in cmp_.items():
        tun = " ".join(f"{t['rpm']:.0f}:CT{t['CT_pct_mean']:+.1f}/CP{t['CP_pct_mean']:+.1f}/eta{t['eta_max_pct']:+.1f}" for t in r["tunnel"])
        print(f"{k:24s} T5000 {r['static5000_T_pct']:+.1f}%  P5000 {r['static5000_P_pct']:+.1f}%  "
              f"T^1.5/P {r['static5000_T15_over_P_pct']:+.1f}%  worst T {r['worst_thrust_pct']:+.1f}%  | {tun}")


if __name__ == "__main__":
    main()
