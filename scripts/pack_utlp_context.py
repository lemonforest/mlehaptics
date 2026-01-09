#!/usr/bin/env python3
"""
Pack UTLP Context for AI Review

Aggregates all UTLP source files into a single text file for AI consumption.
Skips binary files and build directories.

Usage:
    python scripts/pack_utlp_context.py

Output:
    utlp_full_context.txt (in project root)
"""

import os
from pathlib import Path

# Configuration
UTLP_DIR = "examples/utlp"
OUTPUT_FILE = "utlp_full_context.txt"
INCLUDE_EXTENSIONS = {".c", ".h", ".md", ".txt", ".py"}
SKIP_EXTENSIONS = {".bin", ".elf", ".o", ".a", ".so", ".dll", ".exe", ".pyc"}
SKIP_DIRS = {".pio", "__pycache__", ".git", "build", ".vscode"}

def get_project_root():
    """Find project root (where this script's parent 'scripts' dir lives)."""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent

def should_include_file(filepath: Path) -> bool:
    """Check if file should be included based on extension."""
    return filepath.suffix.lower() in INCLUDE_EXTENSIONS

def should_skip_dir(dirname: str) -> bool:
    """Check if directory should be skipped."""
    return dirname in SKIP_DIRS or dirname.startswith(".")

def collect_files(utlp_path: Path) -> list:
    """Recursively collect all source files."""
    files = []

    for root, dirs, filenames in os.walk(utlp_path):
        # Filter out directories to skip (modifies dirs in-place)
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]

        for filename in sorted(filenames):
            filepath = Path(root) / filename
            if should_include_file(filepath):
                files.append(filepath)

    return sorted(files)

def pack_files(project_root: Path, files: list, output_path: Path):
    """Pack all files into single output file with headers."""
    total_lines = 0
    total_bytes = 0

    with open(output_path, "w", encoding="utf-8") as out:
        # Write header
        out.write("=" * 79 + "\n")
        out.write("UTLP FULL CONTEXT - Aggregated Source for AI Review\n")
        out.write("=" * 79 + "\n")
        out.write(f"Files included: {len(files)}\n")
        out.write("=" * 79 + "\n\n")

        for filepath in files:
            # Get relative path from project root
            rel_path = filepath.relative_to(project_root)

            # Write file header
            out.write("=" * 47 + "\n")
            out.write(f"FILE: {rel_path}\n")
            out.write("=" * 47 + "\n")

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    out.write(content)
                    total_lines += content.count("\n")
                    total_bytes += len(content.encode("utf-8"))
            except UnicodeDecodeError:
                out.write(f"[BINARY FILE - SKIPPED]\n")
            except Exception as e:
                out.write(f"[ERROR READING FILE: {e}]\n")

            out.write("\n\n")

        # Write footer with stats
        out.write("=" * 79 + "\n")
        out.write("END OF UTLP CONTEXT\n")
        out.write(f"Total files: {len(files)}\n")
        out.write(f"Total lines: {total_lines:,}\n")
        out.write(f"Total bytes: {total_bytes:,}\n")
        out.write("=" * 79 + "\n")

    return total_lines, total_bytes

def main():
    project_root = get_project_root()
    utlp_path = project_root / UTLP_DIR
    output_path = project_root / OUTPUT_FILE

    print(f"Project root: {project_root}")
    print(f"Scanning: {utlp_path}")

    if not utlp_path.exists():
        print(f"ERROR: UTLP directory not found: {utlp_path}")
        return 1

    # Collect files
    files = collect_files(utlp_path)
    print(f"Found {len(files)} source files")

    if not files:
        print("No files found to pack!")
        return 1

    # Pack files
    total_lines, total_bytes = pack_files(project_root, files, output_path)

    print(f"\nOutput written to: {output_path}")
    print(f"  Files: {len(files)}")
    print(f"  Lines: {total_lines:,}")
    print(f"  Size:  {total_bytes:,} bytes ({total_bytes/1024:.1f} KB)")

    # List included files
    print("\nIncluded files:")
    for f in files:
        rel = f.relative_to(project_root)
        print(f"  {rel}")

    return 0

if __name__ == "__main__":
    exit(main())
