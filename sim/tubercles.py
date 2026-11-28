"""Leading-edge tubercles as a modified 2D polar (card BIO-20261128-1116; result card in INDEX.md).

BEMT cannot see the 3D wavy leading edge, so each tubercle setting becomes a change to the
SDA1075 polar, copied from measured NACA 0021 polars with and without tubercles:

Source (REF, full text read 2026-11-28, curves digitised by eye from the figures, about +-0.02 in Cl
and +-0.003 in Cd): Hansen, Kelso & Dally, "An investigation of three-dimensional effects on the
performance of tubercles at low Reynolds numbers", 17th Australasian Fluid Mechanics Conference,
Auckland 2010, paper 329, https://people.eng.unimelb.edu.au/imarusic/proceedings/17/329_Paper.pdf
NACA 0021, c = 70 mm, Re = 120,000, closed-loop wind tunnel, Tu ~0.8 %, no trips, 2D (full-span) data,
Figures 2, 3, 4, 5, 6 and 8. A/c and lambda/c are the paper's Table 1 values.

Mapping (every step is an assumption; tags as on the result card):
1. Normalised angle s = (alpha - alpha0) / (alpha_Clmax - alpha0). For the NACA 0021 data alpha0 = 0
   and alpha_Clmax = 12 deg (baseline 2D peak). For SDA1075, alpha0 and alpha_Clmax come from its own
   NeuralFoil polar at the element's Reynolds number (bemt.alpha0_deg, bemt.alpha_clmax_deg).
   Angles are matched by s, so "2 deg before stall" on one airfoil maps to "2 deg before stall" on the
   other, scaled.  (AI possible)
2. Pre-stall lift (|s| <= 1): Cl = Cl_SDA(alpha) * rL(s), rL = Cl_tub / Cl_base of the NACA data at
   alpha_H = 12 |s| deg; rL = 1 below alpha_H = 2 deg where both curves coincide.  (AI possible)
3. Post-stall lift (s > 1): Cl = max(Cl_SDA(alpha) * rL(1), Clmax_SDA * kP(s)), kP = Cl_tub(alpha_H) /
   Clmax_base. The second term carries over the tubercles' gentle stall; the first keeps the SDA1075's
   own post-stall shape when that is already gentler.  (AI possible)
4. Drag: Cd = Cd_SDA(alpha) * rD(s) for |s| <= 1 with rD = Cd_tub / Cd_base. After stall the paper's
   ratio is dominated by the baseline's abrupt stall (Cd jumps 0.068 -> 0.178), which SDA1075 does not
   show in NeuralFoil, so rD is held at its mean over alpha_H = 8..12 deg, reached by a linear ramp
   from the measured ratio at 8 deg (so Cd has no jump).  (AI possible)
5. The same ratios are used at every Reynolds number, although the blade runs at Re 3e3-2.3e4, five to
   forty times lower than the source. The paper itself concludes that tubercles bring no significant gain
   at low Re except post-stall.  (AI possible: the true penalty at our Re is unknown)
6. Negative angles mirror the positive side (the NACA 0021 is symmetric).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

import bemt

ALPHA_STALL_BASE = 12.0  # deg, NACA 0021 2D baseline peak (Fig. 2)

# Digitised 2D curves, alpha in deg. Baseline drag beyond 15 deg is off the plot top; not needed.
BASE = {
    "cl": {0: 0.0, 1: 0.09, 2: 0.18, 4: 0.39, 6: 0.66, 8: 0.95, 10: 1.02, 11: 1.04, 12: 1.045,
           13: 0.33, 15: 0.39, 20: 0.55},
    "cd": {0: 0.026, 1: 0.026, 2: 0.027, 4: 0.031, 6: 0.039, 8: 0.050, 10: 0.056, 11: 0.061, 12: 0.068},
}

SETTINGS = {
    # label: A/c, lambda/c (Table 1), digitised Cl (Fig. 2/4/6) and Cd (Fig. 3/5/8)
    "A2L7.5": {
        "A_c": 0.03, "lam_c": 0.11, "fig": "Fig. 2, 3 (red filled)",
        "cl": {0: 0.0, 1: 0.09, 2: 0.18, 4: 0.36, 6: 0.56, 8: 0.88, 9: 0.90, 10: 0.91, 11: 0.925, 12: 0.94,
               13: 0.94, 14: 0.90, 15: 0.86, 17: 0.81, 20: 0.76},
        "cd": {0: 0.029, 1: 0.030, 2: 0.031, 4: 0.035, 6: 0.041, 8: 0.052, 10: 0.060, 11: 0.065, 12: 0.073},
    },
    "A4L15": {
        "A_c": 0.06, "lam_c": 0.21, "fig": "Fig. 6, 8 (blue plus)",
        "cl": {0: 0.0, 1: 0.09, 2: 0.18, 4: 0.34, 6: 0.54, 8: 0.84, 9: 0.87, 10: 0.88, 11: 0.90, 12: 0.90,
               13: 0.85, 14: 0.80, 15: 0.76, 17: 0.76, 20: 0.72},
        "cd": {0: 0.027, 1: 0.028, 2: 0.029, 4: 0.032, 6: 0.039, 8: 0.050, 10: 0.060, 11: 0.069, 12: 0.094},
    },
    "A4L7.5": {
        "A_c": 0.06, "lam_c": 0.11, "fig": "Fig. 4, 5 (green filled)",
        "cl": {0: 0.0, 1: 0.09, 2: 0.18, 4: 0.33, 6: 0.46, 8: 0.775, 9: 0.83, 10: 0.81, 11: 0.80, 12: 0.81,
               13: 0.79, 14: 0.75, 15: 0.73, 17: 0.74, 20: 0.75},
        "cd": {0: 0.031, 1: 0.032, 2: 0.033, 4: 0.036, 6: 0.042, 8: 0.057, 10: 0.067, 11: 0.076, 12: 0.093},
    },
}


def _interp(table: dict, x: float) -> float:
    k = np.array(sorted(table))
    return float(np.interp(x, k, [table[i] for i in k]))


@dataclass
class TuberclePolar:
    """Wrap a polar (alpha_deg, re) -> (cl, cd) and apply one tubercle setting from SETTINGS."""

    base: Callable[[float, float], tuple[float, float]]
    setting: str
    _cache: dict = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        t = SETTINGS[self.setting]
        self._t = t
        h = np.arange(8.0, 12.01, 0.5)
        self._rd_post = float(np.mean([_interp(t["cd"], a) / _interp(BASE["cd"], a) for a in h]))
        self._clmax_base = max(BASE["cl"].values())

    def rL(self, a_h: float) -> float:
        a_h = min(abs(a_h), ALPHA_STALL_BASE)
        if a_h <= 2.0:
            return 1.0
        return _interp(self._t["cl"], a_h) / _interp(BASE["cl"], a_h)

    def rD(self, a_h: float) -> float:
        a_h = abs(a_h)
        if a_h >= ALPHA_STALL_BASE:
            return self._rd_post
        if a_h > 8.0:  # ramp to the held value so Cd has no jump at stall
            r8 = _interp(self._t["cd"], 8.0) / _interp(BASE["cd"], 8.0)
            return r8 + (self._rd_post - r8) * (a_h - 8.0) / (ALPHA_STALL_BASE - 8.0)
        return _interp(self._t["cd"], a_h) / _interp(BASE["cd"], a_h)

    def kP(self, a_h: float) -> float:
        return _interp(self._t["cl"], min(a_h, 20.0)) / self._clmax_base

    def _ref(self, re: float) -> tuple[float, float, float]:
        key = round(float(np.log10(max(re, 1.0))), 2)
        if key not in self._cache:
            a0 = bemt.alpha0_deg(self.base, re)
            am = bemt.alpha_clmax_deg(self.base, re)
            self._cache[key] = (a0, am, self.base(am, re)[0])
        return self._cache[key]

    def __call__(self, alpha_deg: float, re: float) -> tuple[float, float]:
        cl, cd = self.base(alpha_deg, re)
        a0, am, clmax = self._ref(re)
        s = (alpha_deg - a0) / max(am - a0, 1.0)
        a_h = ALPHA_STALL_BASE * s
        if s <= 1.0:
            return cl * self.rL(a_h), cd * self.rD(a_h)
        return max(cl * self.rL(ALPHA_STALL_BASE), clmax * self.kP(a_h)), cd * self._rd_post


def summary() -> dict:
    """Ratios that the page and the card quote."""
    out = {}
    for k, t in SETTINGS.items():
        tp = TuberclePolar(lambda a, r: (1.0, 1.0), k)
        out[k] = {
            "A_c": t["A_c"], "lam_c": t["lam_c"], "fig": t["fig"],
            "clmax_ratio": round(max(t["cl"].values()) / max(BASE["cl"].values()), 3),
            "rL_6deg": round(tp.rL(6.0), 3), "rL_8deg": round(tp.rL(8.0), 3), "rL_12deg": round(tp.rL(12.0), 3),
            "rD_0deg": round(tp.rD(0.0), 3), "rD_8deg": round(tp.rD(8.0), 3), "rD_post": round(tp._rd_post, 3),
            "cl_post_15_over_clmax_base": round(tp.kP(15.0), 3), "cl_post_20_over_clmax_base": round(tp.kP(20.0), 3),
        }
    return out


if __name__ == "__main__":
    import json

    print(json.dumps(summary(), indent=1))
