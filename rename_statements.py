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
# You can keep these here or move them to a separate JSON/YAML file in the future.
BANK_RULES = [
    {
        "name": "Nordstrom",
        "signature": "NORDSTROM CARD SERVICES",
        "date_regex": r"to\s+([A-Za-z]+\s\d{1,2},\s\d{4})"
    },
    {
        "name": "Chase_Credit_Card",
        "signature": "Chase Card Services",
        "date_regex": r"Opening/Closing Date\s+\d{2}/\d{2}/\d{2}\s+-\s+(\d{2}/\d{2}/\d{2})"
    },
    {
        "name": "Amex",
        "signature": "American Express",
        "date_regex": r"Closing Date\s+([A-Za-z]+\s\d{1,2},\s\d{4})"
    },
    {
        "name": "Schwab_Brokerage",
        "signature": "Charles Schwab & Co",
        "date_regex": r"Statement Period:.*through\s+([A-Za-z]+\s\d{1,2},\s\d{4})"
    }
]
# =======================================================

def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

def extract_text_from_pdf(filepath):
    """Safely extracts text from the first page of the PDF."""
    try:
        with pdfplumber.open(filepath) as pdf:
            if not pdf.pages:
                logging.warning(f"File is empty or has no pages: {filepath}")
                return None
            return pdf.pages[0].extract_text()
    except Exception as e:
        logging.error(f"Failed to read PDF {filepath}: {e}")
        return None

def normalize_date(date_string):
    """Parses a raw date string into YYYY-MM-DD format."""
    try:
        dt = parser.parse(date_string)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError) as e:
        logging.warning(f"Could not parse date string '{date_string}': {e}")
        return None

def process_files(input_dir, output_dir, dry_run, organize_by_folder):
    # validate input directory
    if not os.path.exists(input_dir):
        logging.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)

    # If not a dry run, ensure output directory exists (base level)
    if not dry_run and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            logging.error(f"Could not create output directory {output_dir}: {e}")
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
            logging.warning(f"  [Skipping] No text found in {filename}")
            continue

        matched_rule = None
        for rule in BANK_RULES:
            if rule["signature"] in text:
                matched_rule = rule
                break
        
        if not matched_rule:
            logging.warning(f"  [Skipping] No bank signature matched for {filename}")
            continue

        # Search for date using regex
        match = re.search(matched_rule["date_regex"], text, re.IGNORECASE)
        
        if match:
            raw_date = match.group(1)
            formatted_date = normalize_date(raw_date)
            
            if formatted_date:
                # Construct new filename
                new_filename = f"{matched_rule['name']} - {formatted_date} Statement.pdf"
                
                # Determine final destination folder
                final_output_dir = output_dir
                if organize_by_folder:
                    final_output_dir = os.path.join(output_dir, matched_rule['name'])

                destination_path = os.path.join(final_output_dir, new_filename)
                
                if dry_run:
                    logging.info(f"  [DRY RUN] Match: {matched_rule['name']}")
                    logging.info(f"  [DRY RUN] Move to: {destination_path}")
                else:
                    # Create subfolder if needed
                    if organize_by_folder and not os.path.exists(final_output_dir):
                        try:
                            os.makedirs(final_output_dir)
                        except OSError as e:
                            logging.error(f"  Could not create subfolder {final_output_dir}: {e}")
                            continue

                    # Handle file collision
                    if os.path.exists(destination_path):
                        logging.warning(f"  [Skipping] File already exists: {destination_path}")
                    else:
                        try:
                            shutil.move(filepath, destination_path)
                            logging.info(f"  [SUCCESS] Renamed to: {destination_path}")
                            files_renamed += 1
                        except OSError as e:
                            logging.error(f"  Failed to move file: {e}")
            else:
                logging.warning(f"  [Skipping] Date matched '{raw_date}' but parsing failed.")
        else:
            logging.warning(f"  [Skipping] Identified as {matched_rule['name']} but regex failed to find date.")

    logging.info("------------------------------------------------")
    logging.info(f"Summary: Processed {files_processed} files. Renamed {files_renamed} files.")

if __name__ == "__main__":
    parser_args = argparse.ArgumentParser(description="Rename PDF bank statements based on content.")
    
    # Arguments
    parser_args.add_argument("--input", "-i", default="./inbox", help="Input directory containing PDFs (default: ./inbox)")
    parser_args.add_argument("--output", "-o", default="./processed", help="Output directory for renamed files (default: ./processed)")
    parser_args.add_argument("--dry-run", action="store_true", help="Run without moving files to see what would happen")
    parser_args.add_argument("--organize", action="store_true", help="Create subfolders for each bank in the output directory")
    parser_args.add_argument("--verbose", "-v", action="store_true", help="Increase output verbosity")

    args = parser_args.parse_args()

    process_files(args.input, args.output, args.dry_run, args.organize)