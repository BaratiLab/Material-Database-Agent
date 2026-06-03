#!/usr/bin/env python3
"""
MCP Server for converting individual PDFs to markdown using marker_chunk_convert.

This server processes PDF files one at a time from numbered folders and outputs markdown
to corresponding folders with images enabled.
"""

import os
import subprocess
import logging
import shutil
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("marker_pdfs_mcp")

# Create the MCP server instance
mcp = FastMCP("Marker PDFs MCP Server")

# Base directories. Defaults preserve the original local setup; environment variables
# make the copied server usable with this repository's dataset folders.
PDF_BASE_DIR = Path(os.environ.get("PDF_BASE_DIR", "/home/ash/matdatabase/PDFs"))
OUTPUT_BASE_DIR = Path(os.environ.get("OUTPUT_BASE_DIR", "/home/ash/matdatabase/pdfs_markdown"))
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ConversionResult:
    pdf_file: str
    folder_name: str
    output_dir: str
    success: bool
    log_path: Optional[str] = None
    error: Optional[str] = None


def _resolve_marker_chunk_convert() -> Optional[str]:
    """
    Resolve the marker_chunk_convert executable.

    The MCP server may run outside the marker project venv, so we try, in order:
    1) MARKER_CHUNK_CONVERT_BIN env var
    2) PATH lookup
    3) Local project venv at ../marker/.venv/bin/marker_chunk_convert
    """
    override = os.environ.get("MARKER_CHUNK_CONVERT_BIN")
    if override:
        return override

    from_path = shutil.which("marker_chunk_convert")
    if from_path:
        return from_path

    # Try the original marker project venv
    marker_venv = Path(__file__).parent.parent / "marker" / ".venv" / "bin" / "marker_chunk_convert"
    if marker_venv.exists():
        return str(marker_venv)

    return None


def convert_single_pdf_to_markdown(
    pdf_file_path: str,
    folder_name: str,
    num_devices: int = 3,
    num_workers: int = 7,
    disable_image_extraction: bool = False
) -> ConversionResult:
    """
    Convert a single PDF to markdown using marker_chunk_convert.
    
    Args:
        pdf_file_path: Path to the PDF file
        folder_name: Name of the folder (e.g., "1", "2", "12")
        num_devices: Number of devices for marker (default: 3)
        num_workers: Number of workers for marker (default: 7)
        disable_image_extraction: Whether to disable image extraction (default: False for images enabled)
    
    Returns:
        ConversionResult with output path, log path, and error details (if any).
    """
    pdf_path = Path(pdf_file_path)
    if not pdf_path.exists():
        logger.error(f"PDF file does not exist: {pdf_file_path}")
        return ConversionResult(
            pdf_file=pdf_file_path,
            folder_name=folder_name,
            output_dir=str(OUTPUT_BASE_DIR / folder_name),
            success=False,
            error=f"PDF file does not exist: {pdf_file_path}",
        )
    
    # Create output directory for this folder
    output_dir = OUTPUT_BASE_DIR / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"{pdf_path.stem}_marker.log"
    
    # Prepare environment variables
    env = os.environ.copy()
    if disable_image_extraction:
        env["DISABLE_IMAGE_EXTRACTION"] = "1"
    else:
        # Ensure images are enabled by not setting the env var
        env.pop("DISABLE_IMAGE_EXTRACTION", None)
    env["NUM_DEVICES"] = str(num_devices)
    env["NUM_WORKERS"] = str(num_workers)

    marker_bin = _resolve_marker_chunk_convert()
    
    # Ensure marker command is in PATH by adding venv bin directory
    if marker_bin:
        marker_bin_dir = Path(marker_bin).parent
        if marker_bin_dir.exists():
            current_path = env.get("PATH", "")
            venv_bin = str(marker_bin_dir.absolute())
            if venv_bin not in current_path:
                env["PATH"] = f"{venv_bin}:{current_path}"
                logger.info(f"Added {venv_bin} to PATH")
    if not marker_bin:
        message = (
            "marker_chunk_convert command not found. "
            "Install marker-pdf or set MARKER_CHUNK_CONVERT_BIN to the executable path."
        )
        logger.error(message)
        log_path.write_text(message + "\n", encoding="utf-8")
        return ConversionResult(
            pdf_file=pdf_file_path,
            folder_name=folder_name,
            output_dir=str(output_dir.absolute()),
            success=False,
            log_path=str(log_path),
            error=message,
        )
    
    # Build command - marker_chunk_convert expects a directory, so we pass the parent
    # and it will process all PDFs in that directory
    # But since we want one file at a time, we'll use marker_single instead if available
    # For now, let's use marker_chunk_convert on the folder containing just this file
    
    # Create a temporary input folder for just this PDF
    temp_input_dir = output_dir / f"temp_input_{pdf_path.stem}"
    temp_input_dir.mkdir(exist_ok=True)
    temp_pdf = temp_input_dir / pdf_path.name
    
    # Copy PDF to temp folder
    shutil.copy2(pdf_path, temp_pdf)
    
    cmd = [
        marker_bin,
        str(temp_input_dir.absolute()),
        str(output_dir.absolute())
    ]
    
    logger.info(f"Running marker conversion for {pdf_path.name} from folder {folder_name}")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info(f"Environment: DISABLE_IMAGE_EXTRACTION={env.get('DISABLE_IMAGE_EXTRACTION', 'not set (images enabled)')}, "
                f"NUM_DEVICES={env.get('NUM_DEVICES')}, NUM_WORKERS={env.get('NUM_WORKERS')}")
    
    try:
        # Run the conversion
        result = subprocess.run(
            cmd,
            env=env,
            cwd=str(output_dir),
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Conversion successful for {pdf_path.name}")
        log_path.write_text(
            "COMMAND:\n"
            + " ".join(cmd)
            + "\n\nSTDOUT:\n"
            + (result.stdout or "")
            + "\n\nSTDERR:\n"
            + (result.stderr or "")
            + "\n",
            encoding="utf-8",
        )
        
        # Clean up temp input directory
        shutil.rmtree(temp_input_dir, ignore_errors=True)
        
        return ConversionResult(
            pdf_file=pdf_file_path,
            folder_name=folder_name,
            output_dir=str(output_dir.absolute()),
            success=True,
            log_path=str(log_path),
        )
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed for {pdf_path.name}: {e}")
        log_path.write_text(
            "COMMAND:\n"
            + " ".join(cmd)
            + "\n\nEXIT CODE:\n"
            + str(e.returncode)
            + "\n\nSTDOUT:\n"
            + (e.stdout or "")
            + "\n\nSTDERR:\n"
            + (e.stderr or "")
            + "\n",
            encoding="utf-8",
        )
        # Clean up temp input directory
        shutil.rmtree(temp_input_dir, ignore_errors=True)
        
        return ConversionResult(
            pdf_file=pdf_file_path,
            folder_name=folder_name,
            output_dir=str(output_dir.absolute()),
            success=False,
            log_path=str(log_path),
            error=f"marker_chunk_convert failed with exit code {e.returncode}",
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        import traceback
        trace = traceback.format_exc()
        logger.error(trace)
        log_path.write_text(
            "COMMAND:\n"
            + " ".join(cmd)
            + "\n\nEXCEPTION:\n"
            + str(e)
            + "\n\nTRACEBACK:\n"
            + trace
            + "\n",
            encoding="utf-8",
        )
        # Clean up temp input directory
        shutil.rmtree(temp_input_dir, ignore_errors=True)
        
        return ConversionResult(
            pdf_file=pdf_file_path,
            folder_name=folder_name,
            output_dir=str(output_dir.absolute()),
            success=False,
            log_path=str(log_path),
            error=str(e),
        )


@mcp.tool()
async def convert_pdfs_to_markdown(
    folder_numbers: List[str] = Field(
        ...,
        description="List of folder numbers to process (e.g., ['1', '2', '12', '19']). Each folder in PDF_BASE_DIR will be processed."
    ),
    num_devices: int = Field(
        default=3,
        ge=1,
        description="Number of devices for marker conversion (default: 3)"
    ),
    num_workers: int = Field(
        default=7,
        ge=1,
        description="Number of workers for marker conversion (default: 7)"
    ),
    enable_images: bool = Field(
        default=True,
        description="Whether to enable image extraction (default: True)"
    )
) -> str:
    """
    Convert PDFs to markdown files one at a time with image extraction enabled.
    
    This tool takes a list of folder numbers and processes each PDF file one at a time.
    PDFs are read from PDF_BASE_DIR/{folder_number}/ and output to
    OUTPUT_BASE_DIR/{folder_number}/.
    
    Returns a summary of processed files.
    """
    logger.info(f"Starting conversion for {len(folder_numbers)} folder(s)")
    
    # Collect all PDF files from the specified folders
    all_pdfs = []
    for folder_num in folder_numbers:
        folder_path = PDF_BASE_DIR / folder_num
        if not folder_path.exists():
            logger.warning(f"Folder does not exist: {folder_path}")
            continue
        
        # Find all PDF files in this folder
        pdf_files = list(folder_path.glob("*.pdf"))
        for pdf_file in pdf_files:
            all_pdfs.append((str(pdf_file), folder_num))
    
    if not all_pdfs:
        return f"Error: No PDF files found in the specified folders: {folder_numbers}"
    
    logger.info(f"Found {len(all_pdfs)} PDF file(s) to process")
    
    # Process PDFs one at a time
    results = []
    for i, (pdf_path, folder_num) in enumerate(all_pdfs, 1):
        pdf_name = Path(pdf_path).name
        logger.info(f"Processing file {i}/{len(all_pdfs)}: {pdf_name} from folder {folder_num}")
        
        conversion = convert_single_pdf_to_markdown(
            pdf_file_path=pdf_path,
            folder_name=folder_num,
            num_devices=num_devices,
            num_workers=num_workers,
            disable_image_extraction=not enable_images
        )
        
        results.append(conversion)
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    if not successful:
        details = "Error: All conversions failed.\n\n"
        for r in failed:
            details += f"- File: {Path(r.pdf_file).name} (folder {r.folder_name})\n"
            if r.error:
                details += f"  Error: {r.error}\n"
            if r.log_path:
                details += f"  Log: {r.log_path}\n"
        return details
    
    # Format response
    response = f"Successfully converted {len(successful)} file(s) to markdown"
    if failed:
        response += f" ({len(failed)} failed)"
    response += f"\n\nImages: {'Enabled' if enable_images else 'Disabled'}\n"
    response += f"Output directory: {OUTPUT_BASE_DIR}\n\n"
    
    # Group by folder for cleaner output
    folders_processed = {}
    for r in successful:
        if r.folder_name not in folders_processed:
            folders_processed[r.folder_name] = []
        folders_processed[r.folder_name].append(Path(r.pdf_file).name)
    
    response += "Processed files by folder:\n"
    for folder_num in sorted(folders_processed.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        response += f"\nFolder {folder_num}:\n"
        for pdf_name in folders_processed[folder_num]:
            response += f"  - {pdf_name}\n"

    if failed:
        response += "\n\nFailed conversions:\n"
        for r in failed:
            response += f"- File: {Path(r.pdf_file).name} (folder {r.folder_name})\n"
            if r.error:
                response += f"  Error: {r.error}\n"
            if r.log_path:
                response += f"  Log: {r.log_path}\n"
    
    return response


@mcp.tool()
async def convert_all_pdfs_to_markdown(
    num_devices: int = Field(
        default=3,
        ge=1,
        description="Number of devices for marker conversion (default: 3)"
    ),
    num_workers: int = Field(
        default=7,
        ge=1,
        description="Number of workers for marker conversion (default: 7)"
    ),
    enable_images: bool = Field(
        default=True,
        description="Whether to enable image extraction (default: True)"
    )
) -> str:
    """
    Convert ALL PDFs from all folders in PDF_BASE_DIR to markdown.
    
    This tool automatically discovers all numbered folders and processes every PDF file
    one at a time with image extraction enabled.
    
    Returns a summary of processed files.
    """
    # Discover all folders
    if not PDF_BASE_DIR.exists():
        return f"Error: PDF base directory does not exist: {PDF_BASE_DIR}"
    
    all_folders = [d.name for d in PDF_BASE_DIR.iterdir() if d.is_dir()]
    
    if not all_folders:
        return f"Error: No folders found in {PDF_BASE_DIR}"
    
    logger.info(f"Found {len(all_folders)} folder(s): {sorted(all_folders, key=lambda x: int(x) if x.isdigit() else 0)}")
    
    # Call the main conversion function
    return await convert_pdfs_to_markdown(
        folder_numbers=all_folders,
        num_devices=num_devices,
        num_workers=num_workers,
        enable_images=enable_images
    )


if __name__ == "__main__":
    try:
        print("Starting Marker PDFs MCP server...")
        logger.info("Starting Marker PDFs MCP server...")
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
