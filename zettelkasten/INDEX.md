# Zettelkasten index — biomimetics-2026

Rules for AI agents. Read the topic table first. Do not read all card lines: grep them for a keyword or an ID, then open only the matching cards. Use cards with status `valid`. Read `superseded` cards only when the user asks why something changed. Card format and append-only rules: `../AGENTS.md` section 5.

## 主題入口 (topic entry points)

Rewrite this table freely. One row per topic: the words people use for it, and the cards to open first.

| Keywords or situation | Start here |
|---|---|
| 目標、使用者要什麼 | BIO-20261125-0149 |
| 專案設定、隱私、發布、公開 | BIO-20261126-2259 |
| 方向：無人機仿生旋翼 | BIO-20261125-0151 |
| 前人研究、商業產品 | BIO-20261125-0152 |
| 組內六個構想原文 | BIO-20261125-0153 |
| 流體模擬方法、CFD、能不能跑 | BIO-20261125-0154, BIO-20261126-2300 |
| 規格、成功標準、基準槳、分工（grill） | BIO-20261125-0207 |
| 期末報告日期、截止 | BIO-20261126-2258 |
| 需求證據、噪音投訴、法規 | BIO-20261126-2301 |
| BEMT 模擬、目前採用的模型、升力修正、Snel、Corrigan–Schillings | BIO-20261127-0044, BIO-20261127-1036 |
| 基準槳驗證、DA4002、n_crit、阻力校正 | BIO-20261126-2351, BIO-20261126-2302 |
| 仿生特徵（瘤突、鋸齒）計畫、下一步 | BIO-20261128-1116 |
| 鯨魚瘤突：文獻參數、BEMT 結果、推力損失、CAD | BIO-20261128-1315, BIO-20261128-1314, BIO-20261128-1316 |
| 貓頭鷹尾緣鋸齒：文獻參數、BEMT 結果、推力損失、CAD、尾緣加厚、列印 | BIO-20261128-1718, BIO-20261128-1712, BIO-20261128-1720 |
| 3D 模型、CAD、列印、建模 skill | BIO-20261126-2326, BIO-20261126-2325 |

## Cards

| ID | Date | Type | Status | Title — summary | Tags |
|---|---|---|---|---|---|
| BIO-20261125-0149 | 2026-11-25 | requirement | valid | User's goals for the biomimetics course project — contribute, practice a prototype, focus on real need | goal, course, prototype |
| BIO-20261125-0150 | 2026-11-25 | decision | superseded-by BIO-20261126-2259 | Intake choices for biomimetics-2026 — private repo, TLP:RED, site/ to github.io, prefix BIO, names deleted | intake, project-setup, privacy |
| BIO-20261125-0151 | 2026-11-25 | decision | valid | Direction: bio-inspired drone rotor; printing handed to teammates — chosen over fan and boat | direction, drone-rotor, scope |
| BIO-20261125-0152 | 2026-11-25 | research | valid | Prior art: bio-inspired drone rotors — owl studied, humpback mixed, shark only on wings, no triple combo found | prior-art, drone-rotor |
| BIO-20261125-0153 | 2026-11-25 | source | valid | The group's six top-voted ideas plus the leader's boat example — transcript without names | six-ideas, source |
| BIO-20261125-0154 | 2026-11-25 | research | valid | Fluid simulation methods for rotors — BEMT to LBM, trade-offs, gaps to reality, what this hardware can run | cfd, simulation, aeroacoustics |
| BIO-20261125-0207 | 2026-11-25 | decision | valid | Grill round 1: all six recommendations accepted — simulation pipeline as prototype, -2 dB target, UIUC baseline | grill, scope, success-criteria |
| BIO-20261125-0301 | 2026-11-25 | decision | valid | Where each simulation runs, given the laptop's RTX 3060 — BEMT in cloud, FluidX3D on laptop, OpenFOAM on hold | hardware, simulation-plan, fluidx3d |
| BIO-20261126-2258 | 2026-11-26 | decision | valid | Final presentation date: 2026-12-16 — replaces tentative 2027-01-08 | deadline, schedule |
| BIO-20261126-2259 | 2026-11-26 | correction | valid | Repo stays public (TLP:CLEAR) so teammates can read it — names still never recorded | intake, privacy, visibility |
| BIO-20261126-2300 | 2026-11-26 | decision | valid | Simulation plan confirmed; BEMT runs on the lab desktop with NeuralFoil polars | hardware, simulation-plan, bemt, neuralfoil |
| BIO-20261126-2301 | 2026-11-26 | research | valid | Demand evidence: delivery-drone noise complaints, NASA annoyance study, EU C1/C2 sound limits | demand, noise, regulation |
| BIO-20261126-2302 | 2026-11-26 | result | valid | Baseline BEMT validation vs UIUC DA4002 5x3.75 — thrust ~5-7 % low in tunnel, power 14-28 % low; n_crit 3 adopted | bemt, validation, baseline, da4002 |
| BIO-20261126-2325 | 2026-11-26 | decision | valid | Modeling skill search: aero skills make no 3D geometry, so text-to-cad's cad skill was used — skill not installed in repo (classifier), cad 0.11.17 via uv | cad, skill, text-to-cad |
| BIO-20261126-2326 | 2026-11-26 | result | valid | 3D CAD model of the DA4002 5x3.75 baseline prop — dims and volume check out; FDM/SLA checks fail on the 0.12 mm trailing edge | cad, 3d-model, dfm, printing |
| BIO-20261126-2351 | 2026-11-26 | result | valid | Drag calibration dCd = 0.0325 — tunnel power within 2 % on held-out RPMs, but thrust 7-9 % low, efficiency now under-predicted, hover not fixed | bemt, calibration, drag |
| BIO-20261127-0044 | 2026-11-27 | result | valid | Snel stall delay plus dCd 0.0325 adopted — hover thrust -1.7 %, tunnel power within 1 %, mid-J thrust still 5-8 % low, static trend wrong | bemt, stall-delay, snel, calibration |
| BIO-20261127-1036 | 2026-11-27 | result | valid | Corrigan-Schillings stall delay slightly worse than Snel; neither fixes the static thrust trend — Snel + dCd stays | bemt, stall-delay, corrigan-schillings |
| BIO-20261128-1116 | 2026-11-28 | decision | valid | Bionic features: tubercles first as modified polars, literature parameters, continue in a new session | bionic-features, tubercles, plan |
| BIO-20261128-1314 | 2026-11-28 | research | valid | Leading-edge tubercle data at low Reynolds number — Hansen 2010 NACA 0021 curves digitised; three settings chosen | tubercles, literature, low-reynolds |
| BIO-20261128-1315 | 2026-11-28 | result | valid | Tubercle polars on the DA4002 — all three settings lose 6-23 % hover thrust; none meets the 5 % criterion | tubercles, bemt, thrust-loss |
| BIO-20261128-1316 | 2026-11-28 | result | valid | CAD model with A2 lambda 7.5 tubercles — dfm timed out; cad inspect overstates spline-loft volumes | cad, tubercles, dfm, volume |
| BIO-20261128-1712 | 2026-11-28 | research | valid | Trailing-edge serration data on small propellers at Re 2.5-4.4e4 — Li et al. 2018 and Candeloro et al. 2024/2026 read in full; settings L18, STE1, STE2 with thrust, power and dB | serrations, owl, trailing-edge, literature, low-reynolds, propeller, noise |
| BIO-20261128-1718 | 2026-11-28 | result | valid | Serration polars on the DA4002 — L18 and STE1 lose 3-5 % hover thrust and pass the 5 % criterion in both models; STE2 loses 12-20 % and fails; thickened TE +2 % (likely artefact) | serrations, owl, bemt, thrust-loss, success-criterion, da4002 |
| BIO-20261128-1720 | 2026-11-28 | result | valid | CAD model with L18 TE serrations and a 0.4 mm thickened TE — closed mesh 508.5 mm3 per blade; SLA dfm finished in 7 min and FAILED on the 1 mm unsupported-wall rule | cad, serrations, owl, 3d-model, dfm, printing, volume, trailing-edge |
