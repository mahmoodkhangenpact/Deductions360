import pandas as pd
import os

# Input file path
input_file = "consolidated.xlsx"
output_folder = "invoices_split"

# Create output folder if not exists
os.makedirs(output_folder, exist_ok=True)

# Read Excel
df = pd.read_excel(input_file)

# Ensure column name matches exactly
invoice_column = "invoice number"

# Loop through each unique invoice number and save separate file
for invoice_no, group in df.groupby(invoice_column):
    # Drop the invoice number column
    group = group.drop(columns=[invoice_column])
    
    # Create file name
    file_name = f"{invoice_no}.xlsx"
    output_path = os.path.join(output_folder, file_name)
    
    # Save
    group.to_excel(output_path, index=False)

print("✅ Files created in:", output_folder)
