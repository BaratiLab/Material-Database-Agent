#!/usr/bin/env python3
"""Run every model's Table 2 (MeltpoolNet) evaluation in sequence."""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for model in ["gpt54", "gpt52", "claude", "glm", "qwen"]:
    script = HERE / model / "evaluate.py"
    sys.argv = [str(script)]
    runpy.run_path(str(script), run_name="__main__")
