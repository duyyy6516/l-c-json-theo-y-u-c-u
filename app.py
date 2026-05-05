import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

uploaded_file = st.file_uploader("Tải lên file JSON của bạn", type=['json'])

def normalize_keys(data):
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    elif isinstance(data, dict):
        return {str(k).lower(): normalize_keys(v) for k, v in data.items()}
    return data

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        clean_data = normalize_keys(data)
        if isinstance(clean_data, dict): clean_data = [clean_data]
        
        df = pd.json_normalize(clean_data)
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()].drop_duplicates().fillna(0)

        # 1. XỬ LÝ CỘT THỜI GIAN
        time_col = next((col for col in df.columns if 'thời gian' in col.lower() or 'time' in col.lower()), None)
        if time_col:
            df[time_col] = df[time_col].astype(str).str.replace('-', ':', regex=False)
            df[time_col] = df[time_col].apply(lambda x: x.replace(':', '-', 2) if len(x) > 10 else x)
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            df = df.dropna(subset=[time_col])

        # 2. XỬ LÝ CỘT SỐ
        for col in df.columns:
            if col != time_col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. BẢNG DỮ LIỆU (HIỂN THỊ TOÀN BỘ)
        st.subheader("📋 Bảng dữ liệu gốc (Excel Style)")
        st.data_editor(df, use_container_width=True)
        
        st.divider()

        # 4. KHU VỰC VẼ BIỂU ĐỒ (ÁP DỤNG BỘ LỌC)
        st.subheader("📈 Khu vực vẽ biểu đồ (có lọc thời gian)")
        
        if time_col:
            min_date = df[time_col].min().date()
            max_date = df[time_col].max().date()
            start_date, end_date = st.date_input("Chọn khoảng thời gian cho biểu đồ:", value=(min_date, max_date))
            df_filtered = df[(df[time_col].dt.date >= start_date) & (df[time_col].dt.date <= end_date)]
        else:
            df_filtered = df
            st.warning("Không tìm thấy cột thời gian, biểu đồ sẽ hiển thị toàn bộ dữ liệu.")

        numeric_cols = df_filtered.select_dtypes(include=['number']).columns.tolist()
        cols = st.columns(4)
        selected_keys = [key for i, key in enumerate(numeric_cols) if cols[i % 4].checkbox(key.upper(), key=f"chk_{key}")]

        if selected_keys:
            plot_df = df_filtered.set_index(time_col) if time_col else df_filtered
            for col in selected_keys:
                st.write(f"**Biểu đồ: {col.upper()}**")
                st.line_chart(plot_df[col])
                st.write("---")

    except Exception as e:
        st.error(f"Lỗi: {e}")
