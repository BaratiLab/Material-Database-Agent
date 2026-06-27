"""
Shared evaluation library for the MeltpoolNet benchmark (Table 2 of the paper).

For each model we are given three artifacts:

  * the ORIGINAL ground-truth dataset  (meltpoolnet_regression.csv, shared)
  * a RECONSTRUCTED dataset extracted by the MDA pipeline for that model
  * a frozen ROW MAPPING that pairs 100 ground-truth rows with 100 extracted rows
    (the manual mapping that was done for the paper)

This library re-computes, strictly from those artifacts, the numbers reported in
Table 2:

  * precision / recall / F1 for: beam D, Hatch spacing, E (J/mm),
    depth of meltpool, d/w
  * mean absolute error (MAE) of melting temperature T

Classification (per mapped row pair, per field), following Sierepeklis & Cole
(2022), https://doi.org/10.1038/s41597-022-01752-1 :

  TP : original has a value, reconstructed has a value, they match (within tol)
  FP : (a) both present but mismatch, or (b) original empty but reconstructed has a value
  FN : original has a value, reconstructed empty
  both empty -> not counted

Each model only differs in (i) the row-mapping file format and indexing
convention, and (ii) the per-field numeric tolerance / unit handling. Those
differences are supplied as a CONFIG dict by each model's evaluate.py; the
metric maths below is identical for every model.
"""
from __future__ import annotations

import csv
from pathlib import Path

# Strings that count as "no value" in either dataset.
MISSING = {"", "?", "nan", "na", "n/a", "none", "null"}

# Canonical field order as printed in Table 2.
FIELDS = ["beam D", "Hatch spacing", "E (J/mm)", "depth of meltpool", "d/w"]


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def parse_float(value):
    """Return float(value), or None for empty / non-numeric / missing markers."""
    if value is None:
        return None
    s = str(value).strip().replace("−", "-")  # normalise unicode minus
    if s.lower() in MISSING:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))


def col_index(header, name):
    """Index of a column matched case-insensitively after stripping whitespace.

    Header cells in these CSVs carry inconsistent leading/trailing spaces, so an
    exact match is unreliable.
    """
    want = name.strip().lower()
    for i, cell in enumerate(header):
        if cell.strip().lower() == want:
            return i
    raise KeyError(f"column {name!r} not found in header")


# --------------------------------------------------------------------------- #
# Matching predicates (built by each model's config)
# --------------------------------------------------------------------------- #
def match_abs(tol):
    """Match if |orig - recon| <= tol."""
    return lambda o, r: abs(o - r) <= tol


def match_rel(tol):
    """Match within a relative tolerance; both-near-zero counts as a match."""
    def predicate(o, r):
        if abs(o) < 1e-12 and abs(r) < 1e-12:
            return True
        denom = max(abs(o), abs(r))
        if denom < 1e-12:
            return True
        return abs(o - r) / denom <= tol
    return predicate


def scale_div1000(value):
    """Convert an original value to the reconstructed file's SI scale.

    Used for models whose extraction reports beam diameter in metres (vs mm in
    the ground truth) and hatch spacing in mm (vs micrometres in the ground
    truth); both are a factor of 1000.
    """
    return value / 1000.0


def scale_identity(value):
    return value


# --------------------------------------------------------------------------- #
# Row-mapping parsers -> list of (orig_list_index, recon_list_index)
#
# `*_list_index` indexes the list returned by load_csv(), where element 0 is the
# header and element 1 is the first data row.
# --------------------------------------------------------------------------- #
def mapping_header_based(path, orig_col, recon_col, limit=100, comment="#"):
    """Mapping whose row numbers are 1-based FILE LINES (header == line 1).

    Therefore data list index = row_number - 1. Used by claude, gpt52, glm, qwen.
    """
    rows = load_csv(path)
    pairs = []
    header_seen = False
    oi = ri = None
    for row in rows:
        if not row or (comment and row[0].lstrip().startswith(comment)):
            continue
        if not header_seen:
            header_seen = True
            oi = col_index(row, orig_col)
            ri = col_index(row, recon_col)
            continue
        try:
            o = int(row[oi])
            r = int(row[ri])
        except (ValueError, IndexError):
            continue
        pairs.append((o - 1, r - 1))
        if len(pairs) >= limit:
            break
    return pairs


def mapping_data_index_based(path, orig_col, recon_col, limit=100):
    """Mapping whose row numbers are 1-based DATA rows (header excluded).

    Therefore data list index = row_number (list[1] is the first data row).
    Used by gpt54. Only the first `limit` pairs are used.
    """
    rows = load_csv(path)
    oi = col_index(rows[0], orig_col)
    ri = col_index(rows[0], recon_col)
    pairs = []
    for row in rows[1:]:
        try:
            o = int(row[oi])
            r = int(row[ri])
        except (ValueError, IndexError):
            continue
        pairs.append((o, r))
        if len(pairs) >= limit:
            break
    return pairs


# --------------------------------------------------------------------------- #
# Core evaluation
# --------------------------------------------------------------------------- #
def evaluate(config, here):
    """Run the full Table-2 evaluation for one model.

    `config` keys:
        original         : path to meltpoolnet_regression.csv
        reconstructed    : path to the model's extracted CSV
        pairs            : list of (orig_idx, recon_idx)
        fields           : {field_name: {ocol, rcol, scale, match}}
        melting          : {ocol, rcol}
    `here` is only used for resolving relative output paths.

    Returns (results, mae, n_mae) where results[field] = (tp, fp, fn).
    """
    O = load_csv(config["original"])
    R = load_csv(config["reconstructed"])
    pairs = config["pairs"]

    results = {}
    for field, fc in config["fields"].items():
        oi = col_index(O[0], fc["ocol"])
        ri = col_index(R[0], fc["rcol"])
        scale = fc.get("scale", scale_identity)
        match = fc["match"]
        tp = fp = fn = 0
        for o_idx, r_idx in pairs:
            try:
                ov = parse_float(O[o_idx][oi])
                rv = parse_float(R[r_idx][ri])
            except IndexError:
                continue
            o_has, r_has = ov is not None, rv is not None
            if o_has and r_has:
                tp += 1 if match(scale(ov), rv) else 0
                fp += 0 if match(scale(ov), rv) else 1
            elif o_has and not r_has:
                fn += 1
            elif not o_has and r_has:
                fp += 1
        results[field] = (tp, fp, fn)

    # melting temperature MAE
    mc = config["melting"]
    oi = col_index(O[0], mc["ocol"])
    ri = col_index(R[0], mc["rcol"])
    total = 0.0
    n = 0
    for o_idx, r_idx in pairs:
        try:
            ov = parse_float(O[o_idx][oi])
            rv = parse_float(R[r_idx][ri])
        except IndexError:
            continue
        if ov is not None and rv is not None:
            total += abs(ov - rv)
            n += 1
    mae = total / n if n else None
    return results, mae, n


def precision_recall_f1(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * p * r / (p + r)) if (p + r) else 0.0
    return p, r, f1


def run(config, model_name, write_csv=True):
    """Evaluate, print a Table-2 style summary, and optionally write results CSV."""
    here = Path(config.get("here", "."))
    results, mae, n = evaluate(config, here)

    print(f"\nMeltpoolNet benchmark (Table 2) -- {model_name}")
    print(f"  mapped row pairs: {len(config['pairs'])}")
    print(f"  {'field':18s} {'TP':>4} {'FP':>4} {'FN':>4} {'P%':>7} {'R%':>7} {'F1%':>7}")
    out_rows = [["field", "TP", "FP", "FN", "precision_pct", "recall_pct", "f1_pct"]]
    for field in FIELDS:
        tp, fp, fn = results[field]
        p, r, f1 = precision_recall_f1(tp, fp, fn)
        print(f"  {field:18s} {tp:>4} {fp:>4} {fn:>4} "
              f"{p*100:>7.2f} {r*100:>7.2f} {f1*100:>7.2f}")
        out_rows.append([field, tp, fp, fn,
                         f"{p*100:.2f}", f"{r*100:.2f}", f"{f1*100:.2f}"])
    print(f"  melting T MAE: {mae:.2f} K  (n = {n} pairs with both values)")
    out_rows.append(["melting_T_MAE_K", "", "", "", "", "", f"{mae:.4f}"])
    out_rows.append(["melting_T_MAE_n_pairs", "", "", "", "", "", str(n)])

    if write_csv:
        out_path = here / "results_reproduced.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(out_rows)
        print(f"  wrote {out_path}")
    return results, mae, n
