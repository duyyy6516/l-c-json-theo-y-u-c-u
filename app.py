import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Dashboard", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

def normalize_keys(data):
    if isinstance(data, list): return [normalize_keys(item) for item in data]
    elif isinstance(data, dict): return {str(k).lower(): normalize_keys(v) for k, v in data.items()}
    return data

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        clean_data = normalize_keys(data)
        if isinstance(clean_data, dict): clean_data = [clean_data]
        
        df = pd.json_normalize(clean_data)
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()].drop_duplicates().fillna(0)

        # Xử lý thời gian và số
        time_col = next((col for col in df.columns if 'thời gian' in col.lower() or 'time' in col.lower()), None)
        if time_col:
            df[time_col] = df[time_col].astype(str).str.replace('-', ':', regex=False)
            df[time_col] = df[time_col].apply(lambda x: x.replace(':', '-', 2) if len(x) > 10 else x)
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            df = df.dropna(subset=[time_col])

        for col in df.columns:
            if col != time_col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 1. Bảng dữ liệu gốc
        st.subheader("📋 Bảng dữ liệu gốc")
        st.data_editor(df, use_container_width=True)
        
        st.divider()

        # 2. KHU VỰC ĐIỀU KHIỂN (Dashboard)
        st.subheader("⚙️ Thiết lập biểu đồ")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("Chọn khoảng thời gian:")
            min_date = df[time_col].min().date() if time_col else pd.to_datetime('today').date()
            max_date = df[time_col].max().date() if time_col else pd.to_datetime('today').date()
            start_date, end_date = st.date_input("Khoảng thời gian:", value=(min_date, max_date))
            
        with col2:
            st.write("Chọn các chỉ số:")
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            # Dùng container để các checkbox nằm gọn
            with st.container():
                cols_check = st.columns(4)
                selected_keys = []
                for i, key in enumerate(numeric_cols):
                    if cols_check[i % 4].checkbox(key.upper(), key=f"check_{key}"):
                        selected_keys.append(key)

        # --- NÚT TẠO BIỂU ĐỒ ---
        if st.button("🚀 TẠO BIỂU ĐỒ", type="primary"):
            if not selected_keys:
                st.warning("Vui lòng chọn ít nhất một chỉ số!")
            else:
                # Chỉ lọc dữ liệu khi đã nhấn nút
                mask = (df[time_col].dt.date >= start_date) & (df[time_col].dt.date <= end_date) if time_col else True
                df_filtered = df[mask]
                
                plot_df = df_filtered.set_index(time_col) if time_col else df_filtered
                
                st.success(f"Đang hiển thị dữ liệu từ {start_date} đến {end_date}")
                for col in selected_keys:
                    st.write(f"**Biểu đồ: {col.upper()}**")
                    st.line_chart(plot_df[col])

    except Exception as e:
        st.error(f"Lỗi: {e}")
