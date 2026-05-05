import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

def flatten_json(y):
    out = {}
    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x: flatten(x[a], name + a + '.')
        elif isinstance(x, list):
            i = 0
            for a in x:
                flatten(a, name + str(i) + '.')
                i += 1
        else: out[name[:-1]] = x
    flatten(y)
    return out

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        if isinstance(data, dict): data = [data]
        df = pd.DataFrame([flatten_json(row) for row in data])
        
        # Làm sạch cột, bỏ cột toàn rỗng
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()]
        
        # 1. NHẬN DIỆN VÀ CHUẨN HÓA CỘT THỜI GIAN NGAY TỪ ĐẦU
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        if time_col:
            # Ép kiểu an toàn, bỏ qua lỗi (Coerce)
            df[time_col] = pd.to_datetime(df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
            df = df.dropna(subset=[time_col]) # Chỉ giữ dòng có thời gian hợp lệ
        
        # 2. BẢNG GỐC (HIỂN THỊ TRƯỚC)
        st.subheader("📋 Bảng dữ liệu gốc")
        st.data_editor(df, use_container_width=True)
        st.divider()

        # 3. THIẾT LẬP (Dashboard)
        st.subheader("⚙️ Thiết lập biểu đồ")
        col1, col2 = st.columns([1, 2])
        
        start_date, end_date = None, None
        if time_col:
            with col1:
                valid_dates = df[time_col].dt.date
                start_date, end_date = st.date_input("Khoảng thời gian:", value=(valid_dates.min(), valid_dates.max()))
        
        with col2:
            numeric_cols = [c for c in df.columns if c != time_col and '_id' not in c]
            selected_keys = st.multiselect("Chọn các chỉ số (chỉ các cột số):", numeric_cols)

        # 4. NÚT TẠO (XỬ LÝ ĐỘC LẬP)
        if st.button("🚀 TẠO BIỂU ĐỒ", type="primary"):
            if not selected_keys:
                st.warning("Vui lòng chọn ít nhất một chỉ số!")
            else:
                # Lọc dữ liệu
                plot_df = df.copy()
                if time_col:
                    mask = (plot_df[time_col].dt.date >= start_date) & (plot_df[time_col].dt.date <= end_date)
                    plot_df = plot_df[mask]
                    plot_df = plot_df.set_index(time_col)
                
                # Vẽ
                for col in selected_keys:
                    st.write(f"**Biểu đồ: {col.upper()}**")
                    # Tự động ép kiểu số và vẽ
                    series = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)
                    st.line_chart(series)
    except Exception as e:
        st.error(f"Lỗi: {e}")
