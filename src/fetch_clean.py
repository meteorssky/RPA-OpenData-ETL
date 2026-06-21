import pandas as pd
import json
import urllib.request
import urllib.parse
import os
import re

def clean_address_for_geocode(addr):
    addr = str(addr)
    # Strip floor suffix and trailing '等'
    addr = re.sub(r'([一二三四五六七八九十百千0-9]+樓|樓|之).*', '', addr)
    addr = re.sub(r'等$', '', addr)
    return "台北市內湖區" + addr

def geocode_address(address, api_key):
    if not api_key:
        return None, None
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data['status'] == 'OK' and len(data['results']) > 0:
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng']
            else:
                print(f"Geocoding failed for {address}: {data.get('status')}")
    except Exception as e:
        print(f"Error geocoding {address}: {e}")
    return None, None

def convert_roc_date(sdate):
    """Converts ROC YYYMMDD to ISO YYYY-MM-DD."""
    sdate_str = str(sdate)
    if not sdate_str or sdate_str == 'nan':
        return sdate

    # Pad to at least 6 characters in case year is < 100
    if len(sdate_str) < 6:
        return sdate

    year = int(sdate_str[:-4]) + 1911
    month = sdate_str[-4:-2]
    day = sdate_str[-2:]
    return f"{year}-{month}-{day}"

def normalize_buitype(btype):
    """Normalizes BUITYPE into {公寓, 華廈, 住宅大樓, 透天厝, 其他}."""
    if pd.isna(btype):
        return '其他'

    btype_str = str(btype)
    if '公寓' in btype_str:
        return '公寓'
    elif '華廈' in btype_str:
        return '華廈'
    elif '住宅大樓' in btype_str or '大樓' in btype_str:
        if '透天厝' not in btype_str: # avoid '透天厝' getting classified as 大樓 just in case
            return '住宅大樓'
    elif '透天厝' in btype_str:
        return '透天厝'

    return '其他'

def clean_data(df):
    """
    Cleans the Taiwan real-estate data according to specifications.
    """
    # Filter 1: CASE_T, DISTRICT, CASE_F
    df = df[(df['CASE_T'] == '買賣') &
            (df['DISTRICT'] == '內湖區') &
            (~df['CASE_F'].isin(['土地', '車位']))].copy()

    # Filter 2: UPRICE is not empty or '0'
    df['UPRICE'] = pd.to_numeric(df['UPRICE'], errors='coerce')
    df = df[df['UPRICE'].notna()]
    df = df[df['UPRICE'] > 0]

    # 4. Add boolean 含車位
    df['含車位'] = df['UPNOTE'] == '是'

    # 3. Convert SDATE
    df['SDATE'] = df['SDATE'].apply(convert_roc_date)

    # 5. Normalize BUITYPE
    df['BUITYPE'] = df['BUITYPE'].apply(normalize_buitype)

    # Rename columns to match target
    df = df.rename(columns={
        'SDATE': '交易日期',
        'BUITYPE': '建物型態',
        'TPRICE': '總價萬元',
        'UPRICE': '每坪單價萬元',
        'FAREA': '建物面積坪',
        'LOCATION': '地址'
    })

    # Select columns
    target_columns = ['交易日期', '建物型態', '每坪單價萬元', '含車位', '地址']
    # Check if 緯度/經度 already exist (unlikely in raw data but good for robustness)
    if '緯度' in df.columns and '經度' in df.columns:
        target_columns += ['緯度', '經度']

    df = df[target_columns]

    return df

def process_geocoding(df, maps_key):
    lats = []
    lngs = []
    indices_to_drop = []

    for idx, row in df.iterrows():
        # Only geocode if missing
        if '緯度' in row and '經度' in row and not pd.isna(row['緯度']) and not pd.isna(row['經度']):
            lats.append(row['緯度'])
            lngs.append(row['經度'])
            continue

        raw_address = row['地址']
        clean_addr = clean_address_for_geocode(raw_address)
        lat, lng = geocode_address(clean_addr, maps_key)

        if lat is not None and lng is not None:
            lats.append(lat)
            lngs.append(lng)
        else:
            print(f"Skipping row {idx}: failed to geocode {raw_address}")
            indices_to_drop.append(idx)

    df = df.drop(indices_to_drop)
    df['緯度'] = lats
    df['經度'] = lngs
    return df

if __name__ == "__main__":
    input_file = "data/RPWeekData(1150617).csv"
    output_file = "data/neihu_clean.csv"

    # 1. Read CSV with encoding utf-8-sig
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    # 2-7. Clean data
    cleaned_df = clean_data(df)

    # 8. Geocode
    maps_key = os.environ.get('MAPS_KEY')
    if not maps_key:
        print("Warning: MAPS_KEY not found in environment.")

    cleaned_df = process_geocoding(cleaned_df, maps_key)

    # Save output
    cleaned_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # 9. Print stats
    row_count = len(cleaned_df)
    df_no_park = cleaned_df[~cleaned_df['含車位']]
    median_uprice = df_no_park['每坪單價萬元'].median()

    print(f"Row count: {row_count}")
    print(f"Median 每坪單價萬元 (excluding 含車位): {median_uprice}")

    # 10. Generate web/map.html from template
    try:
        with open("web/map_template.html", "r", encoding="utf-8") as f:
            html = f.read()

        # Replace placeholders
        html = html.replace("{{MAPS_KEY}}", maps_key if maps_key else "NO_API_KEY")
        html = html.replace("{{SHEET_ID}}", os.environ.get('SHEET_ID', ''))
        html = html.replace("{{SHEETS_KEY}}", os.environ.get('SHEETS_KEY', ''))

        with open("web/map.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Generated web/map.html")
    except Exception as e:
        print(f"Error generating web/map.html: {e}")
