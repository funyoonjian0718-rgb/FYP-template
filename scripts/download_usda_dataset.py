#!/usr/bin/env python3
"""
Download USDA FoodData Central and process it for RAG ingestion.

This script fetches the USDA branded food products dataset (CSV format)
and prepares it for ingestion into ChromaDB for RAG.

Download link: https://fdc.nal.usda.gov/download-datasets.html

The file should be named something like:
  - FoodData_Central_branded_food_csv_2024-10-24.csv
  - or FoodData_Central_survey_food_csv_2024-10-24.csv

Place the downloaded CSV in the `data/` folder, and this script will
automatically pick it up when running `python -m app.rag.ingest`.

Manual download:
1. Go to: https://fdc.nal.usda.gov/download-datasets.html
2. Download the "Branded Foods" CSV file (~300MB)
3. Move to: backend/data/
4. Run: python -m app.rag.ingest
"""

import os
import sys
import requests
from pathlib import Path


def download_usda_dataset():
    """
    Note: USDA does NOT provide direct download links via API for the full dataset.
    You must manually download from: https://fdc.nal.usda.gov/download-datasets.html
    
    This function provides instructions and a helper to verify the file.
    """
    print("=" * 70)
    print("USDA FoodData Central Dataset Download")
    print("=" * 70)
    print()
    print("USDA datasets are NOT directly downloadable via API.")
    print("You must manually download from their website.")
    print()
    print("📥 STEPS TO DOWNLOAD:")
    print()
    print("1. Go to: https://fdc.nal.usda.gov/download-datasets.html")
    print("   (Click 'Download Full Dataset')")
    print()
    print("2. Choose the file type (Recommended: Branded Foods CSV):")
    print("   - Branded Foods: ~300MB, includes packaged products")
    print("   - Survey Foods: Smaller, includes home-cooked foods")
    print()
    print("3. Download the CSV file (it's a .zip, extract it)")
    print()
    print("4. Move the extracted CSV to this folder:")
    data_dir = Path(__file__).parent.parent / "data"
    print(f"   → {data_dir}/")
    print()
    print("5. Run ingestion:")
    print("   python -m app.rag.ingest")
    print()
    print("=" * 70)
    print()
    
    # Check if any CSV exists in data folder
    data_dir = Path(__file__).parent.parent / "data"
    csv_files = list(data_dir.glob("*.csv"))
    
    if csv_files:
        print(f"✅ Found {len(csv_files)} CSV file(s) in {data_dir}:")
        for csv_file in csv_files:
            size_mb = csv_file.stat().st_size / (1024 * 1024)
            print(f"   • {csv_file.name} ({size_mb:.1f} MB)")
        print()
        print("The ingestion script will use these files automatically.")
    else:
        print(f"❌ No CSV files found in {data_dir}")
        print("   Please download and place a CSV file there first.")
    
    print()
    print("For more info: https://fdc.nal.usda.gov/")


if __name__ == "__main__":
    download_usda_dataset()
