#!/usr/bin/env python3
"""Reproduce the GLM 5V Turbo column of Table 3 (HEA/CCA benchmark).

Run:  python3 evaluate.py
Expected: sigma_Y 119.0914, sigma_max 1.8750, epsilon 0.5542, E 2.9091.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hea_lib as lib

ORIG_COLS = {"sigma_y": "sigma_y (MPa)", "sigma_max": "sigma_max (MPa)",
             "epsilon": "epsilon (%)", "E": "E (GPa)"}
RECON_COLS = {"sigma_y": "sigma_Y", "sigma_max": "sigma_max",
              "epsilon": "epsilon", "E": "E"}

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "table_1.csv",
    "reconstructed": HERE / "refractory_data.csv",
    "mapping": HERE / "row_mapping_100.txt",
    # GLM mapping generator: header-name columns, first-number parsing,
    # skipinitialspace=True (the phase column contains quoted commas).
    "orig_reader": lib.make_header_reader(ORIG_COLS, skipinitialspace=True),
    "recon_reader": lib.make_header_reader(RECON_COLS, skipinitialspace=True),
}

if __name__ == "__main__":
    lib.run(CONFIG, "GLM 5V Turbo")
