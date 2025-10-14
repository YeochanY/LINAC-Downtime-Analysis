import os
import pdfplumber
import re
import pandas as pd
from tqdm import tqdm

def extract_data_from_pdf(pdf_path):
    """Extracts key data from a given PDF file."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    extracted_data = {}

    # Optimized regex patterns for accurate extraction
    extracted_data['work_order_id'] = re.search(r"Work Order\s+WO-(\d+)", text)
    extracted_data['machine_id'] = re.search(r"Asset\s+(\S+)", text)
    extracted_data['subject'] = re.search(r"Subject\s+(.+)", text)
    extracted_data['description'] = re.search(r"Closure Summary\s+([\s\S]+?)\nWork Order Times", text)  
    extracted_data['malfunction_start'] = re.search(r"Malfunction Start\s*:\s*([\d/]+ [\d:]+ [APM]+)", text)
    extracted_data['machine_release'] = re.search(r"Machine Release\s*([\d/]+ [\d:]+ [APM]+)", text)
    extracted_data['time_in'] = re.search(r"Time In\s*([\d/]+ [\d:]+ [APM]+)", text)
    extracted_data['time_out'] = re.search(r"Time Out\s*([\d/]+ [\d:]+ [APM]+)", text)
    extracted_data['down_time_hours'] = re.search(r"Agreed Downtime\s*(\d+\.?\d*)", text)
    extracted_data['site_hours'] = re.search(r"Site Hours\s*(\d+\.?\d*)", text)
    extracted_data['travel_hours'] = re.search(r"Travel Hours\s*(\d+\.?\d*)", text)
    extracted_data['total_work_hours'] = re.search(r"Total Work Hours\s*(\d+\.?\d*)", text)
    
    # Extract matched values or set None if not found
    for key, match in extracted_data.items():
        if key == 'work_order_id' and match:
            extracted_data[key] = f"WO-{match.group(1).strip()}"
        elif match:
            extracted_data[key] = match.group(1).strip()
        else:
            extracted_data[key] = None
    
    # Static field
    extracted_data['report_source'] = "varian"

    return extracted_data

def process_multiple_pdfs(pdf_files):
    """Processes multiple PDF files and saves extracted data into a Pandas DataFrame."""
    results = []
    
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        extracted_data = extract_data_from_pdf(pdf_file)
        extracted_data["file_name"] = os.path.basename(pdf_file)  # Store the file name for reference
        results.append(extracted_data)

    # Convert results to Pandas DataFrame
    df = pd.DataFrame(results)
    return df

# Example usage: Process specific uploaded PDFs
# pdf_files = [varian_file, varian_file2]

if __name__ == "__main__":
    directory_path = "/Users/yeochanyoun/Desktop/projects/LINAC_prediction/clean_data/varian_reports_v1/"
    pdf_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.pdf')]
    df_results = process_multiple_pdfs(pdf_files)
    df_results.to_csv("/Users/yeochanyoun/Desktop/projects/LINAC_prediction/clean_data/varian_v1_2.csv", index=False)