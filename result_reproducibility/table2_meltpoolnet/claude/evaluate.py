#!/usr/bin/env python3
"""Reproduce the Claude Opus 4.6 column of Table 2 (MeltpoolNet benchmark).

Run:  python3 evaluate.py
Expected: beam D 90.48/82.61/86.38, Hatch 72.09/59.62/65.26,
          E 95.96/98.96/97.44, depth 38.96/56.60/46.15, d/w 16.18/33.33/21.79,
          melting T MAE 156.84 K.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import meltpoolnet_lib as lib

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "meltpoolnet_regression.csv",
    "reconstructed": HERE / "extracted_data_claude.csv",
    # row numbers are 1-based file lines (header = line 1)
    "pairs": lib.mapping_header_based(
        HERE / "row_mapping_original_to_reconstructed.csv",
        "original_row_number_meltpoolnet",
        "reconstructed_row_number_extracted",
    ),
    # Claude's extraction reports beam D in metres and hatch in mm; the ground
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
    lib.run(CONFIG, "Claude Opus 4.6")
