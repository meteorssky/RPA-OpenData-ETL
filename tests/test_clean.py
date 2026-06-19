import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from fetch_clean import convert_roc_date, clean_data, normalize_buitype

def test_convert_roc_date():
    assert convert_roc_date(1150411) == "2026-04-11"
    assert convert_roc_date("1150411") == "2026-04-11"
    assert convert_roc_date(990101) == "2010-01-01"

def test_filtering_logic():
    data = {
        'CASE_T': ['買賣', '租賃', '買賣', '買賣', '買賣'],
        'DISTRICT': ['內湖區', '內湖區', '信義區', '內湖區', '內湖區'],
        'CASE_F': ['房屋', '房屋', '房屋', '土地', '房屋'],
        'UPRICE': ['10', '10', '10', '10', '0'],
        'SDATE': ['1150411', '1150411', '1150411', '1150411', '1150411'],
        'UPNOTE': ['-', '-', '-', '-', '-'],
        'BUITYPE': ['公寓', '公寓', '公寓', '公寓', '公寓'],
        'TPRICE': [100, 100, 100, 100, 100],
        'FAREA': [10, 10, 10, 10, 10],
        'LOCATION': ['addr1', 'addr2', 'addr3', 'addr4', 'addr5']
    }
    df = pd.DataFrame(data)
    cleaned_df = clean_data(df)

    assert len(cleaned_df) == 1
    assert cleaned_df.iloc[0]['地址'] == 'addr1'

def test_drop_empty_uprice():
    data = {
        'CASE_T': ['買賣', '買賣', '買賣', '買賣'],
        'DISTRICT': ['內湖區', '內湖區', '內湖區', '內湖區'],
        'CASE_F': ['房屋', '房屋', '房屋', '房屋'],
        'UPRICE': ['10', '', '0', None],
        'SDATE': ['1150411'] * 4,
        'UPNOTE': ['-'] * 4,
        'BUITYPE': ['公寓'] * 4,
        'TPRICE': [100] * 4,
        'FAREA': [10] * 4,
        'LOCATION': ['addr1', 'addr2', 'addr3', 'addr4']
    }
    df = pd.DataFrame(data)
    cleaned_df = clean_data(df)

    assert len(cleaned_df) == 1
    assert cleaned_df.iloc[0]['地址'] == 'addr1'

def test_normalize_buitype():
    assert normalize_buitype('公寓(5樓含以下無電梯)') == '公寓'
    assert normalize_buitype('華廈(10層含以下有電梯)') == '華廈'
    assert normalize_buitype('住宅大樓(11層含以上有電梯)') == '住宅大樓'
    assert normalize_buitype('大樓') == '住宅大樓'
    assert normalize_buitype('透天厝') == '透天厝'
    assert normalize_buitype('廠辦') == '其他'

def test_has_parking_flag():
    data = {
        'CASE_T': ['買賣', '買賣', '買賣'],
        'DISTRICT': ['內湖區', '內湖區', '內湖區'],
        'CASE_F': ['房屋', '房屋', '房屋'],
        'UPRICE': ['10', '20', '30'],
        'SDATE': ['1150411'] * 3,
        'UPNOTE': ['-', '否', '是'],
        'BUITYPE': ['公寓'] * 3,
        'TPRICE': [100] * 3,
        'FAREA': [10] * 3,
        'LOCATION': ['addr1', 'addr2', 'addr3']
    }
    df = pd.DataFrame(data)
    cleaned_df = clean_data(df)

    assert len(cleaned_df) == 3
    assert not cleaned_df.iloc[0]['含車位']
    assert not cleaned_df.iloc[1]['含車位']
    assert cleaned_df.iloc[2]['含車位']
