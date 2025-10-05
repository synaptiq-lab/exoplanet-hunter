#!/usr/bin/env python3
"""
Fast script to merge all batch CSV files from temp_batches directory into a single CSV file.
Uses pure file operations for maximum efficiency with large files.
"""

import os
import glob
from pathlib import Path

def merge_batch_files_fast(input_dir, output_file, buffer_size=1024*1024):
    """
    Merge all batch CSV files in the input directory into a single CSV file.
    Uses pure file operations for maximum speed and minimal memory usage.
    
    Parameters:
    -----------
    input_dir : str or Path
        Directory containing the batch CSV files
    output_file : str or Path
        Path to the output merged CSV file
    buffer_size : int
        Buffer size for reading/writing (default: 1MB)
    """
    input_path = Path(input_dir)
    output_path = Path(output_file)
    
    # Get all batch files sorted by name
    batch_files = sorted(glob.glob(str(input_path / "batch_*.csv")))
    
    if not batch_files:
        print(f"No batch files found in {input_dir}")
        return
    
    print(f"Found {len(batch_files)} batch files to merge")
    print(f"Output file: {output_path}")
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    total_bytes = 0
    
    # Open output file for writing
    with open(output_path, 'wb') as outfile:
        for i, batch_file in enumerate(batch_files, 1):
            print(f"\nProcessing {i}/{len(batch_files)}: {Path(batch_file).name}")
            
            with open(batch_file, 'rb') as infile:
                # For the first file, copy everything including header
                if i == 1:
                    while True:
                        chunk = infile.read(buffer_size)
                        if not chunk:
                            break
                        outfile.write(chunk)
                        total_bytes += len(chunk)
                else:
                    # For subsequent files, skip the header line
                    # Read first line (header) and discard it
                    infile.readline()
                    
                    # Copy the rest of the file
                    while True:
                        chunk = infile.read(buffer_size)
                        if not chunk:
                            break
                        outfile.write(chunk)
                        total_bytes += len(chunk)
            
            file_size_mb = Path(batch_file).stat().st_size / (1024 * 1024)
            print(f"  ✓ Copied {file_size_mb:.2f} MB from {Path(batch_file).name}")
    
    print(f"\n{'='*60}")
    print(f"Merge completed successfully!")
    print(f"Total bytes written: {total_bytes:,}")
    
    # Get output file size
    if output_path.exists():
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        file_size_gb = file_size_mb / 1024
        print(f"Output file size: {file_size_mb:.2f} MB ({file_size_gb:.2f} GB)")
    print(f"Output file: {output_path}")
    print(f"{'='*60}")


def main():
    """Main function to run the merge process."""
    
    # Configuration
    input_directory = "/home/artorius/Projects/Perso/Hackhathon/NASA/data/final/temp_batches"
    output_file = "/home/artorius/Projects/Perso/Hackhathon/NASA/data/final/merged_all_batches.csv"
    
    print("="*60)
    print("Batch CSV Files Merger (Fast Version)")
    print("="*60)
    
    merge_batch_files_fast(
        input_dir=input_directory,
        output_file=output_file,
        buffer_size=10*1024*1024  # 10MB buffer for large files
    )


if __name__ == "__main__":
    main()
