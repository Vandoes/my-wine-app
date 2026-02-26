import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ASC 酒款推薦", page_icon="🍷", layout="wide")

@st.cache_data
def load_data():
    # 1. 智慧尋找 CSV
    all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    target_file = next((f for f in all_files if 'Price List' in f), None)
    
    if not target_file:
        st.error("❌ GitHub 中找不到 CSV 檔案，請確認檔案已上傳。")
        return pd.DataFrame()

    # 2. 嘗試讀取（不指定標題行，手動處理）
    df = None
    for enc in ['utf-8-sig', 'cp950', 'utf-8', 'gbk']:
        try:
            # 讀取整份檔案
            df_full = pd.read_csv(target_file, encoding=enc, header=None)
            
            # 尋找包含 "Product Name" 的那一行作為標題
            header_idx = None
            for i in range(len(df_full)):
                row_str = df_full.iloc[i].astype(str).values
                if any('Product Name' in s for s in row_str):
                    header_idx = i
                    break
            
            if header_idx is not None:
                # 重新讀取，將找到的那一行設為 header
                df = pd.read_csv(target_file, encoding=enc, skiprows=header_idx)
                break
        except:
            continue

    if df is None:
        st.error("❌ 讀取失敗，請確認 CSV 檔案是否包含 'Product Name' 字樣。")
        return pd.DataFrame()

    # 3. 清理欄位 (處理 CSV 中的空列與空欄位)
    df.columns = [str(c).strip() for c in df.columns]
    # 移除所有 'Unnamed' 的空欄位
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # 模糊尋找關鍵欄位
    col_map = {}
    for col in df.columns:
        if 'Product Name' in col: col_map[col] = 'Name'
        if 'Price' in col: col_map[col] = 'Price'
        if 'Code' in col: col_map[col] = 'Code'
        if 'Vintage' in col: col_map[col] = 'Vintage'
        if 'Country' in col: col_map[col] = 'Country'

    df = df.rename(columns=col_map)

    # 4. 數據清洗
    if 'Name' in df.columns and 'Price' in df.columns:
        # 價格轉數字 (移除 HK$, 逗號等)
        df['Price'] = pd.to_numeric(df['Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        # 移除沒有品名或價格的行
        df = df.dropna(subset=['Name', 'Price'])
        return df
    else:
        st.error(f"❌ 找不到關鍵欄位。目前的欄位有: {list(df.columns)}")
        return pd.DataFrame()

# --- 介面 ---
st.title("🍷 ASC 酒款智能推薦系統")
data = load_data()

if not data.empty:
    st.sidebar.header("🔍 篩選條件")
    
    # 搜尋框
    search = st.sidebar.text_input("輸入酒名關鍵字 (如: Rothschild)")
    
    # 價格滑桿
    max_p = int(data['Price'].max())
    budget = st.sidebar.slider("預算範圍 (HK$)", 0, max_p, (0, 1500), step=50)

    # 過濾邏輯
    filtered = data.copy()
    if search:
        filtered = filtered[filtered['Name'].str.contains(search, case=False, na=False)]
    
    filtered = filtered[(filtered['Price'] >= budget[0]) & (filtered['Price'] <= budget[1])]

    # 顯示結果
    st.success(f"找到 {len(filtered)} 個推薦選項")
    
    # 格式化顯示
    st.dataframe(
        filtered[['Code', 'Name', 'Vintage', 'Price']].sort_values('Price', ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Price": st.column_config.NumberColumn("價格 (HK$)", format="$%d"),
            "Name": st.column_config.TextColumn("產品名稱", width="large")
        }
    )
else:
    st.info("💡 提示：請確保您的 CSV 檔案已正確上傳至 GitHub，且檔案中包含 'Product Name' 與 'Price' 欄位。")