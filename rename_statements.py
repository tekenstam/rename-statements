import os
import re
import shutil
import pdfplumber
from dateutil import parser
from datetime import datetime

# ================= CONFIGURATION =================
# Set to False to actually rename/move files
DRY_RUN = True 

INPUT_FOLDER = "./inbox"
OUTPUT_FOLDER = "./processed"

# Define rules for each bank. 
# 'signature': A unique phrase found in the PDF text (e.g., "Chase Freedom", "Wells Fargo").
# 'date_regex': A regex pattern to find the date. The date part must be in a capture group ().
BANK_RULES = [
    {
        "name": "Chase_Credit_Card",
        "signature": "Chase Card Services",
        # Example pattern: "Opening/Closing Date 12/02/23 - 01/01/24"
        # We capture the second date (Closing Date)
        "date_regex": r"Opening/Closing Date\s+\d{2}/\d{2}/\d{2}\s+-\s+(\d{2}/\d{2}/\d{2})"
    },
    {
        "name": "Amex",
        "signature": "American Express",
        # Example pattern: "Closing Date Jan 04, 2024"
        "date_regex": r"Closing Date\s+([A-Za-z]+\s\d{1,2},\s\d{4})"
    },
    {
        "name": "Schwab_Brokerage",
        "signature": "Charles Schwab & Co",
        # Example pattern: "Statement Period: January 1, 2024 through January 31, 2024"
        "date_regex": r"Statement Period:.*through\s+([A-Za-z]+\s\d{1,2},\s\d{4})"
    },
    {
        "name": "Nordstrom",
        "signature": "NORDSTROM CARD SERVICES", 
        # Matches "to January 19, 2026" and captures the date part
        "date_regex": r"to\s+([A-Za-z]+\s\d{1,2},\s\d{4})"
    }
]
# =================================================

def extract_text_from_pdf(filepath):
    """Extracts text from the first page of the PDF."""
    try:
        with pdfplumber.open(filepath) as pdf:
            # Usually the date is on the first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def normalize_date(date_string):
    """Parses a raw date string into YYYY-MM-DD format."""
    try:
        dt = parser.parse(date_string)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None

def process_files():
    if not os.path.exists(OUTPUT_FOLDER) and not DRY_RUN:
        os.makedirs(OUTPUT_FOLDER)

    for filename in os.listdir(INPUT_FOLDER):
        if not filename.lower().endswith(".pdf"):
            continue

        filepath = os.path.join(INPUT_FOLDER, filename)
        print(f"Processing: {filename}...")

        text = extract_text_from_pdf(filepath)
        if not text:
            continue

        matched_rule = None
        
        # 1. Identify the Bank
        for rule in BANK_RULES:
            if rule["signature"] in text:
                matched_rule = rule
                break
        
        if not matched_rule:
            print(f"  [!] No bank signature matched for {filename}")
            continue

        # 2. Extract the Date
        # re.IGNORECASE makes it less brittle regarding capitalization
        match = re.search(matched_rule["date_regex"], text, re.IGNORECASE)
        
        if match:
            raw_date = match.group(1) # Get the captured group from regex
            formatted_date = normalize_date(raw_date)
            
            if formatted_date:
                new_filename = f"{matched_rule['name']} - {formatted_date} Statement.pdf"

                new_path = os.path.join(OUTPUT_FOLDER, new_filename)
                
                if DRY_RUN:
                    print(f"  [DRY RUN] Would rename to: {new_filename}")
                else:
                    # Handle duplicates if file already exists
                    if os.path.exists(new_path):
                        print(f"  [!] File {new_filename} already exists. Skipping.")
                    else:
                        shutil.move(filepath, new_path)
                        print(f"  [SUCCESS] Renamed to: {new_filename}")
            else:
                print(f"  [!] Date found '{raw_date}' but could not parse.")
        else:
            print(f"  [!] Bank identified as {matched_rule['name']}, but regex failed to find date.")

if __name__ == "__main__":
    process_files()