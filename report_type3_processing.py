import fitz  # PyMuPDF
import os
import re
import pandas as pd

def extract_report_data(file_path):
    """Extract structured service report data from a single Varian PDF."""
    with fitz.open(file_path) as doc:
        text = "\n".join(page.get_text() for page in doc)

    filename = os.path.splitext(os.path.basename(file_path))[0]

    def find(pattern, group=1, flags=0, fallback=""):
        match = re.search(pattern, text, flags)
        return match.group(group).strip() if match else fallback

    # Extract timestamps (Time In, Time Out, Malfunction Start, Machine Release)
    time_in = time_out = malfunction_start = machine_release = ""
    times_match = re.search(
        r"Time In\s+Time Out\s+Malfunction Start\s+Machine Release Time\s+"
        r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\s+"
        r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\s+"
        r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\s+"
        r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2})", text)
    if times_match:
        time_in, time_out, malfunction_start, machine_release = times_match.groups()

    # Extract metadata fields
    work_order_id = find(r"Work Order Number\s+(WO-\d+)")
    machine_id = find(r"Installed Product\s+([A-Z0-9]+)")
    subject = find(r"Problem Description\s+(.+?)(?:\n|Work Performed Comments)", flags=re.DOTALL)
    description = find(r"Work Performed Comments\s+(.+?)(?:\nFollow Up Comments|\n\n)", flags=re.DOTALL)

    # Extract hours
    site_hours = travel_hours = total_work_hours = ""
    hours_match = re.search(
        r"Total Travel Hours\s+Total Work Hours\s+Total Site Hours\s+Agreed Downtime\s*\n"
        r"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", text)
    if hours_match:
        travel_hours, total_work_hours, site_hours = hours_match.groups()

    return {
        "work_order_id": work_order_id,
        "machine_id": machine_id,
        "subject": subject,
        "description": description,
        "malfunction_start": malfunction_start,
        "machine_release": machine_release,
        "time_in": time_in,
        "time_out": time_out,
        "down_time_hours": "",  # Optional: can compute if needed
        "site_hours": site_hours,
        "travel_hours": travel_hours,
        "total_work_hours": total_work_hours,
        "report_source": "varian",
        "file_name": filename
    }

def extract_from_folder(folder_path):
    """Batch extract all PDFs in a folder."""
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    data = [extract_report_data(os.path.join(folder_path, f)) for f in pdf_files]
    return pd.DataFrame(data)

# === Script Execution ===
if __name__ == "__main__":
    # ✏️ CHANGE THIS to your PDF folder path
    folder = "/Users/yeochanyoun/Desktop/projects/LINAC_prediction/clean_data/varian_reports_v3"
    output_file = "/Users/yeochanyoun/Desktop/projects/LINAC_prediction/clean_data/varian_v3_2.csv"

    df = extract_from_folder(folder)
    df.to_csv(output_file, index=False)
    print(f"Extraction complete. Output saved to: {output_file}")