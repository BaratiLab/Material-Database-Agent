# Reproducibility — Material Database Agent (MDA) benchmark tables

This folder contains everything needed to reproduce the two quantitative
benchmark tables in the paper directly from the released data:

- **Table 2** — MeltpoolNet benchmark (precision / recall / F1 of selected
  fields + melting-temperature MAE), in [`table2_meltpoolnet/`](table2_meltpoolnet/)
- **Table 3** — High-entropy / complex-concentrated alloy (HEA/CCA) benchmark
  (MAE of four mechanical properties), in [`table3_hea_cca/`](table3_hea_cca/)

Each table is evaluated for the same five backbone models:

| Folder name | Model (as in paper)            | Agent environment |
|-------------|--------------------------------|-------------------|
| `gpt54`     | GPT-5.4                        | Codex CLI         |
| `gpt52`     | GPT-5.2                        | Codex CLI         |
| `claude`    | Claude Opus 4.6                | Claude Code       |
| `glm`       | GLM 5V Turbo                   | Claude Code       |
| `qwen`      | Qwen-3.5-397B (open-source)    | Claude Code       |

## What "reproduce" means here

Each model's score is computed against a **frozen manual row mapping** — the
100 ground-truth ↔ extracted row pairs that were mapped by hand for the paper
(see the paper's *Materials and Methods*). For each table/model we ship:

- the **original ground-truth dataset** (shared per table),
- the model's **reconstructed/extracted dataset**,
- the **row-mapping file** that pairs 100 ground-truth rows with 100 extracted
  rows, and
- an **`evaluate.py`** that re-reads those three artifacts and recomputes the
  reported numbers (writing a `results_reproduced.csv` next to itself).

The evaluation **does not re-run any LLM or re-do the mapping** — it deterministically
recomputes the published metrics from the released data and the prior mapping.

## How the row mapping was done (per the paper)

- **MeltpoolNet (Table 2):** 100 row pairs mapped on five fields — material
  composition, laser power, scan velocity, layer thickness, and paper DOI.
- **HEA/CCA (Table 3):** 100 row pairs mapped on three fields — alloy
  composition, source paper number, and Vickers hardness (HV).

## Requirements

- Python 3.8+ — **standard library only**, no third-party packages.

## Quick start

```bash
# Table 2 — all five models
cd table2_meltpoolnet && python3 run_all.py

# Table 3 — all five models
cd ../table3_hea_cca && python3 run_all.py
```

Or run a single cell, e.g. the Claude column of Table 3:

```bash
cd table3_hea_cca/claude && python3 evaluate.py
```

See each table's own `README.md` for the per-cell expected values and the exact
matching rules.

All twenty table cells (10 model/table combinations across both tables)
reproduce the published numbers exactly.
