import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ASC 酒款智能推薦", page_icon="🍷", layout="wide")

@st.cache_data
def load_data():
    # 1. 智慧尋找 CSV 檔案
    all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    target_file = next((f for f in all_files if 'Price List' in f), None)
    
    if not target_file:
        st.error("❌ 找不到 CSV 檔案！請確保已將 CSV 上傳至 GitHub 根目錄。")
        return pd.DataFrame()

    # 2. 嘗試不同編碼讀取
    df = None
    for enc in ['utf-8-sig', 'cp950', 'utf-8', 'gbk']:
        try:
            # 先讀取前 20 行來定位標題
            temp_df = pd.read_csv(target_file, encoding=enc, header=None, nrows=20)
            
            # 尋找包含 "Product Name" 的那一行作為標題
            header_row = None
            for i, row in temp_df.iterrows():
                if row.astype(str).str.contains('Product Name').any():
                    header_row = i
                    break
            
            if header_row is not None:
                df = pd.read_csv(target_file, encoding=enc, skiprows=header_row)
                break
        except:
            continue

    if df is None:
        st.error("❌ 檔案讀取失敗：無法辨識檔案編碼或找不到標題行。")
        return pd.DataFrame()

    # 3. 清理數據
    # 去除欄位名稱的空格
    df.columns = [str(c).strip() for c in df.columns]
    
    # 關鍵欄位改名 (防止 CSV 裡有隱藏字元)
    name_col = next((c for c in df.columns if 'Product Name' in c), None)
    price_col = next((c for c in df.columns if 'Price' in c), None)
    country_col = next((c for c in df.columns if 'Country' in c or 'CHAMPAGNE' in str(df.iloc[0])), None)

    if not name_col or not price_col:
        st.error(f"❌ 格式錯誤：找不到 'Product Name' 或 'Price' 欄位。目前的欄位有：{list(df.columns)}")
        return pd.DataFrame()

    # 統一欄位名
    df = df.rename(columns={name_col: 'Product Name', price_col: 'Price'})
    
    # 價格轉數字
    df['Price'] = pd.to_numeric(df['Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
    
    # 剔除空行
    df = df.dropna(subset=['Product Name', 'Price'])
    
    # 補足國家資訊 (因為你的 CSV 國家通常在大標題行，這部分程式會嘗試從上方填充)
    if 'Country' not in df.columns:
        df['Country'] = 'Global' 

    return df

# --- 介面 ---
st.title("🍷 ASC 酒款智能推薦系統")
data = load_data()

if not data.empty:
    st.sidebar.header("🔍 篩選")
    search = st.sidebar.text_input("搜尋酒名")
    
    # 價格滑桿
    min_p = float(data['Price'].min())
    max_p = float(data['Price'].max())
    budget = st.sidebar.slider("預算範圍 (HK$)", 0, int(max_p), (0, 1500))

    # 過濾
    filtered = data.copy()
    if search:
        filtered = filtered[filtered['Product Name'].str.contains(search, case=False, na=False)]
    
    filtered = filtered[(filtered['Price'] >= budget[0]) & (filtered['Price'] <= budget[1])]

    # 顯示
    st.success(f"找到 {len(filtered)} 個推薦選項")
    st.dataframe(
        filtered[['Product Name', 'Vintage', 'Price']].sort_values('Price', ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={"Price": st.column_config.NumberColumn("價格 (HK$)", format="$%d")}
    )