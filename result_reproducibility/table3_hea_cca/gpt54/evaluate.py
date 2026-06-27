#!/usr/bin/env python3
"""Reproduce the GPT-5.4 column of Table 3 (HEA/CCA benchmark).

Run:  python3 evaluate.py
Expected: sigma_Y 137.525, sigma_max 71.938, epsilon 0.646, E 56.433.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hea_lib as lib

# GPT-5.4 mapping generator used fixed FORWARD column indices (both files share
# the layout: composition, folder, phases, rho, HV, test, sigma_y, sigma_max,
# epsilon, E -> property indices 6,7,8,9), safe_float for sigma_y/sigma_max/
# epsilon, and a first-number parse for the E column (handles "135 (203)").
IDX = {"sigma_y": 6, "sigma_max": 7, "epsilon": 8, "E": 9}

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "table_1.csv",
    "reconstructed": HERE / "inference_codex_1_79_compiled.csv",
    "mapping": HERE / "row_mapping_100.txt",
    "orig_reader": lib.make_forward_index_reader(IDX, lib.safe_float, e_special=True),
    "recon_reader": lib.make_forward_index_reader(IDX, lib.safe_float, e_special=False),
}

if __name__ == "__main__":
    lib.run(CONFIG, "GPT-5.4")
