import os
import re
import shutil
import argparse
import sys
import logging
from datetime import datetime

# Third-party libraries
try:
    import pdfplumber
    from dateutil import parser
except ImportError:
    print("Error: Missing required libraries. Please run: pip install pdfplumber python-dateutil")
    sys.exit(1)

# ================= CONFIGURATION RULES =================
BANK_RULES = [
    {
        "name": "Nordstrom",
        "signature": "NORDSTROM CARD SERVICES",
        "date_regex": r"to\s+([A-Za-z]+\s\d{1,2},\s\d{4})"
    },
    {
        "name": "Nordstrom",
        "signature": "www.nordstromcard.com",
        "date_regex": r"to\s+([A-Za-z]+\s\d{1,2},\s\d{4})"
    },
    {
        "name": "Chase_Credit_Card",
        "signature": "Chase Card Services",
        "date_regex": r"Opening/Closing Date\s+\d{2}/\d{2}/\d{2}\s+-\s+(\d{2}/\d{2}/\d{2})"
    },
        {
        "name": "HealthEquity",
        "signature": "HealthEquity",
        "date_regex": r"through(\d{2}/\d{2}/\d{2})"
    }
]
# =======================================================

def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

def extract_text_from_pdf(filepath):
    try:
        with pdfplumber.open(filepath) as pdf:
            if not pdf.pages:
                return None
            return pdf.pages[0].extract_text()
    except Exception as e:
        logging.error(f"Failed to read PDF {filepath}: {e}")
        return None

def normalize_date(date_string):
    try:
        dt = parser.parse(date_string)
        return dt.strftime("%Y-%m-%d"), dt.year
    except (ValueError, TypeError):
        return None, None

def process_files(input_dir, output_dir, dry_run, organize_by_folder, force):
    if not os.path.exists(input_dir):
        logging.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)

    files_processed = 0
    files_renamed = 0

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".pdf"):
            continue

        filepath = os.path.join(input_dir, filename)
        logging.info(f"Processing: {filename}")
        files_processed += 1

        text = extract_text_from_pdf(filepath)
        if not text:
            continue

        matched_rule = next((r for r in BANK_RULES if r["signature"] in text), None)
        
        if not matched_rule:
            logging.warning(f"  [Skipping] No bank signature matched.")
            continue

        match = re.search(matched_rule["date_regex"], text, re.IGNORECASE)
        if match:
            formatted_date, year = normalize_date(match.group(1))
            
            if formatted_date:
                new_filename = f"{matched_rule['name']} - {formatted_date} Statement.pdf"
                
                # Determine hierarchy: Output/BankName/Year/File
                final_output_dir = output_dir
                if organize_by_folder:
                    final_output_dir = os.path.join(output_dir, matched_rule['name'], str(year))

                destination_path = os.path.join(final_output_dir, new_filename)
                
                if dry_run:
                    logging.info(f"  [DRY RUN] Would move to: {destination_path}")
                    continue

                # 1. Create directory structure
                if not os.path.exists(final_output_dir):
                    os.makedirs(final_output_dir)

                # 2. Collision Handling
                if os.path.exists(destination_path):
                    if force:
                        logging.info(f"  [Force] Overwriting existing file: {new_filename}")
                        os.remove(destination_path) # Explicitly remove for cross-platform reliability
                    else:
                        logging.warning(f"  [Collision] File '{new_filename}' already exists. Skipping. Use --force to overwrite.")
                        continue

                # 3. Move File
                try:
                    shutil.move(filepath, destination_path)
                    logging.info(f"  [SUCCESS] Moved to: {destination_path}")
                    files_renamed += 1
                except OSError as e:
                    logging.error(f"  Failed to move file: {e}")
            else:
                logging.warning(f"  [Skipping] Date parsing failed.")
        else:
            logging.warning(f"  [Skipping] Regex failed to find date.")

    logging.info(f"Finished. Renamed {files_renamed}/{files_processed} files.")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Rename PDF bank statements.")
    
    arg_parser.add_argument("--input", "-i", default="./inbox")
    arg_parser.add_argument("--output", "-o", default="./processed")
    arg_parser.add_argument("--dry-run", action="store_true")
    arg_parser.add_argument("--organize", action="store_true")
    arg_parser.add_argument("--force", action="store_true")
    arg_parser.add_argument("--verbose", "-v", action="store_true")

    args = arg_parser.parse_args() # This now calls the correct object
    setup_logging(args.verbose)
    process_files(args.input, args.output, args.dry_run, args.organize, args.force)