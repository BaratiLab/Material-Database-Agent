# Marker PDFs MCP Server

This MCP server processes individual PDF files one at a time from numbered folders in `/home/ash/matdatabase/PDFs` and converts them to markdown with image extraction enabled.

## Features

- Processes PDFs one file at a time from numbered folders
- Outputs markdown to corresponding folders in `/home/ash/matdatabase/pdfs_markdown`
- Image extraction is enabled by default
- Supports processing specific folders or all folders at once

## Directory Structure

- Input: `/home/ash/matdatabase/PDFs/{folder_number}/`
- Output: `/home/ash/matdatabase/pdfs_markdown/{folder_number}/`

## Tools Available

### 1. convert_pdfs_to_markdown
Convert PDFs from specific folders to markdown.

Parameters:
- `folder_numbers`: List of folder numbers to process (e.g., ['1', '2', '12'])
- `num_devices`: Number of devices for marker conversion (default: 3)
- `num_workers`: Number of workers for marker conversion (default: 7)
- `enable_images`: Whether to enable image extraction (default: True)

### 2. convert_all_pdfs_to_markdown
Convert ALL PDFs from all folders automatically.

Parameters:
- `num_devices`: Number of devices for marker conversion (default: 3)
- `num_workers`: Number of workers for marker conversion (default: 7)
- `enable_images`: Whether to enable image extraction (default: True)

## Installation

Dependencies have been installed using `uv sync`. The virtual environment is located at `.venv/`.

## Usage

Run the server:

```bash
cd /home/ash/matdatabase/marker_pdfs
export MARKER_CHUNK_CONVERT_BIN=/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert
.venv/bin/python main.py
```

**Important:** Always use `.venv/bin/python` to ensure the virtual environment is active.

The server will expose the MCP tools for PDF to markdown conversion.
