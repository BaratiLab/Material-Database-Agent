# Table 2 — MeltpoolNet benchmark

Reproduces Table 2: precision (P), recall (R) and F1 for five fields, plus
melting-temperature MAE, for each of the five models.

## Files

```
table2_meltpoolnet/
├── meltpoolnet_lib.py        # shared evaluation logic (metrics, matching, mapping parsers)
├── run_all.py                # runs all five models
├── meltpoolnet_regression.csv# ORIGINAL ground truth (Akbari et al., shared by all models)
├── gpt54/   gpt52/   claude/   glm/   qwen/
│     ├── evaluate.py                 # model-specific config + run
│     ├── extracted_data_*.csv        # RECONSTRUCTED dataset for this model
│     ├── <row_mapping>.csv           # frozen 100-pair mapping used in the paper
│     └── results_reproduced.csv      # written when you run evaluate.py
```

The row-mapping file name differs per model (it is whatever was produced during
the manual mapping):

| Model  | Reconstructed CSV                 | Row-mapping file |
|--------|-----------------------------------|------------------|
| gpt54  | `extracted_data_codex_gpt54.csv`  | `row_mapping_original_to_reconstructed_codex_gpt54.csv` |
| gpt52  | `extracted_data_codex.csv`        | `row_mapping_original_to_reconstructed.csv` |
| claude | `extracted_data_claude.csv`       | `row_mapping_original_to_reconstructed.csv` |
| glm    | `extracted_data_glm.csv`          | `same_row_mapping_100_manual.csv` |
| qwen   | `extracted_data_qwen.csv`         | `row_mapping_100_same_rows.csv` |

## Run

```bash
python3 run_all.py            # all five models
python3 claude/evaluate.py    # one model
```

## Method

For each of the 100 mapped row pairs and each evaluated field, the reconstructed
cell is classified (Sierepeklis & Cole, 2022,
https://doi.org/10.1038/s41597-022-01752-1):

- **TP** — both present and matching (within the field tolerance)
- **FP** — both present but mismatched, *or* original empty while reconstructed
  has a value
- **FN** — original present, reconstructed empty
- both empty → not counted

Then `P = TP/(TP+FP)`, `R = TP/(TP+FN)`, `F1 = 2PR/(P+R)`. Melting-temperature
MAE is the mean of `|orig − recon|` over pairs where both report a value.

### Per-field matching tolerances

The five extractions use different numeric conventions, so the tolerance / unit
handling is set per model in its `evaluate.py` (and matches the per-model
methodology notes in the original data folders):

- **claude / gpt52** report beam diameter in metres and hatch spacing in mm,
  whereas the ground truth uses mm and micrometres — a factor of 1000 is applied
  before comparison.
- **gpt54 / glm / qwen** use the same numeric scale as the ground truth (no
  conversion).
- `E (J/mm)` and `d/w` use a 1% relative tolerance; `beam D` and
  `depth of meltpool` use a small absolute tolerance; `Hatch spacing` uses the
  per-model tolerance noted in the script.

### Row-index conventions

Most mapping files number rows as **1-based file lines** (header = line 1). The
GPT-5.4 mapping numbers rows as **1-based data rows** (header excluded) and only
its first 100 pairs are used. Both conventions are handled in
`meltpoolnet_lib.py`.

## Expected values (from the paper)

P / R / F1 in %, melting-T MAE in K.

| Field             | GPT-5.4 (P/R/F1)      | GPT-5.2             | Claude Opus 4.6     | GLM 5V Turbo        | Qwen-3.5            |
|-------------------|-----------------------|---------------------|---------------------|---------------------|---------------------|
| beam D            | 35.71/45.45/40.00     | 73.81/79.49/76.54   | 90.48/82.61/86.38   | 80.00/100.0/88.89   | 79.00/100.0/88.27   |
| Hatch spacing     | 87.00/100.0/93.05     | 100.0/42.86/60.00   | 72.09/59.62/65.26   | 86.84/100.0/92.96   | 100.0/100.0/100.0   |
| E (J/mm)          | 100/100/100           | 100/100/100         | 95.96/98.96/97.44   | 100/100/100         | 100/100/100         |
| depth of meltpool | 78.38/31.52/44.96     | 78.57/23.40/36.06   | 38.96/56.60/46.15   | 60.00/100.0/75.00   | 71.95/76.62/74.21   |
| d/w               | 75.00/75.00/75.00     | 28.57/13.79/18.60   | 16.18/33.33/21.79   | 50.00/100.0/66.67   | 54.88/71.43/62.07   |
| **Melting T MAE** | **82.88**             | **172.60**          | **156.84**          | **13.90**           | **9.97**            |

All five models reproduce every value above. F1 may differ by ≤0.02 in the last
printed digit because the paper rounds P and R to two decimals before forming F1;
P, R and MAE match exactly.
