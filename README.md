# Material Database Agent

This repository contains the PDF inputs and local tooling needed to reproduce the Material Database Agent (MDA) benchmark workflows.

MDA is a multimodal, agentic literature-mining workflow. It converts scientific PDFs into markdown and extracted figures, sends each paper's parsed content to specialized subagents, writes one intermediate JSON file per paper, and then aggregates those JSON files into a final CSV material database.

## Reproducing The Paper's Benchmark Tables

The [`result_reproducibility/`](result_reproducibility/) folder lets anyone regenerate the two quantitative benchmark tables from the paper directly from the released data, with **no LLM calls and no third-party Python packages** (standard library only, Python 3.8+).

It covers both benchmark tables across all five backbone models:

| Folder   | Model            | Agent environment |
|----------|------------------|-------------------|
| `gpt54`  | GPT-5.4          | Codex CLI         |
| `gpt52`  | GPT-5.2          | Codex CLI         |
| `claude` | Claude Opus 4.6  | Claude Code       |
| `glm`    | GLM 5V Turbo     | Claude Code       |
| `qwen`   | Qwen-3.5-397B    | Claude Code       |

For each table/model the folder ships the original ground-truth dataset, the model's reconstructed dataset, the frozen 100-pair manual row mapping used in the paper, and an `evaluate.py` that re-reads those artifacts and recomputes the published metrics:

- [`result_reproducibility/table2_meltpoolnet/`](result_reproducibility/table2_meltpoolnet/) - Table 2: precision / recall / F1 for selected MeltpoolNet fields plus melting-temperature MAE.
- [`result_reproducibility/table3_hea_cca/`](result_reproducibility/table3_hea_cca/) - Table 3: MAE of four mechanical properties for the HEA/CCA benchmark.

```bash
# Table 2 - all five models
cd result_reproducibility/table2_meltpoolnet && python3 run_all.py

# Table 3 - all five models
cd ../table3_hea_cca && python3 run_all.py

# Or a single cell, e.g. the Claude column of Table 3
cd result_reproducibility/table3_hea_cca/claude && python3 evaluate.py
```

Each run writes a `results_reproduced.csv` next to the script. All twenty table cells (10 model/table combinations across both tables) reproduce the published numbers exactly. See [`result_reproducibility/README.md`](result_reproducibility/README.md) and each table's own `README.md` for per-cell expected values and the exact matching rules.

## Repository Contents

- `PDFs_meltpoolnet/` - paper PDFs used for the MeltpoolNet benchmark.
- `PDFs_refrac/` - paper PDFs used for the refractory HEA/CCA benchmark.
- `BulkModulus_test_database_MPPolak_DMorgan.xlsx` - bulk modulus benchmark spreadsheet used for the prior text-only comparison.
- `marker_pdfs/` - copied local MCP server for converting PDF folders to markdown with image extraction. The virtual environment from `/home/ash/matdatabase/marker_pdfs/.venv` was intentionally not copied.
- `result_reproducibility/` - self-contained, dependency-free scripts and data that deterministically recompute the paper's two quantitative benchmark tables (Table 2 and Table 3) for all five backbone models. See [Reproducing The Paper's Benchmark Tables](#reproducing-the-papers-benchmark-tables).

## Marker PDFs MCP Server

The copied MCP server is in `marker_pdfs/`. It exposes two tools:

- `convert_pdfs_to_markdown` - process selected numbered folders.
- `convert_all_pdfs_to_markdown` - process every folder under the configured input directory.

The server expects an input directory containing numbered subfolders. Each subfolder can contain one or more PDF files. It writes markdown, extracted images, and log files to the configured output directory while preserving the folder structure.

### Install Dependencies

From the repository root:

```bash
cd /home/ash/matdatabase/Material-Database-Agent/marker_pdfs
uv sync
```

This creates a new local `.venv/` inside the copied server directory. The venv is intentionally generated locally instead of checked into the repository.

The server also needs `marker_chunk_convert`. If you already have the marker environment from the original workspace, use:

```bash
export MARKER_CHUNK_CONVERT_BIN=/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert
```

If not, install `marker-pdf` through `uv sync` and make sure `marker_chunk_convert` is available on `PATH`, or set `MARKER_CHUNK_CONVERT_BIN` to its full path.

### Run Manually

For the MeltpoolNet PDF set:

```bash
cd /home/ash/matdatabase/Material-Database-Agent/marker_pdfs
export PDF_BASE_DIR=/home/ash/matdatabase/Material-Database-Agent/PDFs_meltpoolnet
export OUTPUT_BASE_DIR=/home/ash/matdatabase/Material-Database-Agent/pdfs_markdown_meltpoolnet
export MARKER_CHUNK_CONVERT_BIN=/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert
.venv/bin/python main.py
```

For the refractory HEA/CCA PDF set, change the two dataset paths:

```bash
export PDF_BASE_DIR=/home/ash/matdatabase/Material-Database-Agent/PDFs_refrac
export OUTPUT_BASE_DIR=/home/ash/matdatabase/Material-Database-Agent/pdfs_markdown_refrac
```

If `PDF_BASE_DIR` and `OUTPUT_BASE_DIR` are not set, the copied server keeps the original defaults:

- Input: `/home/ash/matdatabase/PDFs`
- Output: `/home/ash/matdatabase/pdfs_markdown`

### Use From Claude Code

Claude Code can run this as a local stdio MCP server. Project scope writes a shareable `.mcp.json`; local scope stores the setting privately in your Claude config.

MeltpoolNet:

```bash
cd /home/ash/matdatabase/Material-Database-Agent
claude mcp add --transport stdio --scope project \
  --env PDF_BASE_DIR=/home/ash/matdatabase/Material-Database-Agent/PDFs_meltpoolnet \
  --env OUTPUT_BASE_DIR=/home/ash/matdatabase/Material-Database-Agent/pdfs_markdown_meltpoolnet \
  --env MARKER_CHUNK_CONVERT_BIN=/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert \
  marker-pdfs-meltpoolnet -- \
  /home/ash/matdatabase/Material-Database-Agent/marker_pdfs/.venv/bin/python \
  /home/ash/matdatabase/Material-Database-Agent/marker_pdfs/main.py
```

Refractory HEA/CCA:

```bash
cd /home/ash/matdatabase/Material-Database-Agent
claude mcp add --transport stdio --scope project \
  --env PDF_BASE_DIR=/home/ash/matdatabase/Material-Database-Agent/PDFs_refrac \
  --env OUTPUT_BASE_DIR=/home/ash/matdatabase/Material-Database-Agent/pdfs_markdown_refrac \
  --env MARKER_CHUNK_CONVERT_BIN=/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert \
  marker-pdfs-refrac -- \
  /home/ash/matdatabase/Material-Database-Agent/marker_pdfs/.venv/bin/python \
  /home/ash/matdatabase/Material-Database-Agent/marker_pdfs/main.py
```

Useful Claude Code MCP commands:

```bash
claude mcp list
claude mcp get marker-pdfs-meltpoolnet
```

Inside Claude Code, run `/mcp` to inspect server status and available tools.

### Use From Codex

Codex MCP servers are configured in `~/.codex/config.toml` or in a trusted project at `.codex/config.toml`.

Example Codex config for MeltpoolNet:

```toml
[mcp_servers.marker_pdfs_meltpoolnet]
command = "/home/ash/matdatabase/Material-Database-Agent/marker_pdfs/.venv/bin/python"
args = ["/home/ash/matdatabase/Material-Database-Agent/marker_pdfs/main.py"]
startup_timeout_sec = 20
tool_timeout_sec = 3600

[mcp_servers.marker_pdfs_meltpoolnet.env]
PDF_BASE_DIR = "/home/ash/matdatabase/Material-Database-Agent/PDFs_meltpoolnet"
OUTPUT_BASE_DIR = "/home/ash/matdatabase/Material-Database-Agent/pdfs_markdown_meltpoolnet"
MARKER_CHUNK_CONVERT_BIN = "/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert"
```

Example Codex config for refractory HEA/CCA:

```toml
[mcp_servers.marker_pdfs_refrac]
command = "/home/ash/matdatabase/Material-Database-Agent/marker_pdfs/.venv/bin/python"
args = ["/home/ash/matdatabase/Material-Database-Agent/marker_pdfs/main.py"]
startup_timeout_sec = 20
tool_timeout_sec = 3600

[mcp_servers.marker_pdfs_refrac.env]
PDF_BASE_DIR = "/home/ash/matdatabase/Material-Database-Agent/PDFs_refrac"
OUTPUT_BASE_DIR = "/home/ash/matdatabase/Material-Database-Agent/pdfs_markdown_refrac"
MARKER_CHUNK_CONVERT_BIN = "/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert"
```

You can also add stdio servers with `codex mcp add`, then inspect active servers from the Codex TUI with `/mcp`.

## Running The MDA Workflow

1. Install the MCP server dependencies with `uv sync`.
2. Configure either the MeltpoolNet or refractory HEA/CCA MCP server in Claude Code or Codex.
3. Ask the main agent to call `convert_all_pdfs_to_markdown`, or call `convert_pdfs_to_markdown` with a selected folder list such as `["1", "2", "12"]`.
4. After conversion, each output folder contains markdown, figures, and a marker log.
5. Ask doc-writer subagents to read each output paper folder and write one `inference.txt` JSON file per folder.
6. Ask a csv-writer subagent to read all `inference.txt` files and consolidate them into the final CSV.

## Subagents In Claude Code

Claude Code supports built-in and custom subagents. Custom subagents are Markdown files with YAML frontmatter plus a system prompt body.

Recommended setup:

```text
.claude/agents/doc-writer.md
.claude/agents/csv-writer.md
```

Project-scoped agents live in `.claude/agents/`. User-scoped agents live in `~/.claude/agents/`.

Minimal `doc-writer` example:

```markdown
---
name: doc-writer
description: Extracts structured material data from one parsed paper folder.
tools: Read, Grep, Glob, Write
model: inherit
---

Read every markdown and image file in the assigned paper folder together.
Extract only material data supported by the source files.
Write one inference.txt file containing valid JSON in the requested schema.
Return a short summary of extracted rows and any uncertain fields.
```

Minimal `csv-writer` example:

```markdown
---
name: csv-writer
description: Consolidates material JSON inference files into a clean CSV.
tools: Read, Grep, Glob, Write
model: inherit
---

Read every inference.txt file requested by the main agent.
Validate JSON structure, normalize units where instructed, preserve nulls for missing data, and write one CSV with the requested column order.
Do not call PDF conversion MCP tools during CSV aggregation.
```

Use `/agents` in Claude Code to create, edit, inspect, and manage these subagents. You can invoke them naturally:

```text
Use the doc-writer subagent on every folder in pdfs_markdown_meltpoolnet, one folder per subagent, then summarize which folders produced inference.txt.
```

Claude Code can also use `@` mentions for a specific agent, and `claude --agent <name>` can start a session where the main thread itself uses that agent's prompt. Subagents start with isolated context, inherit available tools by default, can run in foreground or background, and cannot spawn nested subagents.

Official docs:

- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/mcp

## Subagents In Codex

Codex supports subagent workflows when you explicitly ask for parallel agents. It does not spawn subagents automatically. This is useful for MDA because each paper folder can be processed independently and the main thread only needs the final summaries.

Project-scoped custom agents live in:

```text
.codex/agents/
```

Personal custom agents live in:

```text
~/.codex/agents/
```

Each custom agent is a standalone TOML file. Required fields are `name`, `description`, and `developer_instructions`.

Example `.codex/agents/doc-writer.toml`:

```toml
name = "doc-writer"
description = "Extracts structured material data from one parsed paper folder."
model = "gpt-5.5"
model_reasoning_effort = "medium"
developer_instructions = """
Read every markdown and image file in the assigned paper folder together.
Extract only material data supported by the source files.
Write one inference.txt file containing valid JSON in the requested schema.
Return a short summary of extracted rows and uncertain fields.
"""
```

Example `.codex/agents/csv-writer.toml`:

```toml
name = "csv-writer"
description = "Consolidates material JSON inference files into a clean CSV."
model = "gpt-5.5"
model_reasoning_effort = "medium"
developer_instructions = """
Read inference.txt files, validate JSON, normalize units where instructed, preserve nulls for missing data, and write one CSV with the requested column order.
Do not call PDF conversion MCP tools during CSV aggregation.
"""
```

Example prompt:

```text
Spawn one doc-writer subagent per folder in pdfs_markdown_meltpoolnet. Each subagent should write inference.txt in its assigned folder. Wait for all agents, then summarize completed and failed folders.
```

Use `/agent` in the Codex CLI to inspect and switch between active agent threads. You can tune concurrency in Codex config:

```toml
[agents]
max_threads = 6
max_depth = 1
```

Official docs:

- https://developers.openai.com/codex/subagents
- https://developers.openai.com/codex/mcp

## Datasets Used

### MeltpoolNet Benchmark

The MeltpoolNet benchmark comes from Akbari et al., "MeltpoolNet: Melt pool characteristic prediction in Metal Additive Manufacturing using machine learning," Additive Manufacturing 55, 102817 (2022).

This benchmark is an experimental dataset for powder bed fusion / metal additive manufacturing. It contains melt pool characteristics, processing parameters, and material data. The relevant fields include laser power, scanning velocity, hatch spacing, layer thickness, beam diameter, meltpool depth/width/length, density, melting point, specific heat capacity, thermal conductivity, absorptivity, material composition, particle size, paper ID, title, and DOI.

The ground-truth MeltpoolNet table used for evaluation has 789 rows. The repository currently contains `PDFs_meltpoolnet/` with 37 numbered paper folders and 39 PDF files, including supplemental PDFs for some papers.

### Refractory HEA/CCA Benchmark

The refractory benchmark is a database of high-entropy alloys and complex concentrated alloys. It targets mechanical-property extraction from source papers and includes alloy composition, reported phases, density, Vickers hardness, test type, yield strength, ultimate strength, elongation, and Young's modulus.

The original HEA/CCA ground-truth database contains roughly 370 rows, with 366 original rows/datapoints used for evaluation. Unlike MeltpoolNet, this dataset is heavily graphical: many values are reported in stress-strain curves, bar charts, plots, and annotated micrographs rather than clean tables.

The repository currently contains `PDFs_refrac/` with 74 folders and 72 PDF files. Folders `no_12` and `no_41` are present but do not contain PDFs in this checkout.

### Evaluation Mapping

For both benchmarks, extracted databases are evaluated against manually mapped ground-truth row pairs. MeltpoolNet rows are mapped using material composition, laser power, scan velocity, layer thickness, and paper DOI. HEA/CCA rows are mapped using alloy composition, source paper number, and hardness value.

### Bulk Modulus Text Benchmark

This workflow also includes a comparison against the Polak and Morgan (2024) ChatExtract benchmark for text-based extraction of bulk modulus values. This benchmark is not one of the two main multimodal MDA datasets; it is used as a previous-generation baseline for constrained text-only extraction.

The local spreadsheet is `BulkModulus_test_database_MPPolak_DMorgan.xlsx`. It contains two sheets:

- `Positive` - 179 labeled rows from 63 papers. Columns are `passage`, `sentence`, `previous_sentence`, `title`, `doi`, `material`, `value`, and `unit`. These rows contain positive examples where a material and bulk modulus value are annotated. All units are `GPa`; the parsed numeric values range from 9.6 to 843.0 GPa.
- `Negative` - 1,912 rows from the same 63 papers. Columns are `passage`, `sentence`, `previous_sentence`, `title`, and `doi`. These rows provide paper context that should not be extracted as positive material-bulk-modulus records.

The bulk modulus extraction workflow uses this spreadsheet with ten independent subagents. The prompt instructs the agents to read each row of the `passage` column, group rows by shared DOI values, and extract the unique material and bulk modulus values for each row. Opus 4.6 is evaluated on this benchmark at 99.23% precision and 100% recall, compared with the 2024 ChatExtract GPT-4 result of 90.8% precision and 87.7% recall.
