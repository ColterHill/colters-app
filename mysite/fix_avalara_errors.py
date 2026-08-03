import pandas as pd

# Paths to your files
input_csv = '/Users/colterhill/Documents/Avalara Tax Data/Jan 2026/BTInvoicesJan2026.csv'
error_ids_csv = "avalara_errors.csv"  # or a manual list in another CSV
output_csv = "BT Invoices January 2026 - Errors Only.csv"

# Load full invoice dataset
df = pd.read_csv(input_csv)

# Clean column names (remove any leading/trailing spaces)
df.columns = df.columns.str.strip()

# List of failed invoice IDs
failed_ids = [
137171, 137201, 137202, 137307, 137330, 137346, 137364, 137483, 137504, 137671, 137686, 137754, 137853, 137854, 137867, 138065, 138101, 138222, 138235, 138257, 138321, 138322, 138397, 138474
]

# Debug: Check data type and sample values
print(f"InvoiceID column dtype: {df['InvoiceID'].dtype}")
print(f"Sample InvoiceIDs from CSV: {df['InvoiceID'].head().tolist()}")
print(f"Looking for IDs: {failed_ids[:5]}")

# Remove any rows where InvoiceID is the header string (duplicate headers in CSV)
df = df[df['InvoiceID'] != 'InvoiceID']
print(f"After removing duplicate headers: {len(df)} rows")

# Ensure InvoiceID column is integer type
df['InvoiceID'] = df['InvoiceID'].astype(int)

# Filter for only those InvoiceIDs
filtered_df = df[df["InvoiceID"].isin(failed_ids)]

print(f"Found {len(filtered_df)} rows matching {filtered_df['InvoiceID'].nunique()} unique invoice IDs")

# Write to new file
filtered_df.to_csv(output_csv, index=False)
print(f"Filtered file saved as: {output_csv}")
