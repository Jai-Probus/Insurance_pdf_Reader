import pdfplumber

def strip_whitespaces(all_tables):
    new_table = []
    for table in all_tables:
        new_table_for_current_table = []
        for row_val in table:
            new_row_val = []
            for cell_val in row_val:
                if cell_val:  # Ensure cell_val is not None or empty
                    new_text = cell_val.strip()
                    if new_text:  # Ensure new_text is not empty after cleaning
                        new_row_val.append(new_text)
            if new_row_val:  # Append the row only if it's not empty
                new_table_for_current_table.append(new_row_val)
        if new_table_for_current_table:  # Append the table only if it's not empty
            new_table.append(new_table_for_current_table)
    return new_table

def convert_to_dict(cleaned_table):
    if len(cleaned_table) >= 2:
        temporary_dict = {cleaned_table[0][i]: cleaned_table[1][i] for i in range(len(cleaned_table[0]))}
        return temporary_dict
    else:
        return {}

def extract_veh_details(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_tables = []
        # Process only pages 2 and 3
        for page_num in range(1, 3):  # Page numbers are zero-indexed
            page = pdf.pages[page_num]
            tables = page.extract_tables()
            all_tables.extend(tables)
            #for table in tables:
             #   if table:  # Ensure the table is not empty
              #      all_tables.(table)
    cleaned_tables = strip_whitespaces(all_tables)
    vehicle_details = {}
    for cleaned_table in cleaned_tables:
        vehicle_details.update(convert_to_dict(cleaned_table))
    return vehicle_details, cleaned_tables

# Test with a sample PDF path
pdf_path = "TataAIG/TataAIG_GCV/GCV_6301862812-00.pdf"

# Extract vehicle details and tables
vehicle_details, cleaned_tables = extract_veh_details(pdf_path)

# Print extracted vehicle details from tables
print("Extracted Vehicle Details from Tables:")
for key, value in vehicle_details.items():
    print(f'{key}: {value}')

# Print the list of lists of lists
print("\nList of Lists of Lists (Cleaned Tables):")
for i, table in enumerate(cleaned_tables):
    print(f"Table {i + 1}:")
    for row in table:
        print(row)
    print()
