"""Check the Corrigan-Schillings stall delay against Tangler & Selig 1997, Table 1 (constant-chord CER blade:
alpha_clmax = 9 deg, alpha_0 = -1.2 deg, n = 1). Run: uv run python sim/test_stall_delay.py"""
import bemt

# (c/r, K, delay angle deg) read from the paper's Table 1
TABLE1 = [(1.000, 0.178, 3.135), (0.607, 0.281, 2.588), (0.364, 0.448, 2.051), (0.260, 0.610, 1.709),
          (0.202, 0.768, 1.461), (0.166, 0.923, 1.266), (0.140, 1.076, 1.106), (0.121, 1.226, 0.971),
          (0.107, 1.375, 0.854), (0.096, 1.523, 0.751)]

worst = 0.0
for cr, k_ref, d_ref in TABLE1:
    k = (0.1517 / cr) ** (1 / 1.084)
    d = bemt.cs_delay_deg(cr, 9.0, -1.2, 1.0)
    worst = max(worst, abs(d - d_ref))
    print(f"c/r {cr:.3f}  K {k:.3f} (paper {k_ref:.3f})  delay {d:.3f} deg (paper {d_ref:.3f})")
    # The paper's K column was likely read off its Fig. 2 curve: it sits up to ~1 % above the printed
    # fit at large c/r, which moves the delay by up to ~0.17 deg (5 %). Check to 6 %.
    assert abs(k - k_ref) / k_ref < 0.03, "K differs from the paper by more than 3 %"
    assert abs(d - d_ref) / d_ref < 0.06, "delay angle differs from the paper by more than 6 %"
print(f"OK: worst delay difference {worst:.3f} deg (largest at c/r = 1)")
