"""Owl-like trailing-edge (TE) serrations as a modified 2D polar (plan card BIO-20261128-1116; result card in INDEX.md).

BEMT cannot see the 3D sawtooth, so each serration setting becomes a change to the SDA1075 polar on the
blade stations that carry serrations (the "serrated span"), passed to the solver through Rotor.polar as a
list with one polar per station. Noise is NOT modelled; dB values below are the sources' measurements only.

Sources (REF; full text read 2026-11-28 with pymupdf; numbers in Fig. 8/10 read by eye):
- L18: Li, Yang, Liu, Wang, Huang & Li, "Aerodynamic and aeroacoustic analyses of a UAV propeller with
  trailing edge serrations", Acoustics 2018, Adelaide, paper 22,
  https://www.acoustics.asn.au/conference_proceedings/AAS2018/papers/p22.pdf
  Prop R = 0.103 m, c(0.75R) = 16.3 mm; serrations cut into the chord, 2h = 0.1 c(0.75R) (average),
  lambda = 0.2 c(0.75R); rounded sawtooth (CNC tip radius, Fig. 2d). Six-component balance, anechoic tunnel.
  Hover 3000-8000 RPM: thrust, torque and efficiency "negligible difference" (Fig. 10).
  Edgewise forward flight (shaft 10 deg): lift -5.34 % / -5.13 %, drag -5.32 % / -5.79 % (mu 0.19 / 0.13).
  Noise: hover up to 7.5 dB at St ~2 (high-frequency band, decreasing with RPM); forward flight up to 12 dB
  at St ~4; OASPL directivity unchanged (Fig. 5b, 9b).
- STE1, STE2: Candeloro, Ragni & Pagliaroli, "Experimental investigation on the application of serrated trailing
  edge propellers for drone noise reduction", Applied Acoustics 242 (2026) 111045,
  https://doi.org/10.1016/j.apacoust.2025.111045 (open copy: TU Delft repository) and the AIAA 2024-3107
  conference version. APC 9x4.7E (D 228.6 mm), sawtooth cut into the TE; Table 4: STE1 b 4 mm, h 3 mm,
  5 teeth, blade area -2 %; STE2 b 6 mm, h 6 mm, 10 teeth, area -10 %. Re(0.75R) = 3.08e4 at 5000 RPM.
  cT and cP are normalised by the REDUCED blade area S^ (their Eq. 6-7). Hover, 5000 RPM: cT STE1 about -2.5 %
  (Fig. 8a, read; text "less than 5 %"), STE2 -12 %; cP STE1 about -2 %, STE2 about -14 % (text).
  Forward flight: cT -10 % / -20 %. Far-field noise: hover STE1 equal to baseline, STE2 -2 dB in the rotor plane
  (theta -10..20 deg) and louder elsewhere; forward flight (J 0.36) STE1 about -2 dB, STE2 -3..-4 dB.

Mapping (every step is an assumption; tags as on the result card):
1. Geometry relative to chord: A_c = tooth depth (peak to valley) / chord, lam_c = tooth pitch / chord.
   L18: 0.10 / 0.20 as published. STE1/STE2: chord not published; c ~ 13.8 mm is inferred from the paper's
   "h/c = 0.58" for h = 8 mm, giving A_c 0.22 / 0.43 and lam_c 0.29 / 0.43.  (AI possible)
   b is the full tooth base (= pitch): it matches Table 4's area loss (5 x 4 x 3 / 2 = 30 mm^2 ~ 2 % of a blade).
2. Serrated span on the DA4002: L18 r/R 0.30-0.95 (the source's Fig. 2c shows teeth along most of the TE; no
   numbers).  STE1/STE2: the same fraction of R as on the APC (n b / R = 0.175 / 0.525), ending at r/R 0.95
   (teeth need chord; the paper says the tip region matters most).  (AI possible)
3. "measured" mapping: the source's whole-rotor change in hover (STE) or forward flight (L18, the larger of its two
   cases; hover showed no change) is put entirely on the serrated span as one factor on Cl (k_L) and one on Cd
   (k_D):  k_L = 1 + dT / f_T,  k_D = 1 + dP / f_P, where f_T and f_P are the shares of thrust and power that the
   serrated span carries on the baseline DA4002 (current model, 5000 RPM static). Candeloro's coefficients are
   per reduced area, so their whole-rotor change is (1 + dcT)(1 - dS) - 1.  (AI possible)
   Cl and Cd are per ORIGINAL chord, so k includes the area removed by the teeth.
4. "area" mapping (check, no fitted numbers): teeth cut into the chord remove half the tooth depth on average, so
   Cl and Cd on the serrated span are scaled by (1 - A_c / 2) and nothing else changes.  (AI possible: the L18
   hover data say the true loss can be smaller; Candeloro's per-area drop says it can be larger)
5. The same factors are used at every angle and Reynolds number; zero-lift angle and stall angle do not move
   (Snel and the stall search see the same alpha0 and alpha_Clmax).  (AI possible)
6. Printable TE (CAD): the SDA1075 TE is 0.13 mm thick at the 11.5 mm mid chord. For the printed L18 prop the
   aft part is thickened so the tooth tips are >= T_MIN_MM (thickened_coords). Its polar effect is computed with
   NeuralFoil on the thickened section ("thickTE" mapping), on top of the measured factors.  (SIM)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

T_MIN_MM = 0.4  # minimum printable tooth thickness (SLA; AI possible, no vendor rule checked)
C_REF_MM = 0.1804 * 63.5  # DA4002 chord at 0.75 R (UIUC geometry), mm

SETTINGS = {
    "L18": {
        "src": "Li et al. 2018 (Acoustics 2018 p22)", "shape": "rounded sawtooth, cut into chord",
        "A_c": 0.10, "lam_c": 0.20, "r0": 0.30, "r1": 0.95,
        "dT": float(np.mean([-5.34, -5.13]) / 100), "dP": float(np.mean([-5.32, -5.79]) / 100),
        "basis": "forward flight lift/drag (hover: no measurable change)",
        "noise": "hover up to -7.5 dB at St~2 (high-frequency band); forward flight up to -12 dB at St~4",
        "re_src": "~4.4e4 at 0.75R, 5000 RPM (AI: computed from R, c and RPM; not stated in the paper)",
    },
    "STE1": {
        "src": "Candeloro et al. 2026 (Appl. Acoust. 242, 111045)", "shape": "sawtooth, cut into chord",
        "A_c": 3 / 13.8, "lam_c": 4 / 13.8, "r0": 0.95 - 20 / 114.3, "r1": 0.95,
        "dcT": -0.025, "dcP": -0.02, "dS": -0.02,
        "basis": "hover 5000 RPM, cT/cP per reduced area times area ratio",
        "noise": "hover far-field OASPL = baseline; forward flight about -2 dB",
        "re_src": "3.08e4 at 0.75R, 5000 RPM (paper)",
    },
    "STE2": {
        "src": "Candeloro et al. 2026 (Appl. Acoust. 242, 111045)", "shape": "sawtooth, cut into chord",
        "A_c": 6 / 13.8, "lam_c": 6 / 13.8, "r0": 0.95 - 60 / 114.3, "r1": 0.95,
        "dcT": -0.12, "dcP": -0.14, "dS": -0.10,
        "basis": "hover 5000 RPM, cT/cP per reduced area times area ratio",
        "noise": "hover -2 dB in rotor plane only (louder elsewhere); forward flight -3..-4 dB",
        "re_src": "3.08e4 at 0.75R, 5000 RPM (paper)",
    },
}
for _s in SETTINGS.values():
    if "dcT" in _s:
        _s["dT"] = (1 + _s["dcT"]) * (1 + _s["dS"]) - 1
        _s["dP"] = (1 + _s["dcP"]) * (1 + _s["dS"]) - 1


@dataclass
class ScaledPolar:
    """Wrap a polar (alpha_deg, re) -> (cl, cd) and multiply Cl by k_l and Cd by k_d."""

    base: Callable[[float, float], tuple[float, float]]
    k_l: float
    k_d: float

    def __call__(self, alpha_deg: float, re: float) -> tuple[float, float]:
        cl, cd = self.base(alpha_deg, re)
        return cl * self.k_l, cd * self.k_d


def span_shares(r_over_R: np.ndarray, dT_dr: np.ndarray, dQ_dr: np.ndarray, r0: float, r1: float) -> tuple[float, float]:
    """Share of thrust and torque (= power at fixed RPM) carried by r0 <= r/R <= r1 (trapezoid on the stations)."""
    m = (r_over_R >= r0) & (r_over_R <= r1)
    tot_t, tot_q = np.trapezoid(dT_dr, r_over_R), np.trapezoid(dQ_dr, r_over_R)
    # integrate only inside the band, with the band edges interpolated
    x = np.concatenate([[r0], r_over_R[m], [r1]])
    t = np.interp(x, r_over_R, dT_dr)
    q = np.interp(x, r_over_R, dQ_dr)
    return float(np.trapezoid(t, x) / tot_t), float(np.trapezoid(q, x) / tot_q)


def factors(setting: str, mapping: str, f_t: float, f_p: float) -> tuple[float, float]:
    s = SETTINGS[setting]
    if mapping == "area":
        k = 1 - s["A_c"] / 2
        return k, k
    if mapping in ("measured", "thickTE"):
        return 1 + s["dT"] / f_t, 1 + s["dP"] / f_p
    raise ValueError(mapping)


def station_polars(base, thick_base, r_over_R: np.ndarray, setting: str, mapping: str, f_t: float, f_p: float) -> list:
    """One polar per station: serrated stations get the scaled polar, the others the base polar."""
    s = SETTINGS[setting]
    k_l, k_d = factors(setting, mapping, f_t, f_p)
    src = thick_base if mapping == "thickTE" else base
    return [ScaledPolar(src, k_l, k_d) if s["r0"] <= r <= s["r1"] else base for r in r_over_R]


def thickened_coords(coords: np.ndarray, chord_mm: float, a_c: float, t_min_mm: float = T_MIN_MM) -> np.ndarray:
    """Selig-format coordinates with the aft part thickened so the tooth region (x >= 1 - a_c) is >= t_min_mm thick.

    The added thickness rises smoothly (smoothstep) from 0 at x_s = 1 - 2 a_c to dt at the tooth root x_r = 1 - a_c and
    stays dt to the TE; it is split half to the upper and half to the lower surface, so the camber line is unchanged.
    dt is chosen so the TE (the thinnest point of the tooth region) is exactly t_min_mm thick.
    """
    i = int(np.argmin(coords[:, 0]))
    up, lo = coords[: i + 1][::-1], coords[i:]
    t_te = np.interp(1.0, up[:, 0], up[:, 1]) - np.interp(1.0, lo[:, 0], lo[:, 1])
    dt = max(t_min_mm / chord_mm - t_te, 0.0)
    x_s, x_r = 1 - 2 * a_c, 1 - a_c

    def add(x):
        u = np.clip((x - x_s) / (x_r - x_s), 0.0, 1.0)
        return dt * u * u * (3 - 2 * u)

    out = coords.copy()
    upper = np.arange(len(coords)) <= i
    out[upper, 1] += add(out[upper, 0]) / 2
    out[~upper, 1] -= add(out[~upper, 0]) / 2
    return out


def summary(shares: dict | None = None) -> dict:
    out = {}
    for k, s in SETTINGS.items():
        row = {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in s.items()}
        row["A_mm_on_da4002"] = round(s["A_c"] * C_REF_MM, 2)
        row["lam_mm_on_da4002"] = round(s["lam_c"] * C_REF_MM, 2)
        row["area_factor"] = round(1 - s["A_c"] / 2, 4)
        if shares and k in shares:
            f_t, f_p = shares[k]
            row["f_T"], row["f_P"] = round(f_t, 4), round(f_p, 4)
            row["k_L_measured"], row["k_D_measured"] = (round(x, 4) for x in factors(k, "measured", f_t, f_p))
        out[k] = row
    return out


if __name__ == "__main__":
    import json

    print(json.dumps(summary(), indent=1))
