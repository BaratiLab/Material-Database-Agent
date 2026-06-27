#!/usr/bin/env python3
"""Reproduce the GPT-5.2 column of Table 3 (HEA/CCA benchmark).

Run:  python3 evaluate.py
Expected: sigma_Y 40.452, sigma_max 57.550, epsilon 1.039, E 19.500.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hea_lib as lib

# GPT-5.2 mapping generator read the ground truth by fixed forward indices
# (6,7,8,9) but read the reconstructed file by indices from the END of each row
# (the comma-containing phase column splits some rows, so counting from the end
# is robust). Both use the codex first-number parser.
ORIG_IDX = {"sigma_y": 6, "sigma_max": 7, "epsilon": 8, "E": 9}

CONFIG = {
    "here": HERE,
    "original": HERE.parent / "table_1.csv",
    "reconstructed": HERE / "inference_codex_1-79.csv",
    "mapping": HERE / "row_mapping_100.txt",
    "orig_reader": lib.make_forward_index_reader(ORIG_IDX, lib.codex_num),
    "recon_reader": lib.make_tail_index_reader(lib.codex_num),
}

if __name__ == "__main__":
    lib.run(CONFIG, "GPT-5.2")
