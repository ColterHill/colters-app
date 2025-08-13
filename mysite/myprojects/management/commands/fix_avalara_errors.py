import pandas as pd

# Paths to your files
input_csv = "/Users/colterhill/Documents/Tax Data/Avalara Transactions Uploads/BT Invoices Mar 2025 Error fixes.csv"
error_ids_csv = "avalara_errors.csv"  # or a manual list in another CSV
output_csv = "BT Invoices - Errors Only.csv"

# Load full invoice dataset
df = pd.read_csv(input_csv)

# List of failed invoice IDs
failed_ids = [
    110366, 110392, 110459, 110500, 110536, 110571, 110836, 111056, 111057, 111191,
    111193, 111194, 111265, 111304, 111305, 111463, 111480, 111488, 111611, 111631,
    111632, 111638, 111774, 111807, 111854, 111867, 111906, 112129, 112130, 112131,
    112174, 112423, 112452, 112504, 112507, 112508
]

# Filter for only those InvoiceIDs
filtered_df = df[df["InvoiceID"].isin(failed_ids)]

# Write to new file
filtered_df.to_csv(output_csv, index=False)
print(f"Filtered file saved as: {output_csv}")
