#!/usr/bin/env python3
"""Reproduce the Qwen-3.5-397B column of Table 2 (MeltpoolNet benchmark).

Run:  python3 evaluate.py
Expected: beam D 79.00/100.00/88.27, Hatch 100/100/100,
          E 100/100/100, depth 71.95/76.62/74.21, d/w 54.88/71.43/62.07,
          melting T MAE 9.97 K.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import meltpoolnet_lib as lib

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "meltpoolnet_regression.csv",
    "reconstructed": HERE / "extracted_data_qwen.csv",
    # row numbers are 1-based file lines (header = line 1)
    "pairs": lib.mapping_header_based(
        HERE / "row_mapping_100_same_rows.csv",
        "original_row", "reconstructed_row",
    ),
    # Qwen extraction uses the same numeric scale as the ground truth.
    "fields": {
        "beam D": {"ocol": "beam D", "rcol": "beam D", "match": lib.match_abs(0.01)},
        "Hatch spacing": {"ocol": "Hatch spacing", "rcol": "Hatch spacing",
                          "match": lib.match_abs(1.0)},  # ~1 micrometre on native scale
        "E (J/mm)": {"ocol": "E (J/mm)", "rcol": "E (J/mm)",
                     "match": lib.match_rel(0.01)},
        "depth of meltpool": {"ocol": "depth of meltpool", "rcol": "depth of meltpool",
                              "match": lib.match_abs(0.01)},
        "d/w": {"ocol": "d/w", "rcol": "d/w", "match": lib.match_rel(0.01)},
    },
    "melting": {"ocol": "melting T", "rcol": "melting T"},
}

if __name__ == "__main__":
    lib.run(CONFIG, "Qwen-3.5-397B")
