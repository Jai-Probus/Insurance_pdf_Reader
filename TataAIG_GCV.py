import re
from datetime import datetime
from PyPDF2 import PdfReader
import pdfplumber
import extract_vehicle_details
from extract_vehicle_details import extract_veh_details


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

    details['Policy Number'] = extract_field(r'Policy Number\s*:\s*(\w+)', text)
    details["Insured Name"] = extract_field(r'Name\s*:\s*(.*)', text)
    details["Customer's Phone Number"] = extract_field(r'Contact Number\s*:\s*(.*)', text)
    details["Customer's Email"] = extract_field(r'(?<!\w)(?!IGST@|SGST@|CGST@)([a-zA-Z0-9._-]+(?:\s*\n*\s*)@[a-zA-Z.-]+\.[a-zA-Z]{2,})(?![\w@])', text)
    details["Insured Address"] = extract_field(r'Address\s*:\s*([\s\S]*?)(?=Your Policy Details:)', text).replace('\n', ', ') if extract_field(r'Address for Communication\s*:\s*([\s\S]*?)(?=Vehicle Type)', text) else 'none'
    details['Date of Issuance'] = convert_ddmmyyyy_to_yyyymmdd(extract_field(r'Date\s*:\s*(.*)', text))

    # Extract the policy period
    policy_period = extract_field(r'Policy Period\s*:\s*From 00:00 Hours on\s*(\d{2}/\d{2}/\d{4})\s+to Midnight of\s*(\d{2}/\d{2}/\d{4})', text)
    details['Policy Start Date'], details['Policy End Date'] = extract_dates(policy_period)

    details['POS Phone Number'] = extract_field(r'POS Number\s*:\s*(\d+)', text)
    details['POS Email'] = extract_field(r'POS Email\s*:\s*([\w\.-]+@[\w\.-]+)', text)

    reg_number = extract_field(r'([A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4})', text)
    reg_number_match = re.search(r'([A-Z]{2})\s*([0-9]{2})\s*([A-Z]*)\s*([0-9]{4})', reg_number)
    details['Registration Number'] = f"{reg_number_match.group(1)}{reg_number_match.group(2)}{reg_number_match.group(3)}{reg_number_match.group(4)}" if reg_number_match else 'none'
    reg_auth = extract_field(r'Registration Authority\s*:\s*(.*)', text)
    reg_auth_match = re.search(r'([A-Z]{2})\s*([0-9]{2})$', reg_auth)
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
    details['Previous Policy Number'] = extract_field(r"1\. Policy Number:\s+(.*)\s", text)
    details['Previous Insurer Name'] = extract_field(r'Name & address if the Insurer\s*:\s*(.*)', text)
    details['Total IDV'] = extract_field(r'Insured’s Declared Value\s*:\s*([\d,]+)', text)
    details['Total Own Damage Premium (A)'] = extract_field(r'Total Own Damage Premium \(A\)\s*₹\s*([\d,]+\.\d{2})',text)
    details['Total Liability Premium (B)'] = extract_field(r'Total Liability Premium \(B\)\s*₹\s*([\d,]+\.\d{2})', text)
    details['Total Add On Premium (C)'] = extract_field(r'Total Add On Premium \(C\)\s*₹\s*([\d,]+\.\d{2})', text)

    details['Net Premium'] = extract_field(r"Net Premium \((?:A|B|C|\+)*\) ₹\s*([0-9,]+(?:\.\d{1,2})?)", text)
    igst = float(extract_field(r'IGST@18%\s*([0-9,]+\.[0-9]+) ₹', text, '0').replace(',', ''))
    cgst = float(extract_field(r'CGST @9%\s*([0-9,]+\.[0-9]+) ', text, '0').replace(',', ''))
    sgst = float(extract_field(r'SGST/UGST @9%\s*([0-9]+\.[0-9]+)', text, '0').replace(',', ''))

    # Calculate total GST
    details['GST'] = igst + cgst + sgst

    details['Total Premium'] = extract_field(r'Total Policy Premium\s*\s*([\d,]+\.\d{2})', text)

    return details
def extract_make_model_body_type(tables):
    for table in tables:
        for row in table:
            if 'Make / Model /\nBody Type/\nSegment' in row:
                idx = row.index('Make / Model /\nBody Type/\nSegment')
                make_model_body_type = table[table.index(row) + 1][idx]
                make, rest = make_model_body_type.split('/', 1)
                model, body_type = rest.split('/', 1) if '/' in rest else (rest, 'none')
                return make.strip(), model.strip(), body_type.strip()
    return 'none', 'none', 'none'

def extract_engine_number(tables):
    for table in tables:
        for row in table:
            if 'Engine Number' in row:
                idx = row.index('Engine Number')
                engine_number = table[table.index(row) + 1][idx]
                return engine_number
    return 'none'

def extract_chassis_number(tables):
    for table in tables:
        for row in table:
            if 'Chassis Number' in row:
                idx = row.index('Chassis Number')
                chassis_number = table[table.index(row) + 1][idx]
                return chassis_number
    return 'none'

def extract_mfg_year(tables):
    for table in tables:
        for row in table:
            if 'Mfg. Year' in row:
                idx = row.index('Mfg. Year')
                mfg_year = table[table.index(row) + 1][idx]
                return mfg_year
    return 'none'

def extract_date_of_registration(tables):
    for table in tables:
        for row in table:
            if 'Date of Registration' in row:
                idx = row.index('Date of Registration')
                date_of_registration = table[table.index(row) + 1][idx]
                try:
                    from datetime import datetime
                    datetime.strptime(date_of_registration, '%d/%m/%Y')
                    return date_of_registration
                except ValueError:
                    return 'Invalid Date Format'
    return 'none'

def extract_vehicle_type(tables):
    for table in tables:
        for row in table:
            if 'Public\nCarrier/Private\nCarrier' in row:
                idx = row.index('Public\nCarrier/Private\nCarrier')
                vehicle_type = table[table.index(row) + 1][idx]
                return vehicle_type
    return 'none'

def extract_cc(tables):
    for table in tables:
        for row in table:
            if 'L\nC\nCC/KW C\nIn' in row:
                idx = row.index('L\nC\nCC/KW C\nIn')
                cc = table[table.index(row) + 1][idx]
                return cc
    return None
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


def extract_registration_number(tables):
    registration_number = None

    for i, row in enumerate(tables):
        for j, cell in enumerate(row):
            if "Registration\nNumber" in cell:
                # The value should be in the next list (i+1) at the same index (j)
                if i + 1 < len(tables) and j < len(tables[i + 1]):
                    registration_number = tables[i + 1][j]
                break
        if registration_number:
            break

    return registration_number

# Test with a sample PDF path
pdf_path = 'TataAIG/TataAIG_GCV/GCV_6301862812-00.pdf'  # Update with your PDF path

# Extract text from PDF
pdf_text = extract_text_from_pdf(pdf_path)

# Extract details using regex
extracted_details = extract_details(pdf_text)


extracted_table_details = extract_veh_details(pdf_path)


make_model_body_type = extract_make_model_body_type(extracted_table_details)
engine_number = extract_engine_number(extracted_table_details)
chassis_number = extract_chassis_number(extracted_table_details)
mfg_year = extract_mfg_year(extracted_table_details)
cc = extract_cc(extracted_table_details)

# Display the extracted data
print(f"Make / Model / Body Type / Segment: {make_model_body_type}")
print(f"Engine Number: {engine_number}")
print(f"Chassis Number: {chassis_number}")
print(f"Mfg. Year: {mfg_year}")
print(f"CC: {cc}")

# Print extracted details
for key, value in extracted_details.items():
    print(f'{key}: {value}')
print(len(extracted_table_details))



