import pandas as pd

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

    1. Filter: CASE_T=='買賣', DISTRICT=='內湖區', CASE_F not in ('土地','車位').
    2. Drop rows where UPRICE is empty, NaN, or '0'.
    3. Convert SDATE (ROC) to ISO format.
    4. Add '含車位' boolean column based on UPNOTE == '是'.
    5. Normalize BUITYPE.
    6. Rename and select specific columns.
    """
    # Filter 1: CASE_T, DISTRICT, CASE_F
    df = df[(df['CASE_T'] == '買賣') &
            (df['DISTRICT'] == '內湖區') &
            (~df['CASE_F'].isin(['土地', '車位']))].copy()

    # Filter 2: UPRICE is not empty or '0'
    # Ensure UPRICE is handled as string initially to catch empty strings, then convert appropriately
    # Some might be numeric so handle carefully
    # Fill NA with empty string first to make string operations safe if they are objects
    # Or just use pd.to_numeric with coerce

    # Check if empty string or '0' (or 0)
    # First, let's convert to numeric, coercing errors to NaN. Then drop NaNs and 0s.
    # UPRICE could be float
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
    target_columns = ['交易日期', '建物型態', '總價萬元', '每坪單價萬元', '建物面積坪', '含車位', '地址']
    df = df[target_columns]

    return df

if __name__ == "__main__":
    input_file = "data/RPWeekData(1150617).csv"
    output_file = "data/neihu_clean.csv"

    # 1. Read CSV with encoding utf-8-sig
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    # 2-7. Clean data
    cleaned_df = clean_data(df)

    # Save output
    cleaned_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # 8. Print stats
    row_count = len(cleaned_df)
    # Median EXCLUDING 含車位 rows
    df_no_park = cleaned_df[~cleaned_df['含車位']]
    median_uprice = df_no_park['每坪單價萬元'].median()

    print(f"Row count: {row_count}")
    print(f"Median 每坪單價萬元 (excluding 含車位): {median_uprice}")
