"""Compare owl TE-serration settings with the baseline DA4002 5x3.75 at equal RPM (card BIO-20261128-1116).

Each setting is run with the current model (n_crit 3, dCd 0.0325, Snel) and the uncorrected one (n_crit 3 only),
with two mappings from serrations.py: "measured" (the source's whole-rotor change put on the serrated span) and
"area" (only the chord removed by the teeth). L18 also runs "thickTE": measured factors on the NeuralFoil polar of
the section thickened for printing (T_MIN_MM at the TE). Points: UIUC static RPMs, 5000 RPM static, UIUC tunnel J.
BEMT does not predict noise.

Run:  uv run python sim/serration_compare.py
Writes sim/out/serrations_compare.json and serrations_compare.png.
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
import serrations as srr
import validate_da4002 as v

HERE = Path(__file__).parent
OUT = HERE / "out"
NCRIT = 3.0
DCD = 0.0325
MODELS = {"current": {"dcd": DCD, "snel": True}, "uncorrected": {"dcd": 0.0, "snel": False}}
STATIC_RPM = 5000.0
CASES = ["baseline"] + [f"{s}/{m}" for s in srr.SETTINGS for m in ("measured", "area")] + ["L18/thickTE"]


def polars():
    coords = bemt.read_airfoil(HERE / "data" / "sda1075.dat")
    p = bemt.neuralfoil_polar(coords, OUT / f"polar_sda1075_ncrit{NCRIT:g}.npz", n_crit=NCRIT)
    a_c = srr.SETTINGS["L18"]["A_c"]
    tc = srr.thickened_coords(coords, srr.C_REF_MM, a_c)
    pt = bemt.neuralfoil_polar(tc, OUT / f"polar_sda1075_thickTE{srr.T_MIN_MM:g}mm_L18_ncrit{NCRIT:g}.npz", n_crit=NCRIT)
    return p, pt


def build(case: str, model: str, shares: dict) -> bemt.Rotor:
    p, pt = polars()
    m = MODELS[model]
    wrap = (lambda q: bemt.DragOffset(q, m["dcd"])) if m["dcd"] else (lambda q: q)
    rotor = v.make_rotor(wrap(p))
    if case != "baseline":
        setting, mapping = case.split("/")
        f_t, f_p = shares[setting]
        rotor.polar = srr.station_polars(wrap(p), wrap(pt), rotor.r_over_R, setting, mapping, f_t, f_p)
    rotor.snel = m["snel"]
    return rotor


def run(job: tuple[str, str, dict]) -> dict:
    case, model, shares = job
    rotor = build(case, model, shares)
    st = v.load_table(v.DATA / "da4002_5x3.75_static_1121md.txt")
    static = [bemt.solve(rotor, 0.0, rpm) for rpm in st[:, 0]]
    s5 = bemt.solve(rotor, 0.0, STATIC_RPM)
    res = {
        "case": case, "model": model,
        "static": {"rpm": st[:, 0].tolist(), "T": [s["T"] for s in static], "P": [s["P"] for s in static],
                   "CT": [s["CT"] for s in static], "CP": [s["CP"] for s in static]},
        "static5000": {"T": s5["T"], "P": s5["P"], "CT": s5["CT"], "CP": s5["CP"],
                        "r_over_R": [e["r"] / v.R for e in s5["elements"]],
                        "alpha": [e["alpha_deg"] for e in s5["elements"]],
                        "cl": [e["cl"] for e in s5["elements"]], "cd": [e["cd"] for e in s5["elements"]],
                        "dT_dr": [e["dT_dr"] for e in s5["elements"]], "dQ_dr": [e["dQ_dr"] for e in s5["elements"]]},
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
        for case in CASES[1:]:
            r = runs[(case, model)]
            row = {
                "static5000_T_pct": pct(r["static5000"]["T"], base["static5000"]["T"]),
                "static5000_P_pct": pct(r["static5000"]["P"], base["static5000"]["P"]),
                "static5000_T_N": r["static5000"]["T"], "static5000_P_W": r["static5000"]["P"],
                "base_static5000_T_N": base["static5000"]["T"], "base_static5000_P_W": base["static5000"]["P"],
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
            out[f"{model}/{case}"] = row
    return out


def polar_delta(p, pt) -> dict:
    """Thickened-TE polar minus baseline polar (no dCd) at a few points, for the card and the page."""
    rows = []
    for re in (1e4, 2e4):
        for a in (0.0, 4.0, 8.0, 12.0):
            cl0, cd0 = p(a, re)
            cl1, cd1 = pt(a, re)
            rows.append({"re": re, "alpha": a, "cl": cl0, "cl_thick": cl1, "cd": cd0, "cd_thick": cd1})
    return {"rows": rows, "alpha": p.alpha_deg.tolist(),
            "cl_2e4": [p(a, 2e4)[0] for a in p.alpha_deg], "cl_thick_2e4": [pt(a, 2e4)[0] for a in p.alpha_deg],
            "cd_2e4": [p(a, 2e4)[1] for a in p.alpha_deg], "cd_thick_2e4": [pt(a, 2e4)[1] for a in p.alpha_deg]}


def plot(runs: dict, path: Path) -> None:
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    shown = ["baseline", "L18/measured", "STE1/measured", "STE2/measured", "L18/thickTE"]
    for i, model in enumerate(MODELS):
        for k, case in enumerate(shown):
            r = runs[(case, model)]
            ls = "-" if case == "baseline" else "--"
            col = "k" if case == "baseline" else f"C{k}"
            t = r["tunnel"][1]  # 5039 RPM
            ax[i, 0].plot(t["J"], t["CT"], ls, color=col, label=case)
            ax[i, 1].plot(t["J"], t["CP"], ls, color=col)
            ax[i, 2].plot(t["J"], [np.nan if e is None else e for e in t["eta"]], ls, color=col)
        ax[i, 0].set(title=f"{model}: CT vs J (5039 RPM)", xlabel="J")
        ax[i, 1].set(title=f"{model}: CP vs J", xlabel="J")
        ax[i, 2].set(title=f"{model}: eta vs J", xlabel="J", ylim=(0, 0.8))
        ax[i, 0].legend(fontsize=8)
    for a in ax.flat:
        a.grid(alpha=0.3)
    fig.suptitle(f"DA4002 5x3.75 with TE-serration polars (Li 2018, Candeloro 2026 ratios) [SIM {date.today().isoformat()}]")
    fig.tight_layout()
    fig.savefig(path, dpi=110)


def main() -> None:
    p, pt = polars()  # build both polar tables once, before the workers read the caches
    base = v.make_rotor(bemt.DragOffset(p, DCD))
    base.snel = True
    s5 = bemt.solve(base, 0.0, STATIC_RPM)
    rr = np.array([e["r"] / v.R for e in s5["elements"]])
    dT = np.array([e["dT_dr"] for e in s5["elements"]])
    dQ = np.array([e["dQ_dr"] for e in s5["elements"]])
    shares = {k: srr.span_shares(rr, dT, dQ, s["r0"], s["r1"]) for k, s in srr.SETTINGS.items()}
    for k, (ft, fp) in shares.items():
        kl, kd = srr.factors(k, "measured", ft, fp)
        print(f"{k}: span {srr.SETTINGS[k]['r0']:.3f}-{srr.SETTINGS[k]['r1']:.2f}  f_T {ft:.3f} f_P {fp:.3f}  "
              f"k_L {kl:.3f} k_D {kd:.3f}  area {1 - srr.SETTINGS[k]['A_c'] / 2:.3f}")
    jobs = [(c, m, shares) for c in CASES for m in MODELS]
    with ProcessPoolExecutor(max_workers=min(len(jobs), 14)) as ex:
        results = list(ex.map(run, jobs))
    runs = {(r["case"], r["model"]): r for r in results}
    cmp_ = compare(runs)
    data = {"run_date": date.today().isoformat(), "n_crit": NCRIT, "dcd": DCD, "static_rpm": STATIC_RPM,
            "t_min_mm": srr.T_MIN_MM, "c_ref_mm": srr.C_REF_MM,
            "settings": srr.summary(shares), "compare": cmp_, "thick_te_polar": polar_delta(p, pt),
            "runs": {f"{m}/{c}": runs[(c, m)] for c, m, _ in jobs}}
    OUT.mkdir(exist_ok=True)
    (OUT / "serrations_compare.json").write_text(json.dumps(data, indent=1))
    plot(runs, OUT / "serrations_compare.png")
    for k, r in cmp_.items():
        tun = " ".join(f"{t['rpm']:.0f}:CT{t['CT_pct_mean']:+.1f}/CP{t['CP_pct_mean']:+.1f}/eta{t['eta_max_pct']:+.1f}" for t in r["tunnel"])
        print(f"{k:28s} T5000 {r['static5000_T_pct']:+.1f}%  P5000 {r['static5000_P_pct']:+.1f}%  "
              f"T^1.5/P {r['static5000_T15_over_P_pct']:+.1f}%  worst T {r['worst_thrust_pct']:+.1f}%  | {tun}")


if __name__ == "__main__":
    main()
