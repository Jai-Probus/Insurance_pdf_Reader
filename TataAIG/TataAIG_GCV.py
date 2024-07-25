import re
from datetime import datetime
from PyPDF2 import PdfReader
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

def extract_field(pattern, text, default='none'):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else default

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

def extract_details(text):
    if not text:
        return {}

    details = {}

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
    details['Start Date'] = extract_field(r'From\s*00:00\s*Hours\s*on\s*(\d{2}/\d{2}/\d{4})', text)
    details['End Date'] = extract_field(r'Midnight\s*of\s*(\d{2}/\d{2}/\d{4})', text)

    details['POS Phone Number'] = extract_field(r'POS Number\s*:\s*(\d+)', text)
    details['POS Email'] = extract_field(r'POS Email\s*:\s*([\w\.-]+@[\w\.-]+)', text)

    reg_number = extract_field(r'([A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4})', text)
    reg_number_match = re.search(r'([A-Z]{2})\s*([0-9]{2})\s*([A-Z]*)\s*([0-9]{4})', reg_number)
    details['Registration Number'] = f"{reg_number_match.group(1)}{reg_number_match.group(2)}{reg_number_match.group(3)}{reg_number_match.group(4)}" if reg_number_match else 'none'

    details['RTO'] = f"{reg_number_match.group(1)}{reg_number_match.group(2)}" if reg_number_match else 'none'

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
   # details['Year of Manufacturing'] = extract_field(r'Mfg Year\s*:\s*(.*)', text)
    details['Date of Registration'] = convert_ddmmyyyy_to_yyyymmdd(extract_field(r'Date of Registration\s*:\s*(.*)', text))
    details['Vehicle Type'] = extract_field(r'Vehicle Type\s*:\s*(.*)', text)
    details['Fuel Type'] = extract_field(r'Fuel Type\s*:\s*(.*)', text)
    details['Chassis Number'] = extract_field(r'Chassis Number\s*:\s*(.*)', text)
    details['Engine Number'] = extract_field(r'Engine Number/Battery Number\s*:\s*([A-z0-9]*)', text).rstrip('/')
    details['Seating Capacity'] = extract_field(r'Seating Capacity \(including driver\)\s*:\s*(.*)', text)
    details['Previous Policy Number'] = extract_field(r"Policy Number\*\s*:\s*(.*)\s", text)
    details['Previous Insurer Name'] = extract_field(r'Name of the Insurer\*\s*:\s*(.*)', text)
    details['Total IDV'] = extract_field(r'Insured’s Declared Value\s*:\s*([\d,]+)', text)
    details['Total Own Damage Premium (A)'] = extract_field(r'TOTAL OWN DAMAGE PREMIUM \(A\)\s*₹\s*([\d,]+\.\d{2})',text)
    details['Total Liability Premium (B)'] = extract_field(r'Net basic Liability Premium \(B\)\s*₹\s*([\d,]+\.\d{2})', text)
    details['Total Add On Premium (C)'] = extract_field(r'TOTAL ADD ON PREMIUM \(C\)\s*₹\s*([\d,]+\.\d{2})', text)
    details['NCB'] = extract_field(r'Less: No claim bonus \(\d+%\)\s*₹\s*([\d,]+\.\d{2})',text)
    details['Net Premium'] = extract_field(r"NET\s+PREMIUM\s*\((?:[A-D]\s*\+\s*)*[A-D]\)\s*₹\s*(\d+\.\d+)", text)
    net = float(extract_field(r"NET\s+PREMIUM\s*\((?:[A-D]\s*\+\s*)*[A-D]\)\s*₹\s*(\d+\.\d+)", text))
    total = float(extract_field(r'TOTAL POLICY PREMIUM\s*₹\s*([0-9\.]*)', text))


    details['GST'] = (total - net)
    details['Total Premium'] = extract_field(r'TOTAL POLICY PREMIUM\s*₹\s*([0-9\.]*)', text)

    return details


def normalize_header(header):
    return ''.join(header.split()).replace('\n', '')

def extract_make_model_variant_body_type(tables):
    table = tables[1][0]  # Use the second table
    for row in table:
        for cell in row:
            normalized_cell = normalize_header(cell)
            if normalized_cell == 'Make/Model/BodyType/Segment':
                idx = row.index(cell)
                make_model_body_type = table[table.index(row) + 1][idx]

                # Split the extracted value by '/'
                parts = make_model_body_type.split('/')

                # Extract Make, Model, Variant, and Vehicle Type
                if len(parts) == 3:
                    make = parts[0].strip()
                    model = parts[1].strip()
                    variant = parts[2].strip()
                    vehicle_type = 'none'
                elif len(parts) == 5:
                    make = parts[0].strip()
                    model = parts[1].strip()
                    variant = ' '.join(parts[2:3]).strip()
                    vehicle_type = parts[4].strip()
                else:
                    make = 'none'
                    model = 'none'
                    variant = 'none'
                    vehicle_type = 'none'

                return make, model, variant, vehicle_type

    return 'none', 'none', 'none', 'none'

def extract_engine_number(tables):
    table = tables[1][0]  # Use the second table
    for row in table:
        if 'Engine Number' in row:
            idx = row.index('Engine Number')
            engine_number = table[table.index(row) + 1][idx]
            return engine_number
    return 'none'

def extract_chassis_number(tables):
    table = tables[1][0]  # Use the second table
    for row in table:
        if 'Chassis Number' in row:
            idx = row.index('Chassis Number')
            chassis_number = table[table.index(row) + 1][idx]
            return chassis_number
    return 'none'

def extract_capacity(tables):
    table = tables[1][0]  # Use the second table
    for row in table:
        if 'icensed\narrying\napacity\ncluding\nDriver' in row:
            idx = row.index('icensed\narrying\napacity\ncluding\nDriver')
            capacity = table[table.index(row) + 1][idx]
            return capacity
    return 'none'

def extract_idv(tables):
    table = tables[1][0]  # Use the second table
    for row in table:
        if 'Vehicle IDV' in row:
            idx = row.index('Vehicle IDV')
            Vehicle_IDV = table[table.index(row) + 1][idx]
            return Vehicle_IDV
    return 'none'

def extract_manufacture_year(tables):
    table = tables[1][0]  # Use the second table
    for row in table:
        if 'Mfg. Year' in row:
            idx = row.index('Mfg. Year')
            Mfg_Year = table[table.index(row) + 1][idx]
            return Mfg_Year
    return 'none'

def main(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    details = extract_details(text)
    tables = extract_veh_details(pdf_path)

    make, model, variant, vehicle_type = extract_make_model_variant_body_type(tables)

    # Store the extracted details in the dictionary
    details['Make'] = make
    details['Model'] = model
    details['Variant'] = variant
    details['Vehicle Type'] = vehicle_type

    capacity = extract_capacity(tables)
    details['Seating Capacity'] = capacity
    IDV = extract_idv(tables)
    details['Total IDV'] = IDV


    engine_number = extract_engine_number(tables)
    details['Engine Number'] = engine_number if engine_number != 'none' else details['Engine Number']

    chassis_number = extract_chassis_number(tables)
    details['Chassis Number'] = chassis_number if chassis_number != 'none' else details['Chassis Number']

    manufacture_year = extract_manufacture_year(tables)
    details['Mfg. Year'] = manufacture_year if manufacture_year != 'none' else details['Mfg. Year']

    for key, value in details.items():
        print(f'{key}: {value}')

    print("Details extracted and printed successfully.")

if __name__ == '__main__':
    pdf_path = r'C:\Users\user\pdfreader\TataAIG\TataAIG\TataAIG_GCV_test_pdfs\GCV_6301862956-00.pdf'
    main(pdf_path)