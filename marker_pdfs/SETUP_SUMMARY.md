# Marker PDFs MCP Server - Setup Summary

## What Was Created

A new MCP server has been created at `/home/ash/matdatabase/marker_pdfs/` that processes PDF files one at a time from the numbered folders in `/home/ash/matdatabase/PDFs/`.

## Directory Structure

```
/home/ash/matdatabase/
├── PDFs/                    # Input directory (existing)
│   ├── 1/
│   │   └── file1.pdf
│   ├── 2/
│   │   └── file2.pdf
│   ├── 12/
│   │   ├── file12.pdf
│   │   └── supp12.pdf
│   └── ... (39 folders total)
│
├── pdfs_markdown/           # Output directory (newly created)
│   └── (will contain numbered folders matching input)
│
└── marker_pdfs/             # New MCP server (newly created)
    ├── main.py
    ├── pyproject.toml
    ├── uv.lock
    ├── README.md
    └── SETUP_SUMMARY.md (this file)
```

## Key Features

### 1. **One File at a Time Processing**
   - The server processes each PDF file individually
   - Uses a temporary folder approach to isolate each file during conversion

### 2. **Images Enabled by Default**
   - Image extraction is enabled (disable_image_extraction=False)
   - Images will be extracted and saved alongside markdown files

### 3. **Folder-Based Organization**
   - Input: `/home/ash/matdatabase/PDFs/{folder_number}/`
   - Output: `/home/ash/matdatabase/pdfs_markdown/{folder_number}/`
   - Each folder's PDFs are processed into a corresponding output folder

### 4. **Two MCP Tools Available**

   **Tool 1: convert_pdfs_to_markdown**
   - Process specific folders
   - Parameters:
     - `folder_numbers`: List of folder numbers (e.g., ['1', '2', '12'])
     - `num_devices`: Number of GPU devices (default: 3)
     - `num_workers`: Number of workers (default: 7)
     - `enable_images`: Enable image extraction (default: True)

   **Tool 2: convert_all_pdfs_to_markdown**
   - Automatically discovers and processes ALL folders
   - Same parameters except folder_numbers (auto-detected)

## Differences from Original Marker Server

| Feature | Original Marker | New Marker PDFs |
|---------|----------------|-----------------|
| Input | Group folders (getpapers downloads) | Individual numbered folders |
| Processing | Batch processing of folder | One PDF at a time |
| Images | Disabled by default | Enabled by default |
| Output | `/marker/markdown_output/` | `/pdfs_markdown/` |
| Use Case | Research paper groups | Individual PDF collections |

## How to Run

### Option 1: Using Existing Marker Installation
```bash
export MARKER_CHUNK_CONVERT_BIN=/home/ash/matdatabase/marker/.venv/bin/marker_chunk_convert
cd /home/ash/matdatabase/marker_pdfs
python main.py
```

### Option 2: Install Dependencies Locally
```bash
cd /home/ash/matdatabase/marker_pdfs
uv sync
python main.py
```

## Example Usage

Once the server is running, you can call the MCP tools:

### Process Specific Folders
```json
{
  "tool": "convert_pdfs_to_markdown",
  "arguments": {
    "folder_numbers": ["1", "2", "12", "19"],
    "num_devices": 3,
    "num_workers": 7,
    "enable_images": true
  }
}
```

### Process All Folders
```json
{
  "tool": "convert_all_pdfs_to_markdown",
  "arguments": {
    "num_devices": 3,
    "num_workers": 7,
    "enable_images": true
  }
}
```

## Output Structure

For each PDF processed, you'll get:
```
/home/ash/matdatabase/pdfs_markdown/{folder_number}/
├── {pdf_name}/
│   ├── {pdf_name}.md          # Main markdown file
│   ├── images/                # Extracted images (if any)
│   │   ├── image_001.png
│   │   ├── image_002.png
│   │   └── ...
│   └── metadata.json          # Conversion metadata
└── {pdf_name}_marker.log      # Conversion log
```

## Notes

- The server processes PDFs sequentially (one at a time) to ensure stability
- Each PDF is temporarily copied to an isolated folder during processing
- Logs are saved for each PDF conversion for debugging
- The output directory structure mirrors the input directory structure
- Image extraction is enabled by default (can be disabled if needed)

## Folders to Process

Based on the current `/home/ash/matdatabase/PDFs/` directory, there are 39 folders:
1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 33, 34, 35, 36, 37, 38, 39

Some folders contain multiple PDFs (e.g., folder 12 has file12.pdf and supp12.pdf).
