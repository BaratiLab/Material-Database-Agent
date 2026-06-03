# Quick Start Guide - Marker PDFs MCP Server

## What This Does

Converts PDF files from `/home/ash/matdatabase/PDFs/` to markdown in `/home/ash/matdatabase/pdfs_markdown/` with **images enabled**.

## Key Points

✅ Processes PDFs **one at a time** (sequential processing)  
✅ **Images are enabled** by default  
✅ Maintains folder structure (folder 1 → pdfs_markdown/1/)  
✅ Processes all PDFs in each folder  

## Quick Commands

### 1. Start the Server

```bash
cd /home/ash/matdatabase/marker_pdfs
export MARKER_CHUNK_CONVERT_BIN=/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert
.venv/bin/python main.py
```

**Note:** Use `.venv/bin/python` to run with the correct virtual environment.

### 2. Process Specific Folders

Use the MCP tool `convert_pdfs_to_markdown` with:
```json
{
  "folder_numbers": ["1", "2", "12"]
}
```

### 3. Process ALL Folders

Use the MCP tool `convert_all_pdfs_to_markdown` (no folder list needed)

## Directory Mapping

| Input | Output |
|-------|--------|
| `/home/ash/matdatabase/PDFs/1/file1.pdf` | `/home/ash/matdatabase/pdfs_markdown/1/file1/` |
| `/home/ash/matdatabase/PDFs/12/file12.pdf` | `/home/ash/matdatabase/pdfs_markdown/12/file12/` |
| `/home/ash/matdatabase/PDFs/12/supp12.pdf` | `/home/ash/matdatabase/pdfs_markdown/12/supp12/` |

## Available Folders

37 folders found in `/home/ash/matdatabase/PDFs/`:
- Numbered folders: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 33, 34, 35, 36, 37, 38, 39

## Troubleshooting

### If marker_chunk_convert is not found:
```bash
# Option 1: Use the existing marker installation
export MARKER_CHUNK_CONVERT_BIN=/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert

# Option 2: Install locally
cd /home/ash/matdatabase/marker_pdfs
uv sync
```

### Check if the server is working:
```bash
cd /home/ash/matdatabase/marker_pdfs
python -c "from main import _resolve_marker_chunk_convert; print(_resolve_marker_chunk_convert())"
```

## Logs

Each PDF conversion creates a log file:
```
/home/ash/matdatabase/pdfs_markdown/{folder_number}/{pdf_name}_marker.log
```

Check these logs if a conversion fails.
