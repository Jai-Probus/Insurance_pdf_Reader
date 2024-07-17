import re
from datetime import datetime
from PyPDF2 import PdfReader

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# Function to extract details using regex
def extract_details(text):
    if not text:
        return {}

    details = {}

    def extract_field(pattern, text, default='none'):
        match = re.search(pattern, text)
        return match.group(1).strip() if match else default

    # Extract dates using a unified function
    def extract_dates(period_text):
        match_dates = re.search(r'(\d{2}\s\w{3}\s\'\d{2}).*\s*to\s*(\d{2}\s\w{3}\s\'\d{2}).*', period_text)
        if match_dates:
            start_date = convert_to_yyyymmdd(match_dates.group(1).strip())
            end_date = convert_to_yyyymmdd(match_dates.group(2).strip())
            return start_date, end_date
        return 'none', 'none'

    details['Policy Number'] = extract_field(r'Policy No & Certificate No\s*:\s*(\d+)', text)
    details["Insured Name"] = extract_field(r'Insured Name\s*:\s*(.*)', text)
    details["Customer's Phone Number"] = extract_field(r'Customer contact number\s*:\s*(.*)', text)
    details["Customer's Email"] = extract_field(r'\s+([\w\.-]+@[\w\.-]+)', text)
    #details["Customer's Email"] = extract_field(r'Email ID\s*:\s*(.*)', text)
    details["Insured Address"] = extract_field(r'Address for Communication\s*:\s*([\s\S]*?)(?=4. Vehicle Type)', text).replace('\n', ', ') if extract_field(r'Address for Communication\s*:\s*([\s\S]*?)(?=Vehicle Type)', text) else 'none'
    details['Date of Issuance'] = convert_to_yyyymmdd(extract_field(r'Policy Issuance Date\s*:\s*(.*)', text))

    # TP cover period
    tp_cover_period = extract_field(r'TP cover period\s*:\s*(.*)', text)
    details['TP Cover Start Date'], details['TP Cover End Date'] = extract_dates(tp_cover_period)

    # OD cover period
    od_cover_period = extract_field(r'Period of Insurance OD cover period\s*:\s*(.*)', text)
    details['OD Cover Start Date'], details['OD Cover End Date'] = extract_dates(od_cover_period)

    # CPA cover period
    cpa_cover_period = extract_field(r'CPA to Owner driver cover Period\s*:\s*(.*)', text)
    details['CPA Cover Start Date'], details['CPA Cover End Date'] = extract_dates(cpa_cover_period)

    details['POS Phone Number'] = extract_field(r'POS Number\s*:\s*(\d+)', text)
    details['POS Email'] = extract_field(r'POS Email\s*:\s*([\w\.-]+@[\w\.-]+)', text)

    details["Customer's Email"] = extract_field(r'\s+([\w\.-]+@[\w\.-]+)', text)
    #details['POS Contact Number'] = extract_field(r'Contact No. of POS\s*:\s*(.*)', text)
    reg_number = extract_field(r'Registration no\s*:\s*(.*)', text)
    reg_number_match = re.search(r'([A-Z]{2})\s*(\d{2})\s*([A-Z]{2,3})\s*(\d+)', reg_number)
    details['Registration Number'] = f"{reg_number_match.group(1)}{reg_number_match.group(2)}{reg_number_match.group(3)}{reg_number_match.group(4)}" if reg_number_match else 'none'
    reg_auth = extract_field(r'Registration Authority\s*:\s*(.*)', text)
    reg_auth_match = re.search(r'([A-Z]{2})\s*(\d{2})$', reg_auth)
    details['RTO'] = f"{reg_auth_match.group(1)}{reg_auth_match.group(2)}" if reg_auth_match else 'none'

    make_model_match = re.search(r'Make/Model\s*:\s*(.*)', text)
    if make_model_match:
        make_model = make_model_match.group(1).strip()
        make_model_parts = make_model.split('/')
        details['Make'] = make_model_parts[0].strip() if len(make_model_parts) > 0 else 'none'
        details['Model'] = make_model_parts[1].strip() if len(make_model_parts) > 1 else 'none'
    else:
        details['Make'] = 'none'
        details['Model'] = 'none'

    details['Variant'] = extract_field(r'Variant\s*:\s*(.*)', text)
    details['Year of Manufacturing'] = extract_field(r'Mfg Year\s*:\s*(.*)', text)
    details['Date of Registration'] = convert_ddmmyyyy_to_yyyymmdd(extract_field(r'Date of Registration\s*:\s*(.*)', text))
    details['Vehicle Type'] = extract_field(r'Vehicle Type\s*:\s*(.*)', text)
    details['Fuel Type'] = extract_field(r'Fuel Type\s*:\s*(.*)', text)
    details['Chassis Number'] = extract_field(r'Chassis number\s*:\s*(.*)', text)
    details['Engine Number'] = extract_field(r'Engine Number/Battery Number\s*:\s*([A-z0-9]*)', text).rstrip('/')
    details['Seating Capacity'] = extract_field(r'Seating Capacity \(including driver\)\s*:\s*(.*)', text)
    details['Previous Policy Number'] = extract_field(r"1\. Policy Number\s+(.*?)\s", text)
    details['Previous Insurer Name'] = extract_field(r'Name & address if the Insurer\s*:\s*(.*)', text)
    details['Total IDV'] = extract_field(r'Insured’s Declared Value\s*:\s*([\d,]+)', text)
    details['Total Own Damage Premium (A)'] = extract_field(r'Total Own Damage Premium \(A\)\s*₹\s*([\d,]+\.\d{2})',text)
    details['Total Liability Premium (B)'] = extract_field(r'Total Liability Premium \(B\)\s*₹\s*([\d,]+\.\d{2})', text)
    details['Total Add On Premium (C)'] = extract_field(r'Total Add On Premium \(C\)\s*₹\s*([\d,]+\.\d{2})', text)
    details['Depreciation Reimbursement'] = extract_field(r'Add: Depreciation Reimbursement\s\(TA 16\)[\s]*([\d,]+\.\d{2})', text)
    details['No Claim Bonus Percentage'] = extract_field(r'Less: No claim bonus\s*\(\d+%\)\s*([0-9]+(?:\.\d{1,2})?)', text)
    details['Net Premium'] = extract_field(r'Net Premium \((?:A\+B\+C|A|B|C)\)\s*₹\s*([\d,]+\.\d{2})', text)
    igst = float(extract_field(r'IGST @18 %\s*₹\s*([\d,]+\.\d{2})', text, '0').replace(',', ''))
    cgst = float(extract_field(r'CGST @9 %\s*₹\s*([\d,]+\.\d{2})', text, '0').replace(',', ''))
    sgst = float(extract_field(r'SGST @9 %\s*₹\s*([\d,]+\.\d{2})', text, '0').replace(',', ''))

    # Calculate total GST
    details['GST'] = igst + cgst + sgst


    details['Total Premium'] = extract_field(r'Total Policy Premium\s*\s*([\d,]+\.\d{2})', text)

    return details

def convert_to_yyyymmdd(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%d %b \'%y')
        return date_obj.strftime('%Y/%m/%d')
    except ValueError:
        return 'Invalid Date Format'

def convert_ddmmyyyy_to_yyyymmdd(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        return date_obj.strftime('%Y/%m/%d')
    except ValueError:
        return 'Invalid Date Format'

# Test with a sample PDF path
pdf_path = 'test_pdfs/6101868991-00.pdf'  # Update with your PDF path

# Extract text from PDF
pdf_text = extract_text_from_pdf(pdf_path)

# Extract details using regex
extracted_details = extract_details(pdf_text)

# Print extracted details
for key, value in extracted_details.items():
    print(f'{key}: {value}')
