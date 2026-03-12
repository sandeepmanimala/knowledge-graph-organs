"""
Script to download the full Human Metabolome Database (HMDB) XML.
Since the XML is ~5GB, this script streams the zip file and extracts it.

Execution: python3 scripts/1_acquire/hmdb/download_hmdb.py
"""
import os
import requests
import zipfile
from pathlib import Path

# HMDB All Metabolites URL (latest version)
HMDB_URL = "https://hmdb.ca/system/downloads/current/hmdb_metabolites.zip"
DOWNLOAD_DIR = Path("data/raw/hmdb")
ZIP_PATH = DOWNLOAD_DIR / "hmdb_metabolites.zip"
XML_PATH = DOWNLOAD_DIR / "hmdb_metabolites.xml"

def download_and_extract_hmdb():
    print("🚀 Starting HMDB Data Acquisition...")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download
    if not ZIP_PATH.exists() and not XML_PATH.exists():
        print(f"📥 Downloading HMDB zip file from {HMDB_URL} (this may take a while)...")
        # Stream the massive download
        with requests.get(HMDB_URL, stream=True) as r:
            r.raise_for_status()
            with open(ZIP_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("✅ Download complete.")
    else:
        print("✅ Zip file or XML already exists. Skipping download.")

    # 2. Extract
    if not XML_PATH.exists():
        print(f"📦 Extracting {ZIP_PATH}...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(DOWNLOAD_DIR)
        print("✅ Extraction complete.")
    else:
        print("✅ XML already extracted.")

if __name__ == "__main__":
    download_and_extract_hmdb()
