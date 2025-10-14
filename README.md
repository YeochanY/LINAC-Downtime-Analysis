# LINAC Failure Classifier

Automated classification of LINAC (Linear Accelerator) failure reports using OpenAI's GPT models.

## Overview

This script uses AI to classify medical LINAC downtime reports into standardized failure type categories, helping maintenance teams analyze patterns and improve system reliability.

## Features

- Classifies failure reports into 12 predefined categories
- Supports multi-label classification
- Automatic retry logic for API failures
- Progress tracking and detailed logging
- Batch processing of CSV files

## Failure Type Categories

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

1. **Clone or download this repository**

2. **Install required packages:**
```bash
pip install openai pandas python-dotenv tqdm
```

3. **Create a `.env` file in the project root directory:**
```bash
# On macOS/Linux
touch .env

# On Windows
type nul > .env
```

4. **Add your OpenAI API key to the `.env` file:**

Open `.env` in a text editor and add:
```
OPENAI_API_KEY=sk-your-api-key-here
```

Replace `sk-your-api-key-here` with your actual OpenAI API key.

**Important:** Never commit your `.env` file to version control!

5. **Add `.env` to your `.gitignore` file:**
```bash
echo ".env" >> .gitignore
```

## Usage

### Basic Usage

1. Place your input CSV file in the `clean_data/` directory with the name `df_full_desc.csv`

2. Ensure your CSV has these columns:
   - `subject`: Brief description of the issue
   - `description`: Detailed failure report

3. Run the script:
```bash
python linac_failure_classifier.py
```

4. Results will be saved to `output/classified_reports.csv`

### Custom File Paths

Edit the `main()` function to change input/output paths:

```python
INPUT_FILE = Path('your_input_folder/your_file.csv')
OUTPUT_FILE = Path('your_output_folder/results.csv')
```

### Programmatic Usage

```python
from linac_failure_classifier import LINACFailureClassifier
import pandas as pd

# Initialize classifier
classifier = LINACFailureClassifier(model="gpt-4o")

# Classify a single report
result = classifier.classify_report(
    subject="MLC failure",
    description="Multi-leaf collimator not responding..."
)
print(result['failure_type'])

# Classify a DataFrame
df = pd.read_csv('your_data.csv')
df_classified = classifier.classify_dataframe(df)
df_classified.to_csv('results.csv', index=False)
```

## Output Format

The script adds two new columns to your DataFrame:

- `llm_classification`: Full JSON response from the API
- `failure_type`: Extracted failure type(s) for easy filtering

Example output:
```
failure_type: "Collimation System, Control Hardware"
```

## Configuration Options

### Change the AI Model

```python
classifier = LINACFailureClassifier(model="gpt-4o-mini")  # Faster, cheaper
# or
classifier = LINACFailureClassifier(model="gpt-4o")      # More accurate
```

### Adjust Retry Attempts

```python
result = classifier.classify_report(
    subject="...",
    description="...",
    max_retries=5  # Default is 3
)
```

## Troubleshooting

### "OpenAI API key not found" Error

- Make sure your `.env` file is in the same directory as the script
- Check that the API key is correctly formatted: `OPENAI_API_KEY=sk-...`
- Verify there are no extra spaces or quotes around the key

### "Input file not found" Error

- Check that your CSV file exists in the `clean_data/` folder
- Verify the filename matches exactly (case-sensitive)
- Update the `INPUT_FILE` path in the script if needed

### JSON Parse Errors

The script automatically retries on parse errors. If you see many ParseError classifications:
- Check your API key is valid and has credits
- Try using a different model (gpt-4o is more reliable than gpt-4o-mini)

### Rate Limiting

If you're processing many reports, you may hit API rate limits. The script will show errors in the logs. Solutions:
- Add a delay between requests (modify the code to add `time.sleep()`)
- Upgrade your OpenAI account tier
- Process in smaller batches

## Cost Estimation

Approximate costs per 1,000 reports (using GPT-4o):
- Input tokens: ~1,500 tokens/report × $2.50/1M tokens = $3.75
- Output tokens: ~50 tokens/report × $10/1M tokens = $0.50
- **Total: ~$4.25 per 1,000 reports**

## Project Structure

```
project/
├── linac_failure_classifier.py  # Main script
├── .env                          # API key (DO NOT COMMIT)
├── .gitignore                    # Git ignore file
├── README.md                     # This file
├── clean_data/
│   └── df_full_desc.csv         # Input data
└── output/
    └── classified_reports.csv   # Results
```

## Security Notes

- ⚠️ **Never share your `.env` file or commit it to GitHub**
- ⚠️ Keep your OpenAI API key confidential
- Add `.env` to `.gitignore` immediately
- Rotate your API key if accidentally exposed

## Support

For issues with:
- **OpenAI API**: Check [OpenAI Documentation](https://platform.openai.com/docs)
- **This script**: Review the error logs in the console output
- **LINAC-specific questions**: Consult your medical physics team

## License

[Add your license here]

## Version History

- **v1.0.0** - Initial release with GPT-4o classification