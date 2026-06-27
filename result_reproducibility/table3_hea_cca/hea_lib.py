"""
Shared evaluation library for the HEA/CCA benchmark (Table 3 of the paper).

Inputs per model:
  * ORIGINAL ground truth          : table_1.csv (shared)
  * RECONSTRUCTED dataset           : the model's extracted CSV
  * frozen ROW MAPPING (.txt)       : 100 mapped (original_line, reconstructed_line)
                                      pairs produced for the paper

This library re-reads the frozen mapping and recomputes the mean absolute error
(MAE) for the four mechanical properties reported in Table 3:

    sigma_y   -- yield strength            (MPa)
    sigma_max -- ultimate tensile strength (MPa)
    epsilon   -- elongation / strain       (%)
    E         -- Young's modulus           (GPa)

MAE for a property is averaged only over mapped pairs where BOTH the original and
reconstructed rows report a numeric value for that property:

    MAE = (1/n) * sum_i |orig_i - recon_i|

Each model's extraction CSV is shaped differently and the row-mapping generators
that produced the paper used slightly different cell-parsing rules, so each
model supplies its own row reader (see the `make_*_reader` helpers below). A row
reader maps a CSV path to {file_line_number -> {prop -> float|None}}, where file
line numbers are 1-based with the header on line 1 (first data row = line 2,
matching how the mappings were generated).
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

PROPS = ["sigma_y", "sigma_max", "epsilon", "E"]
PROP_LABELS = {
    "sigma_y": "sigma_Y (MPa)",
    "sigma_max": "sigma_max (MPa)",
    "epsilon": "epsilon (%)",
    "E": "E (GPa)",
}


# --------------------------------------------------------------------------- #
# Value parsers (chosen per model to match the original mapping generators)
# --------------------------------------------------------------------------- #
def first_number(text):
    """First numeric token in a cell, or None. Unicode minus normalised.

    Used by the Claude/GLM/Qwen mappings and (for the E column) the GPT-5.4
    mapping. Recovers a number even from cells like "512 (compression)".
    """
    if text is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(text).replace("−", "-"))
    return float(match.group()) if match else None


def codex_num(text):
    """First numeric token (with optional sign/exponent) after stripping ()[]
    brackets and spaces -- the parser used by the GPT-5.2 mapping generator.
    """
    if text is None:
        return None
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",
                  str(text).strip("()[] ").replace("−", "-"))
    return float(m.group()) if m else None


def safe_float(text):
    """Strip surrounding whitespace/parentheses then float(), else None.

    This is the parser used by the GPT-5.4 mapping generator for sigma_y,
    sigma_max and epsilon: a cell that is not a clean number (e.g.
    "512 (compression)") is treated as missing rather than coerced.
    """
    if text is None:
        return None
    v = text.strip().strip("()").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Row readers -> {file_line_number: {prop: float|None}}
# --------------------------------------------------------------------------- #
def make_header_reader(columns, skipinitialspace, parser=first_number):
    """Reader that locates the four property columns by header name.

    `columns` maps prop -> exact (stripped) header text.
    `skipinitialspace` must match the generator: the Claude mapping was built
    with it False; the GLM and Qwen mappings with it True (so that fields like
    `, "phase, with, commas"` parse as a single quoted cell).
    """
    def read(path):
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh, skipinitialspace=skipinitialspace))
        header = [c.strip().strip('"').strip() for c in rows[0]]
        idx = {}
        for prop, name in columns.items():
            want = name.strip().strip('"').strip()
            try:
                idx[prop] = header.index(want)
            except ValueError:
                raise KeyError(f"column {name!r} not found in {Path(path).name}")
        out = {}
        for line_no, row in enumerate(rows[1:], start=2):
            out[line_no] = {p: (parser(row[i]) if i < len(row) else None)
                            for p, i in idx.items()}
        return out
    return read


def make_forward_index_reader(indices, parser, e_special=False):
    """Reader using fixed forward column indices (GPT-5.4 mapping convention).

    `indices` maps prop -> column index. If `e_special` is set, the E column is
    parsed by taking the first number before any parenthesis (handles ground
    truth entries like "135 (203)"), matching the GPT-5.4 generator.
    """
    def read(path):
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        out = {}
        for line_no, row in enumerate(rows[1:], start=2):
            rec = {}
            for prop, i in indices.items():
                cell = row[i] if i < len(row) else ""
                if prop == "E" and e_special:
                    head = cell.split("(")[0] if "(" in cell else cell
                    val = first_number(head)
                    rec[prop] = val if val is not None else first_number(cell)
                else:
                    rec[prop] = parser(cell)
            out[line_no] = rec
        return out
    return read


def make_tail_index_reader(parser):
    """Reader using indices from the END of the row (GPT-5.2 mapping convention).

    The GPT-5.2 extraction sometimes splits the (comma-containing) phase column
    into several fields, which shifts forward indices. Counting from the end is
    robust because the four property columns are always the last four:
        E = row[-1], epsilon = row[-2], sigma_max = row[-3], sigma_y = row[-4].
    """
    tail = {"sigma_y": -4, "sigma_max": -3, "epsilon": -2, "E": -1}

    def read(path):
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        out = {}
        for line_no, row in enumerate(rows[1:], start=2):
            out[line_no] = {p: (parser(row[i]) if len(row) >= -i else None)
                            for p, i in tail.items()}
        return out
    return read


# --------------------------------------------------------------------------- #
# Mapping parsers -> list of (original_line, reconstructed_line)
# --------------------------------------------------------------------------- #
_RE_CLAUDE = re.compile(r"orig_line=(\d+)\s*\|\s*recon_line=(\d+)")
_RE_CODEX = re.compile(r"original_line=(\d+),\s*reconstructed_line=(\d+)")


def parse_mapping(path):
    """Parse either mapping text format (claude-style or codex-style)."""
    pairs = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = _RE_CLAUDE.search(line) or _RE_CODEX.search(line)
        if m:
            pairs.append((int(m.group(1)), int(m.group(2))))
    return pairs


# --------------------------------------------------------------------------- #
# Core evaluation
# --------------------------------------------------------------------------- #
def evaluate(config):
    orig = config["orig_reader"](config["original"])
    recon = config["recon_reader"](config["reconstructed"])
    pairs = parse_mapping(config["mapping"])

    sums = {p: 0.0 for p in PROPS}
    counts = {p: 0 for p in PROPS}
    for o_line, r_line in pairs:
        o = orig.get(o_line)
        r = recon.get(r_line)
        if o is None or r is None:
            continue
        for p in PROPS:
            ov, rv = o.get(p), r.get(p)
            if ov is not None and rv is not None:
                sums[p] += abs(ov - rv)
                counts[p] += 1
    mae = {p: (sums[p] / counts[p] if counts[p] else None) for p in PROPS}
    return mae, counts, len(pairs)


def run(config, model_name, write_csv=True):
    here = Path(config.get("here", "."))
    mae, counts, n_pairs = evaluate(config)

    print(f"\nHEA/CCA benchmark (Table 3) -- {model_name}")
    print(f"  mapped row pairs: {n_pairs}")
    out_rows = [["property", "MAE", "n_comparable_rows"]]
    for p in PROPS:
        val = mae[p]
        val_s = f"{val:.4f}" if val is not None else "NA"
        print(f"  {PROP_LABELS[p]:16s} MAE = {val_s:>12}  (n = {counts[p]})")
        out_rows.append([PROP_LABELS[p], val_s, counts[p]])

    if write_csv:
        out_path = here / "results_reproduced.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(out_rows)
        print(f"  wrote {out_path}")
    return mae, counts
