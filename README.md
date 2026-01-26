## Prerequisite

You will need to install these packages:

```bash
pip install pdfplumber python-dateutil
```

Or:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```







# 📂 Statement Sorter

**Statement Sorter** is a Python-based utility that automates the tedious task of renaming downloaded bank statements. Instead of manually checking dates and account types, this script "reads" the first page of your PDFs, identifies the financial institution, extracts the closing date, and organizes the files into a clean, searchable directory structure.

Because let's face it: `Statement_20260119_12345.pdf` is a terrible filename.


## ✨ Features

* **Intelligent Extraction:** Uses `pdfplumber` to accurately read PDF text.
* **Flexible Date Parsing:** Handles various date formats (e.g., "Jan 19, 2026" or "01/19/26") using `python-dateutil`.
* **Dry Run Mode:** Test your regex rules without moving a single file.
* **Auto-Organization:** Optionally sorts statements into subfolders by bank name (e.g., `/Accounts/Nordstrom/`).
* **Robust Logging:** Verbose mode for debugging tricky PDF layouts.


## 🚀 Getting Started

### 1. Prerequisites

You’ll need Python 3.x installed. Install the required dependencies via pip:

```bash
pip install pdfplumber python-dateutil

```

Or you can use a virtual Python environment.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Installation

Clone your local repository or simply save `rename_statements.py` to your project folder.

### 3. Usage

Run the script from your terminal using command-line arguments.

| Flag | Long Flag    | Description                          | Default       |
| ---- | ------------ | ------------------------------------ | ------------- |
| `-i` | `--input`    | Folder containing messy PDFs         | `./inbox`     |
| `-o` | `--output`   | Destination for renamed files        | `./processed` |
|      | `--dry-run`  | Preview changes without moving files | `False`       |
|      | `--organize` | Create subfolders for each bank      | `False`       |
| `-v` | `--verbose`  | Show detailed processing logs        | `False`       |

#### Examples

**The "Safety First" Check:**

```bash
python rename_statements.py --input ~/Downloads --dry-run --verbose

```

**The "Big Clean Up" (with subfolders):**

```bash
python rename_statements.py --input ./inbox --output ./Financials --organize

```


## 🛠 Adding New Banks

To add a new financial institution, update the `BANK_RULES` list in `rename_statements.py`:

```python
BANK_RULES = [
    {
        "name": "YourBank",
        "signature": "Unique phrase found in PDF",
        "date_regex": r"Statement Date:\s+([A-Za-z]+\s\d{2},\s\d{4})"
    }
]
```

### How to customize this for your banks

The hardest part is finding the Regex pattern. Here is the workflow to get the correct patterns for your specific PDFs:

Extract the raw text first: Run a simple script on one of your PDFs to see exactly how Python "sees" the text (it often differs slightly from what you see visually).

```Python
import pdfplumber
with pdfplumber.open("my_statement.pdf") as pdf:
    print(pdf.pages[0].extract_text())
```

Find the Anchor: Look for the label next to the date. It might be "Statement Closing Date", "Period Ending", or "For the period of".

### Update BANK_RULES:

signature: Pick a string unique to that bank (e.g., "Wells Fargo Bank, N.A.").

date_regex: Write a regex that matches the label + the date, and put parenthesis () around the date part.

Common Regex Patterns Cheat Sheet

```text
Date Format in PDF	Regex Pattern to use
12/01/24	\d{2}/\d{2}/\d{2}
Dec 01, 2024	[A-Za-z]{3}\s\d{2},\s\d{4}
December 1, 2024	[A-Za-z]+\s\d{1,2},\s\d{4}
```


## 📝 Troubleshooting

* **No Match Found:** Run with `--verbose`. The script will tell you if it recognized the bank but failed the date regex, or if it didn't see the "signature" phrase at all.
* **Encrypted PDFs:** Some banks password-protect their PDFs. This script currently does not support encrypted files unless you decrypt them first.
