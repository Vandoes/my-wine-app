import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ASC 酒款智能推薦", page_icon="🍷", layout="wide")

@st.cache_data
def load_data():
    # --- 智慧搜尋檔案 ---
    # 自動找出當前資料夾下所有 .csv 檔案
    all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    # 優先找名字裡有 'Price List' 的檔案
    target_file = None
    for f in all_files:
        if 'Price List' in f:
            target_file = f
            break
            
    if target_file is None:
        st.error("❌ 在您的 GitHub 中找不到任何 CSV 檔案！請確保您已上傳 CSV。")
        st.info(f"目前資料夾內的檔案有: {all_files}")
        return pd.DataFrame()

    st.toast(f"成功讀取檔案: {target_file}")

    # 嘗試不同編碼讀取
    encodings = ['utf-8', 'cp950', 'gbk', 'utf-8-sig']
    df = None
    for enc in encodings:
        try:
            # 根據你的檔案結構，跳過前 4 行
            df = pd.read_csv(target_file, skiprows=4, encoding=enc)
            # 清理欄位空白
            df.columns = df.columns.str.strip()
            # 檢查關鍵欄位是否存在
            if 'Product Name' in df.columns:
                break
        except:
            continue
            
    if df is None or 'Product Name' not in df.columns:
        st.error("❌ 檔案讀取失敗或格式不符。請檢查 CSV 內容。")
        return pd.DataFrame()

    # --- 數據清洗 ---
    # 處理價格欄位
    if 'Price HK$' in df.columns:
        df['Price HK$'] = df['Price HK$'].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df['Price HK$'] = pd.to_numeric(df['Price HK$'], errors='coerce')
    
    # 過濾無效行
    df = df.dropna(subset=['Product Name', 'Price HK$'])
    return df

# --- 介面設計 ---
st.title("🍷 ASC 酒款智能推薦系統")
data = load_data()

if not data.empty:
    st.sidebar.header("🔍 篩選條件")
    
    # 關鍵字
    search = st.sidebar.text_input("產品名稱關鍵字")
    
    # 國家 (如果有 Country 欄位的話)
    if 'Country' in data.columns:
        countries = sorted(data['Country'].dropna().unique().astype(str))
        sel_country = st.sidebar.multiselect("📍 選擇國家/產區", countries)
    else:
        sel_country = []
        st.sidebar.info("提示：CSV 檔案中未發現 'Country' 欄位")

    # 價格
    max_p = int(data['Price HK$'].max())
    budget = st.sidebar.slider("💰 預算範圍 (HK$)", 0, max_p, (0, 2000))

    # 過濾
    filtered = data.copy()
    if search:
        filtered = filtered[filtered['Product Name'].str.contains(search, case=False, na=False)]
    if sel_country:
        filtered = filtered[filtered['Country'].isin(sel_country)]
    filtered = filtered[(filtered['Price HK$'] >= budget[0]) & (filtered['Price HK$'] <= budget[1])]

    # 顯示
    st.success(f"找到 {len(filtered)} 款建議選項")
    
    # 選擇要顯示的欄位
    cols = [c for c in ['Code', 'Product Name', 'Vintage', 'Country', 'Price HK$'] if c in filtered.columns]
    st.dataframe(
        filtered[cols].sort_values('Price HK$', ascending=False),
        hide_index=True,
        use_container_width=True
    )