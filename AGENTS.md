<!-- project-framework v0.3 · AI entry. Keep this first line: hooks use it to find the project root. -->
# AGENTS.md — biomimetics-2026

Read this file first. It is the only entry point for AI agents in this folder.
`CLAUDE.md` only imports this file. The project's tile in Claude Hub (section 1) is a status page; write it only when the user asks. `README.md` only points there.
Explanations for humans are in `C:\Users\User\Desktop\dev\project-framework\guide.html`. Do not copy them here.

## 1. Project

- Name: biomimetics-2026
- Goal: Merge the group's six biomimetic ideas into a bio-inspired drone rotor, back it with simulation, and present it at the course final.
- Deliverable: Bio-inspired rotor design + simulation results + final presentation (printing handed to teammates)
- Deadline: 2026-12-16 (Wed), course final presentation (AGREED 2026-11-26, BIO-20261126-2258)
- Card ID: `BIO-YYYYMMDD-HHMM`, the Asia/Taipei time when you write the card (Linux: `TZ=Asia/Taipei date +%Y%m%d-%H%M`; PowerShell: `[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId((Get-Date),'Taipei Standard Time').ToString('yyyyMMdd-HHmm')`). If that ID exists, use the next minute. Cards made before v0.2 keep their numbers.
- Access level: `TLP:CLEAR`; the GitHub repo is public so teammates can read it (section 7, BIO-20261126-2259).
- Hub tile: doc `map/biomimetics-2026` in the Claude Hub artifact https://claude.ai/artifact/XJW55vPwu1v4Q8piqSLrYY (framework PF-0034, PF-20261109-2026). Page: https://claude.ai/artifact/XJW55vPwu1v4Q8piqSLrYY#p-biomimetics-2026
- Created 2026-11-25 with project-framework v0.3 (`C:\Users\User\Desktop\dev\project-framework`).

## 2. Folder map

| Path | Purpose | Read when | Edit rule |
|---|---|---|---|
| `AGENTS.md` | AI entry: map and rules | Every session (auto-loaded) | Rewrite to stay current. Keep under 200 lines. |
| `CLAUDE.md` | One line: `@AGENTS.md` | Never | Do not add content. |
| Hub tile `map/biomimetics-2026` (not a file) | User entry, Traditional Chinese: `oneLine`, then four boxes `now`, `next`, `decide`, `parking`, plus `deadline`, `extra`, `artifacts` (section 3) | When the user asks for status | Rewrite the boxes only when the user asks (section 3). Keep history in the log, not on the tile. |
| `README.md` | Points to the Hub tile and the AI entry | Never | Change only when the project name, goal or tile ID changes. |
| `zettelkasten/INDEX.md` | Topic entry points (主題入口) at the top, then one line per card | Read the topic table. Grep the card lines; do not read all of them. | Rewrite the topic table freely. Add a line per card; change only its status cell later. |
| `zettelkasten/cards/` | One piece of information per file | Only the cards that a search or the topic table points to | Append only (5.5) |
| `zettelkasten/log/YYYY-MM.md` | One entry per turn that changed files, oldest first, Asia/Taipei time | Only to find a past turn | Append only |
| `zettelkasten/media/` | Original files: photos, screenshots, raw documents | When a card points to one | Never edit. Name files `<card ID>-<name>`. |
| `.claude/settings.json` | Project Claude Code settings. Empty: the turn hook is global (PF-0014). | Never | Change only with the user's approval. |
| `.gitattributes` | Git merge rules: the log and `INDEX.md` merge with `union` (framework PF-0022, PF-0029) | Never | After a merge, check the topic table for doubled rows. |
| `drive-map.md` | Google Drive folders the session may read: alias, folder ID, content, notes (framework PF-0037). Optional. | When you need files from Drive | Add a row when the user shares a folder. Never list a folder with other people's personal data. |
| `.cache/` | Drive downloads: `python3 ~/.claude/tools/drive.py fetch <alias>` | Never | Ignored by git. Never commit it. |
| `site/bionic-rotor/index.html` | Public page (Traditional Chinese): progress timeline, 3D viewer (three.js 0.160 from jsDelivr), every step with assumptions, parameters and charts (reads `data/results.json`). Source of github.io `biomimetics/bionic-rotor/` | When you change the public page | Edit here, then copy the whole `site/bionic-rotor/` folder to `lucassullivan0219.github.io/biomimetics/bionic-rotor/` and push its main. Preview: `mb-site` in `dev/.claude/launch.json`. Never put teammates' names here. |
| `site/bionic-rotor/data/results.json` | Chart data for the page | Never by hand | Regenerate: `uv run python sim/export_site_data.py`. |
| `site/bionic-rotor/models/` | GLB shown on the page (tolerance 0.02 mm / 5 deg, ~8 MB) | When the CAD model changes | `cad model export <id> site/bionic-rotor/models/<name>.glb --tolerance 0.02 --angle 5`. |
| `cad/da4002_prop.py` | build123d CAD model of the baseline prop, `da4002_prop_tubercles` (A2 lambda 7.5 by default; cards BIO-20261126-2326, BIO-20261128-1316) and `da4002_prop_serrations` (L18 cut-in sawtooth, TE thickened to 0.4 mm; BIO-20261128-1720) | When you change the geometry | `cad server start; cad run cad/da4002_prop.py`; check with `cad model dfm` (on the tubercle prop it hits the 1800 s limit; the serrated single blade finishes in ~7 min). Check volumes on a mesh, not with `cad model inspect` (BIO-20261128-1316). The text-to-cad skill is not installed in this repo (BIO-20261126-2325). |
| `cad/exports/` | STEP (exact) and 3MF (mesh) for teammates who print | When the CAD model changes | Re-export; do not commit STL (45 MB at fine tolerance). |
| `sim/calibrate_dcd.py` | Fits one drag offset dCd on the 5039 RPM tunnel CP and tests it on the other sets (BIO-20261126-2351); `--snel` or `--cs` refits with a stall-delay model (BIO-20261127-0044, BIO-20261127-1036); writes `sim/out/dcd_sweep[_snel|_cs].json` | When the polar or model changes | Rerun, then `validate_da4002.py --ncrit 3 --dcd <chosen>` and update `CAL_DCD` in `export_site_data.py`. |
| `sim/tubercles.py` | Leading-edge tubercles as a modified 2D polar: digitised Hansen et al. 2010 NACA 0021 curves and the mapping rules (BIO-20261128-1314, BIO-20261128-1315) | When you change a tubercle setting or the mapping | Keep the docstring's list of assumptions current. |
| `sim/tubercle_compare.py` | Runs baseline and each tubercle setting with the current and the uncorrected model, in parallel processes (~3 min); writes `sim/out/tubercles_compare.json|png` | After changing `tubercles.py` or the rotor model | Then rerun `export_site_data.py`; record results in a new card (SIM). |
| `sim/serrations.py` | Owl trailing-edge serrations as Cl/Cd factors on the serrated span: literature numbers (Li 2018, Candeloro 2026), "measured" and "area" mappings, thickened-TE coordinates for printing (BIO-20261128-1712, BIO-20261128-1718) | When you change a serration setting or the mapping | Keep the docstring's list of assumptions current. |
| `sim/serration_compare.py` | Runs baseline and each serration setting (two mappings, plus L18 thickTE) with the current and the uncorrected model, in parallel processes (~5 min); writes `sim/out/serrations_compare.json|png` and the thickTE polar cache | After changing `serrations.py` or the rotor model | Then rerun `export_site_data.py`; record results in a new card (SIM). |
| `sim/test_stall_delay.py` | Checks the Corrigan-Schillings delay angle against Tangler & Selig 1997 Table 1 (BIO-20261127-1036) | After changing `bemt.cs_delay_deg` | Run `uv run python sim/test_stall_delay.py`; it must print OK. |
| `sim/export_site_data.py` | Collects validation runs, polars, geometry and a spanwise solve into the page's JSON | After rerunning validations | — |
| `pyproject.toml`, `uv.lock` | Python environment for `sim/` (uv, Python 3.12): numpy, scipy, matplotlib, neuralfoil | When you add a dependency | `uv add <pkg>`; never edit `uv.lock` by hand. |
| `sim/bemt.py` | BEMT solver (single-unknown phi form, Prandtl tip and hub loss) and NeuralFoil polar tables | When you change the rotor model | Keep the docstring's list of simplifications current. |
| `sim/validate_da4002.py` | Validation against UIUC DA4002 5x3.75 (BIO-20261126-2302). Current model: `--ncrit 3 --dcd 0.0325 --snel` (BIO-20261127-0044) | When the model changes: rerun the current model and `--ncrit 3` (uncorrected) | Record new results in a new card (SIM). |
| `sim/fetch_uiuc.py` | Downloads the UIUC data files into `sim/data/uiuc/` (ignored by git: licence not stated) | Before the first validation run on a machine | Add files to `FILES` when you need another prop. |
| `sim/data/sda1075.dat` | SDA1075 airfoil coordinates from AIAA 2014-2151 Table 4 | Never edit | Add other airfoils as new files with a source line. |
| `sim/out/` | Validation plots and JSON (committed); `*.npz` polar caches (ignored) | When you report a result | Regenerate; do not hand-edit. |
| `zettelkasten/media/BIO-20261125-0153-six-ideas-transcript.md` | The group's six ideas and the leader's boat example (slides 82–88), names removed | When you need the original idea text | Never edit (frozen). |

Add a row for every new file or folder that you create.

## 3. Session start and every turn

At session start:
1. The SessionStart hook fast-forwards every framework repo to GitHub. If it reports a repo that is behind or has diverged, say so in the first sentence of your first reply.
2. If `drive-map.md` exists, the hook lists Drive files that changed after the last log entry. Ask the user whether they need a log entry or a card before you start other work.
3. If the deadline in section 1 is 3 days away or less, put framework and tool requests in the 停車場 first, unless the user says that they block the main line.

Before you end each turn that changed files:
1. Append one entry to `zettelkasten/log/YYYY-MM.md` (5.4). A turn that only answers questions needs no entry. A hook blocks the end of a turn that changed files until the entry exists.
2. Make one card for each new piece of information that is worth keeping (5.2).
3. If the project uses git, commit only your own paths: `git commit -m "<summary> [<card ID>]" -- <paths>`. Then push the branch to origin. If the push fails, say so in one line.

Update this file when the structure or a rule changes, and the topic table in `INDEX.md` when a topic gets a new start point.
The Hub tile (status page) is written only when the user asks for status (AGREED 2026-11-11, framework PF-20261111-1728). Then use ArtifactData `update` on collection `map`, doc `biomimetics-2026`, pinned with `if_version` from a fresh `get`; set `updatedAt` (UTC ISO), `lastActivity` (YYYY-MM-DD) and `source`. Fields: `now` and `next` are text; `decide` is a list of `{q, rec}`; `parking` is a list of `{topic, why, due, status}`; `artifacts` is a list of `{title, url, updated}`. Never override the user's choices in collection `moves`.
Other AI tools do not run the hook. Follow the steps without it.

## 4. Information reliability (Claim Ledger)

Tag each claim with its source:
- `REF`: a fact with an authoritative source. Give the link.
- `OBS`: an observation or a measurement. Give who, when and with what.
- `SIM`: a simulation result. Give the model or script, its parameters and the run date. A simulation is not a measurement.
- `MINE`: the user's idea, hypothesis or goal.
- `AI`: an AI inference, estimate or suggestion. Add a confidence word.
- `AGREED`: a decision that both sides confirmed. Give the date. Only a new decision can replace it.
- `OPEN`: an unresolved question. Give a recommended answer.

Confidence words for `AI` and `MINE`: `likely` (66–100 %), `possible` (33–66 %), `unlikely` (0–33 %).
Never write an inference as a fact. Never overwrite a raw value: add the new value with the date and the reason.
Change a tag only with evidence. `AI` or `MINE` becomes `REF` only when you have a source.

## 5. Zettelkasten (information box)

### 5.1 Reading
- Do not load the zettelkasten by default.
- Read the topic table (主題入口) at the top of `zettelkasten/INDEX.md` to find the start point for a topic.
- Grep the card lines of `INDEX.md` for a keyword or an ID. Then read only the matching cards.
- Use cards with status `valid`. Read `superseded` cards only when the user asks why something changed.

### 5.2 What becomes a card
One piece of information is one card. One turn can make many cards.
Make a card for: a decision (with the options considered), a test or experiment result (with raw values), an idea or a requirement from the user, a correction, information that is hard to find online (new research, lab-specific facts, measurements), a summary of a source.
Do not make a card for: knowledge that is easy to find (for example a standard math formula), small talk, steps that add no new information. The log entry is enough for these.

### 5.3 Card format
File `zettelkasten/cards/<ID>.md`. Write the front matter, the title and the summary in English. Write the body in the source language. Do not translate the body. Quote the user verbatim.

```
---
id: BIO-20261104-2359
date: YYYY-MM-DD
type: decision        # decision | result | idea | requirement | correction | research | source | structure
status: valid         # valid | superseded-by <card ID> | withdrawn
claim: AGREED         # REF | OBS | SIM | MINE | AI | AGREED | OPEN
confidence:           # likely | possible | unlikely (AI and MINE only)
lang: zh-TW           # language of the body
tags: [tag-one, tag-two]
links: []             # card IDs that this card depends on
supersedes:           # the card that this card replaces
---
# English title

One-sentence English summary.

Body in the source language.
```

Index line: `| BIO-20261104-2359 | YYYY-MM-DD | decision | valid | English title — one-sentence summary | tags |`

### 5.4 Log entry format
```
## YYYY-MM-DD HH:MM (Asia/Taipei) · <first 8 characters of the session ID>
- User: "<the user's words, verbatim>"
- Done: <what you did, in one or two lines>
- Cards: <card IDs> (or "none")
- Files: Hub tile, AGENTS.md, …
```
For long pasted material, save it to `media/` and point to the file.

### 5.5 Append-only rules
- Never edit or delete a card body after you write it.
- Exception: `INDEX.md` and cards of type `structure` are finding aids. Rewrite them to stay current.
- To correct a card: write a new card with type `correction` and `supersedes: <old ID>`. In the old card, change only the `status` line to `superseded-by <new ID>`. Change its index line the same way.
- After a correction, search for cards that link to the old ID. List them in your reply under 待複查, so that the user can check if they still hold.
- Real deletion is only for keys and passwords, other people's personal data, and content that a law requires you to remove. Do it only when the user asks. Tell the user that git history still keeps the file until the history is rewritten.

### 5.6 Topic entry points
They are the table at the top of `zettelkasten/INDEX.md` (主題入口). When a topic gets a new start point, add or rewrite its row there.

## 6. Working with the user

- Follow the user's global `CLAUDE.md` (language, Claim Ledger, how to explain). It is the single place for personal preferences since 2026-11-11.
- If that file is not loaded (other AI tools): write to the user in Traditional Chinese, keep technical terms in English, and never refer to an item only by a number, a label or an ID.
- This file, card metadata, code, file names and commit messages: English. Card bodies and the user's words: the original language, verbatim.

## 7. Access and storage

- This project is `TLP:CLEAR` (AGREED 2026-11-26, BIO-20261126-2259). RED = only the user. AMBER+STRICT = the user's organization only. AMBER = the organization and its partners. GREEN = a community, for example a class. CLEAR = everyone.
- The project level is the highest level of anything in it.
- The whole repo is public: every `git push` publishes. `site/` is also copied to github.io as the showcase page.
- Do not commit third-party data whose licence is unclear (for example the UIUC measurement files); commit a fetch script instead.
- Teammates' names are never recorded anywhere in this project, not even in private files (AGREED 2026-11-25, BIO-20261125-0150).
- Before `git push`, an artifact publish, an upload to a cloud drive, or a call that sends content to an external API, check the content against this list. If anything matches, stop and tell the user:
  1. keys, passwords, tokens;
  2. unpublished lab designs: circuits, firmware, measurement data;
  3. other people's personal data: names, student IDs, data about research subjects;
  4. human data, for example EEG recordings of other people;
  5. vendor proprietary files: decompiled code, installers.
- Do not put a git repository inside a Google Drive synced folder. Work under `C:\Users\User\Desktop\dev\` and copy the outputs to the drive.
- The Hub tile lives in a private claude.ai artifact (AGREED 2026-11-03, framework card PF-0034). Before you write it, check the content against the list above. A project page for other people is a separate artifact; put it in `artifacts`.
