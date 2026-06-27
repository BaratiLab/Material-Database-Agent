#!/usr/bin/env python3
"""Reproduce the GPT-5.4 column of Table 2 (MeltpoolNet benchmark).

Run:  python3 evaluate.py
Expected: beam D 35.71/45.45/40.00, Hatch 87.00/100.00/93.05,
          E 100/100/100, depth 78.38/31.52/44.96, d/w 75.00/75.00/75.00,
          melting T MAE 82.88 K.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import meltpoolnet_lib as lib

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "meltpoolnet_regression.csv",
    "reconstructed": HERE / "extracted_data_codex_gpt54.csv",
    # GPT-5.4 mapping uses 1-based DATA-row indices (header excluded);
    # only the first 100 pairs are used.
    "pairs": lib.mapping_data_index_based(
        HERE / "row_mapping_original_to_reconstructed_codex_gpt54.csv",
        "original_row", "reconstructed_row",
    ),
    # GPT-5.4 extraction uses the same numeric scale as the ground truth, so no
    # unit conversion is applied. Hatch spacing is compared near-exactly.
    "fields": {
        "beam D": {"ocol": "beam D", "rcol": "beam D", "match": lib.match_abs(0.01)},
        "Hatch spacing": {"ocol": "Hatch spacing", "rcol": "Hatch spacing",
                          "match": lib.match_abs(0.01)},
        "E (J/mm)": {"ocol": "E (J/mm)", "rcol": "E (J/mm)",
                     "match": lib.match_rel(0.01)},
        "depth of meltpool": {"ocol": "depth of meltpool", "rcol": "depth of meltpool",
                              "match": lib.match_abs(0.01)},
        "d/w": {"ocol": "d/w", "rcol": "d/w", "match": lib.match_rel(0.01)},
    },
    "melting": {"ocol": "melting T", "rcol": "melting T"},
}

if __name__ == "__main__":
    lib.run(CONFIG, "GPT-5.4")
