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
| BEMT 模擬、基準槳驗證、DA4002、n_crit、阻力校正 | BIO-20261126-2351, BIO-20261126-2302 |
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
