"""DA4002 5x3.75 two-blade propeller (baseline), as a build123d CAD model for text-to-cad.

Geometry sources:
- Blade chord and twist: UIUC Propeller Database Vol. 2, `da4002_5x3.75_geom.txt` (measured, as tested),
  fetched by `sim/fetch_uiuc.py` into `sim/data/uiuc/`.
- Airfoil: SDA1075 over the whole blade, `sim/data/sda1075.dat` (AIAA 2014-2151, Table 4).

Frame: millimetres, +Z = thrust axis (up), blades along +X / -X, rotation counter-clockwise seen from +Z,
so each section's leading edge faces the direction of travel (+Y for the +X blade) and is pitched up by beta.

Assumptions (not in the sources; see card on the 3D model):
- Sections are stacked on their quarter chord along a straight radial line (no sweep, no rake).
- Hub: a plain cylinder; diameter, height and bore below are guesses, not UIUC data.
- The blade ends at r/R = TIP_END with a flat cap, because the measured chord goes to ~1.4 mm at r/R = 1.

Tubercle variant (models da4002_prop_tubercles / da4002_blade_tubercles; result card on tubercles):
- Leading edge moves fore and aft as a sine along the span; the trailing edge stays where the baseline has it,
  so the local chord is c (1 + (A/c)/2 sin(2 pi (r - r0) / lambda)) and the section (with its thickness) is
  scaled to that chord. A/c is taken as peak-to-peak (the source's Fig. 1 does not settle half vs full).
- lambda is constant along the span: (lambda/c) times the reference chord 0.178 R (the mid-blade chord), as the
  source tested a constant-chord wing. A follows the local chord, so the bumps fade toward the tip.
- Default A/c 0.03, lambda/c 0.11 = setting "A2 lambda 7.5" of Hansen, Kelso & Dally 2010 (AFMC paper 329).
- Ruled loft through 8 sections per wavelength (chord and twist linearly interpolated between UIUC rows).

Run:  cad server start;  cad run cad/da4002_prop.py
Check: cad model dfm "$ID" --process printing --technology fdm
"""
import math
from pathlib import Path

import build123d as bd
from cad import model

ROOT = Path(__file__).resolve().parent.parent
AIRFOIL = ROOT / "sim" / "data" / "sda1075.dat"
GEOM = ROOT / "sim" / "data" / "uiuc" / "da4002_5x3.75_geom.txt"

R = 63.5  # mm, 5 in diameter
B = 2
STACK = model.param("stack_x_over_c", 0.25, min=0.0, max=0.5)
HUB_D = model.param("hub_diameter", 14.0, min=8, max=20, unit="mm")
HUB_H = model.param("hub_height", 9.0, min=5, max=15, unit="mm")
BORE_D = model.param("bore_diameter", 5.0, min=2, max=8, unit="mm")
ROOT_IN = model.param("root_r_over_r", 0.10, min=0.05, max=0.15)  # blade starts inside the hub
TIP_END = model.param("tip_r_over_r", 0.99, min=0.95, max=1.0)
TUB_A_C = model.param("tubercle_amplitude_over_c", 0.03, min=0.0, max=0.15)  # peak-to-peak
TUB_LAM_C = model.param("tubercle_wavelength_over_c", 0.11, min=0.05, max=1.0)
TUB_R0 = model.param("tubercle_start_r_over_r", 0.15, min=0.10, max=0.5)
TUB_C_REF = 0.178  # c/R used to turn lambda/c into mm (mid-blade chord)
TUB_PER_WAVE = 8


def read_airfoil(path: Path) -> list[tuple[float, float]]:
    pts = []
    for line in path.read_text().splitlines()[1:]:
        p = line.split()
        if len(p) == 2:
            pts.append((float(p[0]), float(p[1])))
    return pts


def read_geom(path: Path) -> list[tuple[float, float, float]]:
    rows = []
    for line in path.read_text().splitlines()[1:]:
        p = line.split()
        if len(p) == 3:
            rows.append((float(p[0]), float(p[1]), float(p[2])))
    return rows


def interp(x: float, xs: list[float], ys: list[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def section(r_mm: float, chord_mm: float, beta_deg: float, foil) -> bd.Wire:
    """Airfoil at radius r: chord along -Y (LE at +Y), thickness along +Z, then pitched up by beta about X."""
    cb, sb = math.cos(math.radians(beta_deg)), math.sin(math.radians(beta_deg))
    pts = []
    for xc, yc in foil:
        y = -(xc - STACK) * chord_mm
        z = yc * chord_mm
        # rotation about +X by beta: +Y goes toward +Z, so the LE (at +Y) pitches up
        pts.append(bd.Vector(r_mm, y * cb - z * sb, y * sb + z * cb))
    spline = bd.Spline(*pts)
    te = bd.Line(pts[-1], pts[0])  # blunt trailing edge as in the coordinates
    return bd.Wire([spline, te])


def tubercle_section(r_mm: float, chord_mm: float, beta_deg: float, foil, dchord_mm: float) -> bd.Wire:
    """Like section(), but the chord grows by dchord_mm at the leading edge while the trailing edge stays put."""
    cb, sb = math.cos(math.radians(beta_deg)), math.sin(math.radians(beta_deg))
    c2 = chord_mm + dchord_mm
    y_te = -(1 - STACK) * chord_mm
    pts = []
    for xc, yc in foil:
        y = y_te + (1 - xc) * c2
        z = yc * c2
        pts.append(bd.Vector(r_mm, y * cb - z * sb, y * sb + z * cb))
    return bd.Wire([bd.Spline(*pts), bd.Line(pts[-1], pts[0])])


def tubercle_blade() -> bd.Solid:
    foil = read_airfoil(AIRFOIL)
    g = read_geom(GEOM)
    rr, cc, bb = [x[0] for x in g], [x[1] for x in g], [x[2] for x in g]
    lam = TUB_LAM_C * TUB_C_REF * R  # mm
    wires = [section(ROOT_IN * R, cc[0] * R, bb[0], foil)]
    r0 = max(TUB_R0, rr[0])
    if r0 > ROOT_IN:
        wires.append(section(r0 * R, cc[0] * R, bb[0], foil))
    n = int(math.ceil((TIP_END - r0) * R / lam * TUB_PER_WAVE))
    for k in range(1, n + 1):
        r = r0 + (TIP_END - r0) * k / n
        c = interp(r, rr, cc) * R
        dc = 0.5 * TUB_A_C * c * math.sin(2 * math.pi * (r - r0) * R / lam)
        wires.append(tubercle_section(r * R, c, interp(r, rr, bb), foil, dc))
    return bd.Solid.make_loft(wires, ruled=True)


def blade_stations() -> list[tuple[float, float, float]]:
    g = read_geom(GEOM)
    rr = [row[0] for row in g]
    cc = [row[1] for row in g]
    bb = [row[2] for row in g]
    stations = [(ROOT_IN, cc[0], bb[0])]  # buried in the hub, same section as the first measured one
    stations += [row for row in g if row[0] < TIP_END]
    stations.append((TIP_END, interp(TIP_END, rr, cc), interp(TIP_END, rr, bb)))
    return stations


def blade() -> bd.Solid:
    foil = read_airfoil(AIRFOIL)
    wires = [section(r * R, c * R, b, foil) for r, c, b in blade_stations()]
    return bd.Solid.make_loft(wires, ruled=False)


@model
def da4002_prop():
    b1 = blade()
    b2 = bd.Rotation(0, 0, 180) * b1
    hub = bd.Cylinder(HUB_D / 2, HUB_H) - bd.Cylinder(BORE_D / 2, HUB_H)
    prop = hub + b1 + b2
    prop.label = "da4002_5x3.75"
    prop.color = "#d9822b"
    return prop


@model
def da4002_blade():
    b = blade()
    b.label = "blade"
    b.color = "#d9822b"
    return b


@model
def da4002_prop_tubercles():
    b1 = tubercle_blade()
    b2 = bd.Rotation(0, 0, 180) * b1
    hub = bd.Cylinder(HUB_D / 2, HUB_H) - bd.Cylinder(BORE_D / 2, HUB_H)
    prop = hub + b1 + b2
    prop.label = f"da4002_tubercles_A{TUB_A_C:g}_L{TUB_LAM_C:g}"
    prop.color = "#2b7bd9"
    return prop


if __name__ == "__main__":
    da4002_blade()
    da4002_prop()
    da4002_prop_tubercles()
