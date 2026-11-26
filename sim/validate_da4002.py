"""Validate the BEMT pipeline against UIUC measurements of the DA4002 5x3.75 prop.

Run:  uv run python sim/fetch_uiuc.py
      uv run python sim/validate_da4002.py [--ncrit 9]
Writes sim/out/da4002_validation.png and .json.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import bemt

HERE = Path(__file__).parent
DATA = HERE / "data" / "uiuc"
OUT = HERE / "out"
R = 2.5 * 0.0254  # 5 in diameter
B = 2


def load_table(path: Path) -> np.ndarray:
    return np.loadtxt(path, skiprows=1)


def make_rotor(polar, n_stations: int = 40) -> bemt.Rotor:
    g = load_table(DATA / "da4002_5x3.75_geom.txt")  # r/R, c/R, beta (measured, as tested)
    # cosine spacing, refined toward the tip; stop short of r/R = 1 where F -> 0
    s = np.linspace(0, 1, n_stations)
    rr = 0.15 + (0.995 - 0.15) * np.sin(s * np.pi / 2)
    return bemt.Rotor(
        radius=R,
        n_blades=B,
        r_over_R=rr,
        c_over_R=np.interp(rr, g[:, 0], g[:, 1]),
        beta_deg=np.interp(rr, g[:, 0], g[:, 2]),
        polar=polar,
        hub_r_over_R=0.10,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ncrit", type=float, default=9.0)
    ap.add_argument("--dcd", type=float, default=0.0, help="constant added to every Cd (calibration)")
    args = ap.parse_args()

    coords = bemt.read_airfoil(HERE / "data" / "sda1075.dat")
    polar = bemt.neuralfoil_polar(coords, OUT / f"polar_sda1075_ncrit{args.ncrit:g}.npz", n_crit=args.ncrit)
    rotor = make_rotor(bemt.DragOffset(polar, args.dcd) if args.dcd else polar)

    res: dict = {"run_date": date.today().isoformat(), "n_crit": args.ncrit, "prop": "DA4002 5x3.75",
                 "polar": "NeuralFoil large", "dcd": args.dcd, "stations": len(rotor.r_over_R)}

    st = load_table(DATA / "da4002_5x3.75_static_1121md.txt")
    sim_static = [bemt.solve(rotor, 0.0, rpm) for rpm in st[:, 0]]
    ct_s = np.array([s["CT"] for s in sim_static])
    cp_s = np.array([s["CP"] for s in sim_static])
    res["static"] = {
        "rpm": st[:, 0].tolist(), "CT_meas": st[:, 1].tolist(), "CP_meas": st[:, 2].tolist(),
        "CT_sim": ct_s.tolist(), "CP_sim": cp_s.tolist(),
        "CT_err_pct_mean": float(np.mean((ct_s - st[:, 1]) / st[:, 1]) * 100),
        "CP_err_pct_mean": float(np.mean((cp_s - st[:, 2]) / st[:, 2]) * 100),
        "all_converged": all(s["all_converged"] for s in sim_static),
    }

    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    ax[0, 0].plot(st[:, 0], st[:, 1], "ko", label="UIUC CT")
    ax[0, 0].plot(st[:, 0], ct_s, "k-", label="BEMT CT")
    ax[0, 0].plot(st[:, 0], st[:, 2], "s", color="C3", label="UIUC CP")
    ax[0, 0].plot(st[:, 0], cp_s, "-", color="C3", label="BEMT CP")
    ax[0, 0].set(title="Static (V = 0)", xlabel="RPM", ylabel="coefficient")
    ax[0, 0].legend(fontsize=8)

    res["wind_tunnel"] = []
    files = sorted(DATA.glob("da4002_5x3.75_11*md_*.txt"))
    for k, f in enumerate(files):
        rpm = float(f.stem.split("_")[-1])
        d = load_table(f)  # J, CT, CP, eta
        n = rpm / 60
        sims = [bemt.solve(rotor, J * n * 2 * R, rpm) for J in d[:, 0]]
        ct = np.array([s["CT"] for s in sims])
        cp = np.array([s["CP"] for s in sims])
        eta = np.array([s["eta"] for s in sims])
        col = f"C{k}"
        ax[0, 1].plot(d[:, 0], d[:, 1], "o", color=col, ms=4)
        ax[0, 1].plot(d[:, 0], ct, "-", color=col, label=f"{rpm:.0f} RPM")
        ax[1, 0].plot(d[:, 0], d[:, 2], "o", color=col, ms=4)
        ax[1, 0].plot(d[:, 0], cp, "-", color=col)
        ax[1, 1].plot(d[:, 0], d[:, 3], "o", color=col, ms=4)
        ax[1, 1].plot(d[:, 0], eta, "-", color=col)
        mask = d[:, 1] > 0.03  # relative error is meaningless near CT = 0
        res["wind_tunnel"].append({
            "rpm": rpm, "J": d[:, 0].tolist(),
            "CT_meas": d[:, 1].tolist(), "CT_sim": ct.tolist(),
            "CP_meas": d[:, 2].tolist(), "CP_sim": cp.tolist(),
            "eta_meas": d[:, 3].tolist(), "eta_sim": [None if np.isnan(e) else float(e) for e in eta],
            "CT_err_pct_mean_CTgt0.03": float(np.mean((ct[mask] - d[mask, 1]) / d[mask, 1]) * 100),
            "CP_err_pct_mean_CTgt0.03": float(np.mean((cp[mask] - d[mask, 2]) / d[mask, 2]) * 100),
            "eta_max_meas": float(np.max(d[:, 3])), "eta_max_sim": float(np.nanmax(eta)),
            "all_converged": all(s["all_converged"] for s in sims),
        })
    ax[0, 1].set(title="CT vs J (dots UIUC, lines BEMT)", xlabel="J", ylabel="CT")
    ax[0, 1].legend(fontsize=8)
    ax[1, 0].set(title="CP vs J", xlabel="J", ylabel="CP")
    ax[1, 1].set(title="efficiency vs J", xlabel="J", ylabel="eta", ylim=(0, 0.8))
    for a in ax.flat:
        a.grid(alpha=0.3)
    fig.suptitle(f"DA4002 5x3.75: BEMT + NeuralFoil (n_crit={args.ncrit:g}, dCd={args.dcd:g}) vs UIUC  [SIM {res['run_date']}]")
    fig.tight_layout()
    OUT.mkdir(exist_ok=True)
    tag = f"ncrit{args.ncrit:g}" + (f"_dcd{args.dcd:g}" if args.dcd else "")
    fig.savefig(OUT / f"da4002_validation_{tag}.png", dpi=120)
    (OUT / f"da4002_validation_{tag}.json").write_text(json.dumps(res, indent=1))

    print(f"static  CT err {res['static']['CT_err_pct_mean']:+.1f}%  CP err {res['static']['CP_err_pct_mean']:+.1f}%  conv {res['static']['all_converged']}")
    for w in res["wind_tunnel"]:
        print(f"{w['rpm']:.0f} RPM  CT err {w['CT_err_pct_mean_CTgt0.03']:+.1f}%  CP err {w['CP_err_pct_mean_CTgt0.03']:+.1f}%  "
              f"eta_max meas {w['eta_max_meas']:.3f} sim {w['eta_max_sim']:.3f}  conv {w['all_converged']}")


if __name__ == "__main__":
    main()
