import streamlit as st
import pandas as pd

st.set_page_config(page_title="ASC Wine Selector", layout="wide")

# 讀取數據函式
@st.cache_data
def load_data():
    # 讀取價格表（自動跳過標題前幾行）
    df_p = pd.read_csv('20260113 Price List.xlsx - Price List.csv', skiprows=4)
    df_s = pd.read_csv('20260113 Price List.xlsx - SOH.csv')
    
    # 清理空格
    df_p.columns = df_p.columns.str.strip()
    df_s.columns = df_s.columns.str.strip()
    
    # 合併庫存
    df = pd.merge(df_p, df_s[['Code', 'Total SOH']], on='Code', how='left')
    # 確保價格是數字
    df['Price HK$'] = pd.to_numeric(df['Price HK$'], errors='coerce')
    return df.dropna(subset=['Product Name', 'Price HK$'])

st.title("🍷 ASC 酒款智能推薦系統")

try:
    data = load_data()
    
    # 側邊欄：篩選條件
    st.sidebar.header("篩選條件")
    
    # 1. 國家篩選
    countries = sorted(data['Country'].unique().astype(str))
    sel_country = st.sidebar.multiselect("選擇國家", countries)
    
    # 2. 價格篩選
    max_p = int(data['Price HK$'].max())
    budget = st.sidebar.slider("預算範圍 (HK$)", 0, max_p, (0, 1000))
    
    # 邏輯過濾
    final_df = data.copy()
    if sel_country:
        final_df = final_df[final_df['Country'].isin(sel_country)]
    
    final_df = final_df[(final_df['Price HK$'] >= budget[0]) & (final_df['Price HK$'] <= budget[1])]
    
    # 顯示結果
    st.subheader(f"找到 {len(final_df)} 款符合條件的酒")
    st.dataframe(final_df[['Code', 'Product Name', 'Vintage', 'Country', 'Price HK$', 'Total SOH']], use_container_width=True)

except Exception as e:
    st.error(f"請確認 CSV 檔案已放入資料夾中。錯誤：{e}")