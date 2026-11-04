"""Submission Packaging Script for Parlor (Batch 14).

Creates a clean, portable distribution ZIP archive (`dist/parlor_submission_batch14.zip`)
suitable for university submission and external committee evaluation.

Excludes:
  - Bulky model weights (GGUF, ONNX, BIN, safetensors)
  - Virtual environments (.venv)
  - Pytest & coverage cache (.pytest_cache, .coverage, htmlcov)
  - Python bytecode (__pycache__, *.pyc)
  - Secrets and local environment files (.env)
  - Git internal database (.git)

Preserves:
  - All source code (src/) including vendored on-device VAD assets
  - Automated test suite (tests/)
  - Complete academic documentation & slide decks (docs/)
  - Demonstration, evaluation, and reproduction scripts (scripts/)
  - Historical SQLite database & EMA trial records (shared_state/)
  - Configuration files (pyproject.toml, uv.lock, .env.example, start.ps1)
  - Empirical verification reports (VERIFICATION_REPORT.md, ACCURACY_VALIDATION.md)
"""

import os
import sys
import zipfile
from typing import List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(os.path.join(BASE_DIR, "parlor-main-main")):
    SOURCE_DIR = os.path.join(BASE_DIR, "parlor-main-main")
else:
    SOURCE_DIR = BASE_DIR

OUTPUT_DIR = os.path.join(BASE_DIR, "dist")
OUTPUT_ZIP = os.path.join(OUTPUT_DIR, "parlor_submission_batch14.zip")

EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "env",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "htmlcov",
    "models",
    "dist",
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".gguf",
    ".onnx",
    ".bin",
    ".safetensors",
    ".pt",
    ".coverage",
}

EXCLUDED_FILES = {
    ".env",
    ".coverage",
    ".DS_Store",
    "Thumbs.db",
    "ema_validation_trials.json",  # Exclude unverified synthetic participant trials
}


def should_exclude(rel_path: str, filename: str) -> bool:
    """Evaluates whether a file should be excluded from the release archive."""
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in EXCLUDED_DIRS:
            return True

    if filename in EXCLUDED_FILES:
        return True

    ext = os.path.splitext(filename)[1].lower()
    if ext in EXCLUDED_EXTENSIONS:
        if "web" in parts and "static" in parts and ("vendor" in parts or "vad" in filename):
            return False  # Keep vendored offline VAD and ONNX assets
        return True

    return False


def create_archive() -> Tuple[int, int, int]:
    """Generates the clean submission zip archive."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files_added = 0
    total_uncompressed = 0

    print("=" * 75)
    print("      PARLOR SUBMISSION PACKAGING (BATCH 14 - CSE)")
    print("=" * 75)
    print(f" Source Root : {SOURCE_DIR}")
    print(f" Output Zip  : {OUTPUT_ZIP}")
    print("-" * 75)

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(SOURCE_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, SOURCE_DIR)

                if should_exclude(rel_path, file):
                    continue

                zipf.write(abs_path, os.path.join("parlor", rel_path))
                size = os.path.getsize(abs_path)
                total_uncompressed += size
                files_added += 1

    total_compressed = os.path.getsize(OUTPUT_ZIP)

    print(f" Files Packaged     : {files_added:,}")
    print(f" Uncompressed Size  : {total_uncompressed / (1024 * 1024):.2f} MB")
    print(f" Compressed Zip Size: {total_compressed / (1024 * 1024):.2f} MB")
    print("=" * 75)

    # Integrity verification
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as check_zip:
        names = check_zip.namelist()
        leaked_secrets = [n for n in names if n.endswith("/.env") or n == "parlor/.env"]
        leaked_models = [n for n in names if n.endswith(".gguf") or "models/" in n]

        if leaked_secrets:
            print(f"[FATAL SECURITY ERROR] Secret .env detected in ZIP: {leaked_secrets}", file=sys.stderr)
            sys.exit(1)
        if leaked_models:
            print(f"[FATAL ERROR] Large model weights detected in ZIP: {leaked_models}", file=sys.stderr)
            sys.exit(1)

        print("[AUDIT PASSED] No secret .env and no large model weights in archive.")
        print(f"[SUCCESS] Submission archive ready at: {OUTPUT_ZIP}")

    return files_added, total_uncompressed, total_compressed


if __name__ == "__main__":
    create_archive()

