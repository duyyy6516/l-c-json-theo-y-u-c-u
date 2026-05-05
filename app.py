import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

# Hàm làm phẳng JSON (Xử lý mọi cấp độ lồng nhau)
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
        
        # Làm phẳng dữ liệu từ mọi cấu trúc lồng nhau
        df = pd.DataFrame([flatten_json(row) for row in data])
        
        # Làm sạch cột rỗng và trùng lặp
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()].drop_duplicates().fillna(0)

        # 1. Tự động nhận diện cột thời gian (quét các cột chứa time/thời gian)
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        if time_col:
            df[time_col] = pd.to_datetime(df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
            df = df.dropna(subset=[time_col])

        # 2. Chuyển cột sang số để vẽ biểu đồ
        for col in df.columns:
            if col != time_col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. BẢNG DỮ LIỆU (Luôn hiển thị)
        st.subheader("📋 Bảng dữ liệu gốc")
        st.data_editor(df, use_container_width=True)
        
        st.divider()

        # 4. DASHBOARD ĐIỀU KHIỂN
        st.subheader("⚙️ Thiết lập biểu đồ")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("Khoảng thời gian:")
            min_date = df[time_col].min().date() if time_col else pd.to_datetime('today').date()
            max_date = df[time_col].max().date() if time_col else pd.to_datetime('today').date()
            start_date, end_date = st.date_input("Chọn:", value=(min_date, max_date))
            
        with col2:
            st.write("Chọn chỉ số:")
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            cols_check = st.columns(4)
            selected_keys = [key for i, key in enumerate(numeric_cols) if cols_check[i % 4].checkbox(key.upper(), key=f"check_{key}")]

        # 5. NÚT TẠO BIỂU ĐỒ (Chỉ chạy khi bấm)
        if st.button("🚀 TẠO BIỂU ĐỒ", type="primary"):
            if not selected_keys:
                st.warning("Vui lòng chọn ít nhất một chỉ số!")
            else:
                mask = (df[time_col].dt.date >= start_date) & (df[time_col].dt.date <= end_date) if time_col else True
                df_filtered = df[mask]
                
                plot_df = df_filtered.set_index(time_col) if time_col else df_filtered
                
                st.success(f"Dữ liệu từ {start_date} đến {end_date}")
                for col in selected_keys:
                    st.write(f"**Biểu đồ: {col.upper()}**")
                    st.line_chart(plot_df[col])

    except Exception as e:
        st.error(f"Lỗi cấu trúc file: {e}")
