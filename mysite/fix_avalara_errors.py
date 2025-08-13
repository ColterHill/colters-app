import pandas as pd

# Paths to your files
input_csv = '/Users/colterhill/Documents/Tax Data/Avalara Transactions Uploads/Jul 25/BT Invoices July 2025.csv'
error_ids_csv = "avalara_errors.csv"  # or a manual list in another CSV
output_csv = "BT Refunds July 2025 - Errors Only.csv"

# Load full invoice dataset
df = pd.read_csv(input_csv)

# List of failed invoice IDs
failed_ids = [
121739, 121811, 121812, 121813, 121825, 121834, 121849, 121926, 122161, 122270, 122271, 122272, 122279, 122437, 122637, 122717, 122728, 122730, 122786, 122859, 122885, 122907, 122986, 123113, 123143, 123145, 123146, 123151, 123263, 123264, 123391, 123392, 123470, 123635, 123704, 123712, 123838, 123911, 123951, 123962, 123979, 123992, 124163, 124198, 124329, 124330, 124356, 124590, 124591, 124605
]

# Filter for only those InvoiceIDs
filtered_df = df[df["InvoiceID"].isin(failed_ids)]

# Write to new file
filtered_df.to_csv(output_csv, index=False)
print(f"Filtered file saved as: {output_csv}")
