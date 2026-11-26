"""Blade element momentum theory (BEMT) for small propellers.

Polars come from NeuralFoil (a neural-network surrogate trained on XFOIL), tabulated once
over angle of attack and Reynolds number and then interpolated.

Per blade element the only unknown is the inflow angle phi. From axial and tangential
momentum balance with Prandtl tip and hub loss F:
    u = k W,  w = k' W,   k = sigma' Cn / (4 F sin phi),  k' = sigma' Ct / (4 F sin phi)
with sigma' = B c / (2 pi r), Cn = Cl cos phi - Cd sin phi, Ct = Cl sin phi + Cd cos phi.
Kinematics W sin phi = V + u and W cos phi = Omega r - w give the residual
    R(phi) = Omega r / (cos phi + k') * (sin phi - k) - V = 0,
which stays regular at V = 0 (static thrust), unlike the a / a' form.

Simplifications (see card BIO-20261126-2302 on the baseline validation):
- Reynolds number for the polar uses W0 = sqrt(V^2 + (Omega r)^2), not the induced W.
- No 3D rotational (stall delay) correction, no blade deflection, rigid steady flow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import brentq

RHO = 1.225  # kg/m^3
NU = 1.48e-5  # m^2/s

HERE = Path(__file__).parent


def read_airfoil(path: Path) -> np.ndarray:
    rows = []
    for line in path.read_text().splitlines()[1:]:
        parts = line.split()
        if len(parts) == 2:
            rows.append([float(parts[0]), float(parts[1])])
    return np.array(rows)


@dataclass
class Polar:
    """Cl, Cd tables on (alpha_deg, log10 Re)."""

    alpha_deg: np.ndarray
    log_re: np.ndarray
    cl: np.ndarray  # shape (n_alpha, n_re)
    cd: np.ndarray
    conf: np.ndarray
    _icl: RegularGridInterpolator = field(init=False, repr=False)
    _icd: RegularGridInterpolator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        kw = dict(bounds_error=False, fill_value=None)
        self._icl = RegularGridInterpolator((self.alpha_deg, self.log_re), self.cl, **kw)
        self._icd = RegularGridInterpolator((self.alpha_deg, self.log_re), self.cd, **kw)

    def __call__(self, alpha_deg: float, re: float) -> tuple[float, float]:
        a = float(np.clip(alpha_deg, self.alpha_deg[0], self.alpha_deg[-1]))
        lr = float(np.clip(np.log10(max(re, 1.0)), self.log_re[0], self.log_re[-1]))
        p = np.array([[a, lr]])
        return float(self._icl(p)[0]), float(max(self._icd(p)[0], 1e-4))


@dataclass
class DragOffset:
    """Wrap a polar and add a constant to Cd (calibration for roughness, low-Re drag, hub drag)."""

    base: Callable[[float, float], tuple[float, float]]
    dcd: float = 0.0

    def __call__(self, alpha_deg: float, re: float) -> tuple[float, float]:
        cl, cd = self.base(alpha_deg, re)
        return cl, cd + self.dcd


def neuralfoil_polar(
    coords: np.ndarray,
    cache: Path,
    n_crit: float = 9.0,
    model_size: str = "large",
    alpha_deg: np.ndarray | None = None,
    re: np.ndarray | None = None,
) -> Polar:
    if alpha_deg is None:
        alpha_deg = np.arange(-15.0, 25.01, 0.5)
    if re is None:
        re = np.geomspace(3e3, 2e5, 16)
    log_re = np.log10(re)
    if cache.exists():
        d = np.load(cache)
        if (
            np.allclose(d["alpha_deg"], alpha_deg)
            and np.allclose(d["log_re"], log_re)
            and float(d["n_crit"]) == n_crit
            and str(d["model_size"]) == model_size
        ):
            return Polar(d["alpha_deg"], d["log_re"], d["cl"], d["cd"], d["conf"])
    import neuralfoil as nf

    A, L = np.meshgrid(alpha_deg, log_re, indexing="ij")
    out = nf.get_aero_from_coordinates(
        coordinates=coords,
        alpha=A.ravel(),
        Re=10 ** L.ravel(),
        n_crit=n_crit,
        model_size=model_size,
    )
    cl = np.asarray(out["CL"]).reshape(A.shape)
    cd = np.asarray(out["CD"]).reshape(A.shape)
    conf = np.asarray(out["analysis_confidence"]).reshape(A.shape)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, alpha_deg=alpha_deg, log_re=log_re, cl=cl, cd=cd, conf=conf,
             n_crit=n_crit, model_size=model_size)
    return Polar(alpha_deg, log_re, cl, cd, conf)


@dataclass
class Rotor:
    radius: float  # m
    n_blades: int
    r_over_R: np.ndarray
    c_over_R: np.ndarray
    beta_deg: np.ndarray
    polar: Callable[[float, float], tuple[float, float]] | list  # one polar, or one per station
    hub_r_over_R: float | None = None

    def polar_at(self, i: int):
        return self.polar[i] if isinstance(self.polar, list) else self.polar


def _prandtl(B: int, r: float, R: float, r_hub: float, sphi: float) -> float:
    sphi = max(abs(sphi), 1e-6)
    f_tip = B / 2 * (R - r) / (r * sphi)
    f_hub = B / 2 * (r - r_hub) / (r * sphi)
    F = (2 / np.pi) * np.arccos(np.exp(-max(f_tip, 0.0))) * (2 / np.pi) * np.arccos(np.exp(-max(f_hub, 0.0)))
    return max(F, 1e-4)


def solve_element(rotor: Rotor, i: int, V: float, omega: float) -> dict:
    R = rotor.radius
    B = rotor.n_blades
    r = rotor.r_over_R[i] * R
    c = rotor.c_over_R[i] * R
    beta = np.radians(rotor.beta_deg[i])
    r_hub = (rotor.hub_r_over_R if rotor.hub_r_over_R is not None else rotor.r_over_R[0]) * R
    sigma = B * c / (2 * np.pi * r)
    W0 = np.hypot(V, omega * r)
    re = W0 * c / NU
    polar = rotor.polar_at(i)

    def parts(phi: float):
        sphi, cphi = np.sin(phi), np.cos(phi)
        F = _prandtl(B, r, R, r_hub, sphi)
        cl, cd = polar(np.degrees(beta - phi), re)
        cn = cl * cphi - cd * sphi
        ct = cl * sphi + cd * cphi
        k = sigma * cn / (4 * F * sphi)
        kp = sigma * ct / (4 * F * sphi)
        return sphi, cphi, F, cl, cd, cn, ct, k, kp

    def resid(phi: float) -> float:
        sphi, cphi, F, cl, cd, cn, ct, k, kp = parts(phi)
        return omega * r / (cphi + kp) * (sphi - k) - V

    grid = np.linspace(1e-4, np.pi / 2 - 1e-4, 400)
    vals = np.array([resid(p) for p in grid])
    idx = np.where(np.sign(vals[:-1]) * np.sign(vals[1:]) < 0)[0]
    ok = len(idx) > 0
    if ok:
        j = idx[0]
        phi = brentq(resid, grid[j], grid[j + 1], xtol=1e-10)
    else:
        phi = float(np.arctan2(V, omega * r)) if omega * r > 0 else np.pi / 4
    sphi, cphi, F, cl, cd, cn, ct, k, kp = parts(phi)
    W = omega * r / (cphi + kp)
    q = 0.5 * RHO * W**2 * c
    return dict(r=r, phi=phi, alpha_deg=np.degrees(beta - phi), W=W, re=re, F=F, cl=cl, cd=cd,
                dT_dr=B * q * cn, dQ_dr=B * q * ct * r, converged=ok)


def solve(rotor: Rotor, V: float, rpm: float) -> dict:
    omega = rpm * 2 * np.pi / 60
    n = rpm / 60
    D = 2 * rotor.radius
    els = [solve_element(rotor, i, V, omega) for i in range(len(rotor.r_over_R))]
    r = np.array([e["r"] for e in els])
    dT = np.array([e["dT_dr"] for e in els])
    dQ = np.array([e["dQ_dr"] for e in els])
    T = float(np.trapezoid(dT, r))
    Q = float(np.trapezoid(dQ, r))
    P = Q * omega
    CT = T / (RHO * n**2 * D**4)
    CP = P / (RHO * n**3 * D**5)
    J = V / (n * D)
    eta = J * CT / CP if CP > 0 and V > 0 else float("nan")
    return dict(T=T, Q=Q, P=P, CT=CT, CP=CP, J=J, eta=eta, elements=els,
                all_converged=all(e["converged"] for e in els))
