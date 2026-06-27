#!/usr/bin/env python3
"""Reproduce the GPT-5.2 column of Table 2 (MeltpoolNet benchmark).

Run:  python3 evaluate.py
Expected: beam D 73.81/79.49/76.54, Hatch 100/42.86/60.00,
          E 100/100/100, depth 78.57/23.40/36.06, d/w 28.57/13.79/18.60,
          melting T MAE 172.60 K.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import meltpoolnet_lib as lib

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "meltpoolnet_regression.csv",
    "reconstructed": HERE / "extracted_data_codex.csv",
    # row numbers are 1-based file lines (header = line 1)
    "pairs": lib.mapping_header_based(
        HERE / "row_mapping_original_to_reconstructed.csv",
        "row_meltpoolnet_regression", "row_extracted_data_codex",
    ),
    # GPT-5.2 extraction reports beam D in metres and hatch in mm; the ground
    # truth uses mm and micrometres respectively (a factor of 1000).
    "fields": {
        "beam D": {"ocol": "beam D", "rcol": "beam D",
                   "scale": lib.scale_div1000, "match": lib.match_abs(1e-6)},
        "Hatch spacing": {"ocol": "Hatch spacing", "rcol": "Hatch spacing",
                          "scale": lib.scale_div1000, "match": lib.match_abs(0.001)},
        "E (J/mm)": {"ocol": "E (J/mm)", "rcol": "E (J/mm)",
                     "match": lib.match_rel(0.01)},
        "depth of meltpool": {"ocol": "depth of meltpool", "rcol": "depth of meltpool",
                              "match": lib.match_abs(0.01)},
        "d/w": {"ocol": "d/w", "rcol": "d/w", "match": lib.match_rel(0.01)},
    },
    "melting": {"ocol": "melting T", "rcol": "melting T"},
}

if __name__ == "__main__":
    lib.run(CONFIG, "GPT-5.2")
