# LINAC Failure Report Analysis Pipeline

A two-step automated pipeline for extracting and classifying LINAC (Linear Accelerator) failure reports using PDF parsing and AI-powered classification.
Because the structure of LINAC service reports may vary across institutions, users should modify the corresponding script (report_type_processing.py) to match the specific formatting and field layout of their reports.

## Overview

This project consists of two scripts that work together:

1. **PDF Extraction (`report_type*_processing.py`)**: Extracts structured data from LINAC service report PDFs
2. **LLM Classification (`linac_failure_classifier.py`)**: Classifies extracted reports into standardized failure type categories using OpenAI's GPT models

## Pipeline Workflow

```
PDF Reports → [Step 1: Extract] → CSV Data → [Step 2: Classify] → Classified Results
```

## Failure Type Categories

The classifier assigns reports to one or more of these categories:

- Beam Generation
- Collimation System
- Gantry Motion/Structure
- Imaging System (KV/MV)
- Treatment Couch
- Control Hardware
- System Networks
- Cooling System
- Power System/Distribution
- Ancillary Room Systems
- Safety Systems
- Operator Console/UI

## Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

1. **Install required packages:**
```bash
pip install PyMuPDF pandas python-dotenv tqdm openai
```

2. **Create a `.env` file in the project root directory:**
```bash
# On macOS/Linux
touch .env

# On Windows
type nul > .env
```

3. **Add your OpenAI API key to the `.env` file:**

Open `.env` in a text editor and add:
```
OPENAI_API_KEY=sk-your-api-key-here
```

Replace `sk-your-api-key-here` with your actual OpenAI API key.

**Important:** Never commit your `.env` file to version control!

4. **Add `.env` to your `.gitignore` file:**
```bash
echo ".env" >> .gitignore
```

## Usage

### Step 1: Extract Data from PDFs

This step converts Varian service report PDFs into a structured CSV file.

1. **Place your PDF reports** in a folder (e.g., `raw_data/varian_reports/`)

2. **Update the folder paths** in `extract_varian_reports.py`:
```python
folder = "raw_data/varian_reports/"  # Input folder with PDFs
output_csv = "clean_data/df_full_desc.csv"  # Output CSV file
```

3. **Run the extraction script:**
```bash
python extract_varian_reports.py
```

4. **Verify the output:** Check that `clean_data/df_full_desc.csv` was created with extracted data

**Extracted Fields:**
- Work order ID and machine ID
- Subject and description
- Malfunction start and machine release times
- Time in/out and duration hours
- Travel, site, and total work hours

### Step 2: Classify Failures with AI

This step uses AI to classify the extracted reports into failure type categories.

1. **Ensure the CSV from Step 1 exists** at `clean_data/df_full_desc.csv`

2. **Run the classification script:**
```bash
python linac_failure_classifier.py
```

3. **Results will be saved** to `output/classified_reports.csv`

The script will:
- Load the extracted data
- Send each report to OpenAI's API for classification
- Add classification results to the DataFrame
- Save the enriched data with failure types

### Complete Pipeline Example

```bash
# Step 1: Extract from PDFs
python extract_varian_reports.py

# Step 2: Classify failures
python linac_failure_classifier.py

# Results are now in output/classified_reports.csv
```

## Output Format

### After Step 1 (Extraction)
CSV with columns:
- `work_order_id`, `machine_id`
- `subject`, `description`
- `malfunction_start`, `machine_release`
- `time_in`, `time_out`, `down_time_hours`
- `site_hours`, `travel_hours`, `total_work_hours`
- `report_source`, `file_name`

### After Step 2 (Classification)
All Step 1 columns plus:
- `llm_classification`: Full JSON response from the API
- `failure_type`: Extracted failure type(s), e.g., `"Collimation System, Control Hardware"`

## Programmatic Usage

### Extract Single PDF

```python
from extract_varian_reports import extract_report_data

report = extract_report_data("path/to/report.pdf")
print(report['subject'])
print(report['description'])
```

### Classify Reports

```python
from linac_failure_classifier import LINACFailureClassifier
import pandas as pd

# Load extracted data
df = pd.read_csv('clean_data/df_full_desc.csv')

# Initialize classifier
classifier = LINACFailureClassifier(model="gpt-4o")

# Classify all reports
df_classified = classifier.classify_dataframe(df)

# Save results
df_classified.to_csv('output/results.csv', index=False)

# Analyze results
print(df_classified['failure_type'].value_counts())
```

## Configuration Options

### Extraction Script

Edit paths in `extract_varian_reports.py`:
```python
folder = "your_pdf_folder/"
output_csv = "your_output_file.csv"
```

### Classification Script

**Change the AI Model:**
```python
classifier = LINACFailureClassifier(model="gpt-4o-mini")  # Faster, cheaper
# or
classifier = LINACFailureClassifier(model="gpt-4o")      # More accurate
```

**Adjust Input/Output Paths:**
Edit in the `main()` function:
```python
INPUT_FILE = Path('clean_data/df_full_desc.csv')
OUTPUT_FILE = Path('output/classified_reports.csv')
```

## Troubleshooting

### Step 1: PDF Extraction Issues

**"No such file or directory" Error:**
- Verify the PDF folder path exists
- Check that PDFs are in the correct format (Varian service reports)
- Ensure file permissions allow reading

**Empty or Missing Fields:**
- Some PDFs may have different formats
- Check the regex patterns in `extract_report_data()` function
- Review the PDF structure and update patterns if needed

**ImportError: No module named 'fitz':**
```bash
pip install PyMuPDF
```

### Step 2: Classification Issues

**"OpenAI API key not found" Error:**
- Make sure your `.env` file is in the same directory as the script
- Check that the API key is correctly formatted: `OPENAI_API_KEY=sk-...`
- Verify there are no extra spaces or quotes around the key

**"Input file not found" Error:**
- Run Step 1 (extraction) first
- Check that `clean_data/df_full_desc.csv` exists
- Verify the path in the classification script matches your output from Step 1

## Project Structure

```
project/
├── extract_varian_reports.py     # Step 1: PDF extraction
├── linac_failure_classifier.py   # Step 2: AI classification
├── .env                           # API key (DO NOT COMMIT)
├── .gitignore                     # Git ignore file
├── README.md                      # This file
├── raw_data/
│   └── varian_reports/           # Input: PDF reports
├── clean_data/
│   └── df_full_desc.csv          # Step 1 output / Step 2 input
└── output/
    └── classified_reports.csv    # Final results
```

## Example Workflow

```bash
# 1. Set up environment
pip install PyMuPDF pandas python-dotenv tqdm openai
echo "OPENAI_API_KEY=sk-your-key" > .env

# 2. Add your PDF reports
mkdir -p raw_data/varian_reports
# Copy your PDF files here

# 3. Extract data from PDFs
python extract_varian_reports.py
# ✓ Created: clean_data/df_full_desc.csv

# 4. Classify failures
python linac_failure_classifier.py
# ✓ Created: output/classified_reports.csv

# 5. Analyze results
python -c "import pandas as pd; df = pd.read_csv('output/classified_reports.csv'); print(df['failure_type'].value_counts())"
```
