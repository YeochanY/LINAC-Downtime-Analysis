import fitz  # PyMuPDF
import os
import re
import pandas as pd
from tqdm import tqdm

def extract_report_data(file_path):
    with fitz.open(file_path) as doc:
        text = "\n".join(page.get_text() for page in doc)
    filename = os.path.splitext(os.path.basename(file_path))[0]

    def find(pattern, group=1, flags=0, fallback=""):
        match = re.search(pattern, text, flags)
        return match.group(group).strip() if match else fallback

    # Extract time in/out from service time table
    time_entries = re.findall(
        r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}\s+[AP]M)\s+(\d{1,2}:\d{2}\s+[AP]M)", text
    )
    time_in = f"{time_entries[0][0]} {time_entries[0][1]}" if time_entries else ""
    time_out = f"{time_entries[-1][0]} {time_entries[-1][2]}" if time_entries else ""

    # Extract core metadata
    work_order_id = find(r"Notification No\.\s+(\d+)")
    machine_id = find(r"Equipment ID\s+Equipment Name\s+([A-Z0-9]+)")
    subject = find(r"Reason for Call\s+([^\n]+)")
    description = find(r"Corrective Action Comments(.*?)Times on site", flags=re.DOTALL).strip()
    malfunction_start = find(r"Event Date\s+([\d/]+\s+\d+:\d+:\d+\s+[AP]M?)")
    machine_release = find(r"Equipment Released\s+Customer Signature\s+(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+[AP]M)")

    # Extract hours from totals line
    hours_block = re.search(r"Total [^\n]*?\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", text)
    if hours_block:
        travel_hours, total_work_hours, site_hours = hours_block.groups()
    else:
        travel_hours = total_work_hours = site_hours = ""

    return {
        "work_order_id": work_order_id,
        "machine_id": machine_id,
        "subject": subject,
        "description": description,
        "malfunction_start": malfunction_start,
        "machine_release": machine_release,
        "time_in": time_in,
        "time_out": time_out,
        "down_time_hours": "",  # Optional: compute using datetime
        "site_hours": site_hours,
        "travel_hours": travel_hours,
        "total_work_hours": total_work_hours,
        "report_source": "varian",
        "file_name": filename
    }

def extract_from_folder(folder_path):
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    data = []

    for file in tqdm(pdf_files, desc="Processing PDFs"):
        full_path = os.path.join(folder_path, file)
        data.append(extract_report_data(full_path))

    df = pd.DataFrame(data)
    return df


# === Run the extraction ===
if __name__ == "__main__":
    folder = "/Users/yeochanyoun/Desktop/projects/LINAC_prediction/clean_data/varian_reports_v2"  # <-- Change this!
    df = extract_from_folder(folder)
    df.to_csv("/Users/yeochanyoun/Desktop/projects/LINAC_prediction/clean_data/varian_v2.csv", index=False)