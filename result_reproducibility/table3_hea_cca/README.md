# Table 3 — HEA/CCA benchmark

Reproduces Table 3: mean absolute error (MAE) of four mechanical properties for
each of the five models, computed over the 100 manually mapped row pairs.

| Symbol      | Property                  | Units |
|-------------|---------------------------|-------|
| `sigma_y`   | yield strength            | MPa   |
| `sigma_max` | ultimate tensile strength | MPa   |
| `epsilon`   | elongation / strain       | %     |
| `E`         | Young's modulus           | GPa   |

## Files

```
table3_hea_cca/
├── hea_lib.py                # shared logic (readers, mapping parsers, MAE)
├── run_all.py                # runs all five models
├── table_1.csv               # ORIGINAL ground truth (shared by all models)
├── gpt54/  gpt52/  claude/  glm/  qwen/
│     ├── evaluate.py             # model-specific config + run
│     ├── <reconstructed>.csv     # RECONSTRUCTED dataset for this model
│     ├── row_mapping_100*.txt    # frozen 100-pair mapping used in the paper
│     └── results_reproduced.csv  # written when you run evaluate.py
```

| Model  | Reconstructed CSV                  | Row-mapping file |
|--------|------------------------------------|------------------|
| gpt54  | `inference_codex_1_79_compiled.csv`| `row_mapping_100.txt` |
| gpt52  | `inference_codex_1-79.csv`         | `row_mapping_100.txt` |
| claude | `refractory_hea_data.csv`          | `row_mapping_100.txt` |
| glm    | `refractory_data.csv`              | `row_mapping_100.txt` |
| qwen   | `alloy_properties.csv`             | `row_mapping_100_table1_vs_alloy_properties.txt` |

## Run

```bash
python3 run_all.py            # all five models
python3 claude/evaluate.py    # one model
```

## Method

The frozen mapping file lists 100 `(original_line, reconstructed_line)` pairs.
For each pair the four properties are read from `table_1.csv` and from the
model's reconstructed CSV, and

```
MAE(property) = mean( |orig - recon| )  over pairs where BOTH values are numeric.
```

### Why each model has its own row reader

The reconstructed CSVs differ in column headers and formatting, and the original
mapping generators parsed cells slightly differently. To reproduce the published
numbers *exactly*, each `evaluate.py` selects the reader that matches its
generator (all provided by `hea_lib.py`):

- **claude** — columns by header name, first-number cell parsing,
  `skipinitialspace=False`.
- **glm / qwen** — columns by header name, first-number parsing,
  `skipinitialspace=True` (their phase column contains quoted commas, which would
  otherwise shift later columns).
- **gpt54** — fixed forward indices (6,7,8,9); `safe_float` (a cell that is not a
  clean number, e.g. `"512 (compression)"`, is treated as missing) for
  sigma_y/sigma_max/epsilon; first-number parse for the `E` column (handles
  ground-truth entries like `"135 (203)"`).
- **gpt52** — ground truth by forward indices (6,7,8,9); reconstructed file by
  indices counted **from the end** of each row (its comma-containing phase column
  splits some rows, so the four property columns are read as the last four
  fields). Codex first-number parser throughout.

Line numbers are 1-based with the header on line 1 (first data row = line 2),
matching how the mappings were generated.

## Expected values (from the paper) — all reproduce exactly

| Property        | GPT-5.4  | GPT-5.2 | Claude Opus 4.6 | GLM 5V Turbo | Qwen-3.5 |
|-----------------|----------|---------|-----------------|--------------|----------|
| sigma_Y (MPa)   | 137.525  | 40.452  | 0.2949          | 119.0914     | 122.2735 |
| sigma_max (MPa) | 71.938   | 57.550  | 1.8136          | 1.8750       | 3.4800   |
| epsilon (%)     | 0.646    | 1.039   | 0.2253          | 0.5542       | 46.0483  |
| E (GPa)         | 56.433   | 19.500  | 4.1333          | 2.9091       | 8.9231   |
