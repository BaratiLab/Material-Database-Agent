#!/usr/bin/env python3
"""Reproduce the Qwen-3.5-397B column of Table 3 (HEA/CCA benchmark).

Run:  python3 evaluate.py
Expected: sigma_Y 122.2735, sigma_max 3.4800, epsilon 46.0483, E 8.9231.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hea_lib as lib

ORIG_COLS = {"sigma_y": "sigma_y (MPa)", "sigma_max": "sigma_max (MPa)",
             "epsilon": "epsilon (%)", "E": "E (GPa)"}
RECON_COLS = {"sigma_y": "Yield_Strength_MPa", "sigma_max": "Ultimate_Strength_MPa",
              "epsilon": "Elongation_pct", "E": "Youngs_Modulus_GPa"}

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "table_1.csv",
    "reconstructed": HERE / "alloy_properties.csv",
    "mapping": HERE / "row_mapping_100_table1_vs_alloy_properties.txt",
    # Qwen mapping generator: header-name columns, first-number parsing,
    # skipinitialspace=True (the phase column contains quoted commas).
    "orig_reader": lib.make_header_reader(ORIG_COLS, skipinitialspace=True),
    "recon_reader": lib.make_header_reader(RECON_COLS, skipinitialspace=True),
}

if __name__ == "__main__":
    lib.run(CONFIG, "Qwen-3.5-397B")
