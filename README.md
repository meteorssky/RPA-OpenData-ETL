# RPA-OpenData-ETL

This project fetches Taiwan real-estate data, cleans it, geocodes addresses, and displays them on a Google Map. The map reads data LIVE from a Google Sheet.

## Setup Instructions

### 1. Google Cloud Platform (GCP) Configuration

You need a GCP project with the following APIs enabled:
- **Maps JavaScript API**: For displaying the map in the browser.
- **Geocoding API**: For converting addresses to latitude/longitude during the data cleaning process.
- **Google Sheets API**: For reading data from the Google Sheet in the browser.

### 2. Google Sheet Setup

1. Create a Google Sheet.
2. In the Google Sheet, go to **Share** and set it to **"Anyone with the link can view"**. This is required for the browser-side Sheets API fetch.
3. Note the **Sheet ID** from the URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`.
4. Create a Service Account in GCP, download the JSON key, and share the Sheet with the service account's email (Editor access) if you want the backend to update it.

### 3. Environment Variables

Set the following environment variables:
- `MAPS_KEY`: Your GCP API key (must have Maps JS and Geocoding enabled).
- `SHEETS_KEY`: Your GCP API key (must have Sheets API enabled). You can use the same key as `MAPS_KEY` if it has the appropriate permissions.
- `SHEET_ID`: The ID of your Google Sheet.
- `GOOGLE_SHEETS_SA`: The JSON content of your service account key or the path to the JSON file.

### 4. Running the Pipeline

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the fetch and clean script:
   ```bash
   python src/fetch_clean.py
   ```
   This will generate `data/neihu_clean.csv` (including geocodes) and `web/map.html`.
3. Update the Google Sheet:
   ```bash
   python src/to_sheets.py
   ```
4. Open `web/map.html` in a browser to see the live map.

## Project Structure

- `src/fetch_clean.py`: Fetches raw data, cleans it, geocodes addresses using the Geocoding API, and generates `web/map.html` from a template.
- `src/to_sheets.py`: Uploads the cleaned data to the Google Sheet.
- `web/map_template.html`: Template for the map, which fetches data live from the Google Sheet using the Sheets API v4.
- `web/map.html`: The generated map file (static HTML, but fetches data dynamically).
- `data/`: Directory for data files.
- `tests/`: Directory for tests.
