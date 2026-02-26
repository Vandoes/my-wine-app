import streamlit as st
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="ASC 酒款智能推薦", page_icon="🍷", layout="wide")

# 2. 數據讀取與清洗
@st.cache_data
def load_data():
    file_name = '20260113 Price List.xlsx - Price List.csv'
    
    # 嘗試不同的編碼讀取方式
    encodings = ['utf-8', 'cp950', 'gbk', 'utf-8-sig']
    df = None
    
    for enc in encodings:
        try:
            # skiprows=4 是為了跳過你檔案中前方的空白行
            df = pd.read_csv(file_name, skiprows=4, encoding=enc)
            break # 如果成功讀取就跳出迴圈
        except (UnicodeDecodeError, Exception):
            continue
            
    if df is None:
        st.error(f"無法讀取檔案。請確保檔案名為: {file_name}")
        return pd.DataFrame()

    # 清理欄位名稱
    df.columns = df.columns.str.strip()
    
    # 數據過濾邏輯
    if 'Product Name' in df.columns:
        # 確保價格欄位存在並轉換為數字
        if 'Price HK$' in df.columns:
            df['Price HK$'] = df['Price HK$'].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df['Price HK$'] = pd.to_numeric(df['Price HK$'], errors='coerce')
        
        # 移除沒有品名或價格的行
        df = df.dropna(subset=['Product Name', 'Price HK$'])
        return df
    else:
        st.warning("檔案讀取成功但未找到 'Product Name' 欄位，請檢查 CSV 格式。")
        return pd.DataFrame()

# 3. 介面設計
st.title("🍷 ASC 酒款智能推薦系統 (修正版)")
st.markdown("---")

data = load_data()

if not data.empty:
    # 側邊欄篩選
    st.sidebar.header("🔍 篩選條件")
    search_term = st.sidebar.text_input("關鍵字搜尋")
    
    # 國家篩選
    if 'Country' in data.columns:
        countries = sorted([str(c) for c in data['Country'].unique() if pd.notna(c)])
        sel_country = st.sidebar.multiselect("📍 選擇國家/產區", countries)
    else:
        sel_country = []
    
    # 價格篩選
    max_price = int(data['Price HK$'].max())
    budget = st.sidebar.slider("💰 預算範圍 (HK$)", 0, max_price, (0, 2000), step=50)
    
    # 過濾邏輯
    final_df = data.copy()
    if search_term:
        final_df = final_df[final_df['Product Name'].str.contains(search_term, case=False, na=False)]
    if sel_country:
        final_df = final_df[final_df['Country'].isin(sel_country)]
    
    final_df = final_df[(final_df['Price HK$'] >= budget[0]) & (final_df['Price HK$'] <= budget[1])]
    
    # 顯示結果
    st.success(f"找到 {len(final_df)} 款符合條件的酒！")
    st.dataframe(
        final_df[['Code', 'Product Name', 'Vintage', 'Country', 'Price HK$']].sort_values('Price HK$', ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={"Price HK$": st.column_config.NumberColumn("價格 (HK$)", format="$%d")}
    )