import os
import sys
import pandas as pd
import gspread
import json
from gspread.exceptions import GSpreadException

def main():
    sa_env = os.environ.get("GOOGLE_SHEETS_SA")
    sheet_id = os.environ.get("SHEET_ID")

    if not sa_env or not sheet_id:
        print("Error: Missing GOOGLE_SHEETS_SA or SHEET_ID environment variable.")
        sys.exit(1)

    csv_path = "data/neihu_clean.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist.")
        sys.exit(1)

    try:
        df = pd.read_csv(csv_path)
        # Handle nan values that gspread might choke on
        df = df.fillna("")

        # Authenticate with service account
        # Handle whether GOOGLE_SHEETS_SA is a file path or direct JSON
        if sa_env.strip().startswith("{"):
            sa_info = json.loads(sa_env)
            gc = gspread.service_account_from_dict(sa_info)
        else:
            gc = gspread.service_account(filename=sa_env)

        # Open spreadsheet
        sh = gc.open_by_key(sheet_id)

        # Get the first worksheet
        worksheet = sh.get_worksheet(0)

        # Clear existing data
        worksheet.clear()

        # Prepare data for writing
        header = df.columns.tolist()
        values = df.values.tolist()
        data_to_write = [header] + values

        # Write to sheet
        worksheet.update(values=data_to_write, range_name='A1')

        print("Successfully updated Google Sheet.")
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
