import streamlit as st
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="ASC 酒款智能推薦", page_icon="🍷", layout="wide")

# 2. 數據讀取與清洗
@st.cache_data
def load_data():
    try:
        # 讀取 CSV 檔案 (跳過前 4 行標題，根據你檔案的格式)
        # 確保檔案名稱與 GitHub 上的完全一致
        file_name = '20260113 Price List.xlsx - Price List.csv'
        df = pd.read_csv(file_name, skiprows=4)
        
        # 清除欄位名稱前後的空白
        df.columns = df.columns.str.strip()
        
        # --- 數據清洗核心 ---
        # 確保價格是純數字 (過濾掉可能的 HK$、逗號或文字)
        if 'Price HK$' in df.columns:
            df['Price HK$'] = df['Price HK$'].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df['Price HK$'] = pd.to_numeric(df['Price HK$'], errors='coerce')
        else:
            # 如果欄位名稱變了，嘗試尋找包含 Price 的欄位
            price_col = [col for col in df.columns if 'Price' in col][0]
            df.rename(columns={price_col: 'Price HK$'}, inplace=True)
            df['Price HK$'] = pd.to_numeric(df['Price HK$'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        
        # 確保國家欄位沒有空白
        if 'Country' in df.columns:
            df['Country'] = df['Country'].fillna('Unknown')
        
        # 剔除沒有品名或沒有價格的無效資料
        df = df.dropna(subset=['Product Name', 'Price HK$'])
        
        return df
    except Exception as e:
        st.error(f"讀取資料失敗，請確認檔案名稱是否正確且位於同一資料夾。錯誤細節: {e}")
        return pd.DataFrame()

# 3. 介面設計
st.title("🍷 ASC 酒款智能推薦系統")
st.markdown("快速篩選符合預算與產區的酒款。")
st.markdown("---")

# 載入數據
data = load_data()

if not data.empty:
    # --- 側邊欄：篩選條件 ---
    st.sidebar.header("🔍 篩選條件")
    
    # 關鍵字搜尋
    search_term = st.sidebar.text_input("關鍵字搜尋 (例如: Lafite, Chablis)")
    
    # 國家篩選
    countries = sorted([str(c) for c in data['Country'].unique() if str(c) != 'Unknown'])
    sel_country = st.sidebar.multiselect("📍 選擇國家/產區", countries)
    
    # 價格篩選
    max_price = int(data['Price HK$'].max()) if not data['Price HK$'].empty else 5000
    budget = st.sidebar.slider("💰 預算範圍 (HK$)", 0, max_price, (0, 1500), step=50)
    
    # --- 邏輯過濾執行 ---
    final_df = data.copy()
    
    # 1. 關鍵字過濾
    if search_term:
        final_df = final_df[final_df['Product Name'].str.contains(search_term, case=False, na=False)]
        
    # 2. 國家過濾
    if sel_country:
        final_df = final_df[final_df['Country'].isin(sel_country)]
        
    # 3. 價格過濾
    final_df = final_df[(final_df['Price HK$'] >= budget[0]) & (final_df['Price HK$'] <= budget[1])]
        
    # --- 顯示結果 ---
    if not final_df.empty:
        st.success(f"🎉 找到 {len(final_df)} 款符合條件的酒！ (推薦最接近預算的酒款，由高至低排列)")
        
        # 整理要顯示的欄位 (確保這些欄位存在)
        available_cols = final_df.columns.tolist()
        display_cols = []
        for col in ['Code', 'Product Name', 'Vintage', 'Country', 'Price HK$']:
            if col in available_cols:
                display_cols.append(col)
                
        display_df = final_df[display_cols].sort_values('Price HK$', ascending=False)
        
        # 顯示表格 (優化價格格式)
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Price HK$": st.column_config.NumberColumn("價格 (HK$)", format="$%d")
            }
        )
    else:
        st.warning("🥲 抱歉，目前的篩選條件下沒有找到符合的酒款，請嘗試放寬預算。")