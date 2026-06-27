#!/usr/bin/env python3
"""Reproduce the Claude Opus 4.6 column of Table 3 (HEA/CCA benchmark).

Run:  python3 evaluate.py
Expected: sigma_Y 0.2949, sigma_max 1.8136, epsilon 0.2253, E 4.1333.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hea_lib as lib

ORIG_COLS = {"sigma_y": "sigma_y (MPa)", "sigma_max": "sigma_max (MPa)",
             "epsilon": "epsilon (%)", "E": "E (GPa)"}
RECON_COLS = {"sigma_y": "σY (MPa)", "sigma_max": "σmax (MPa)",
              "epsilon": "ε (%)", "E": "E (GPa)"}

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "table_1.csv",
    "reconstructed": HERE / "refractory_hea_data.csv",
    "mapping": HERE / "row_mapping_100.txt",
    # Claude mapping generator: header-name columns, first-number parsing,
    # default CSV parsing (skipinitialspace=False).
    "orig_reader": lib.make_header_reader(ORIG_COLS, skipinitialspace=False),
    "recon_reader": lib.make_header_reader(RECON_COLS, skipinitialspace=False),
}

if __name__ == "__main__":
    lib.run(CONFIG, "Claude Opus 4.6")
