import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Analyzer", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON & Thời gian")

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        # Chuyển đổi dữ liệu đơn giản
        df = pd.json_normalize(data)
        df = df.dropna(axis=1, how='all').drop_duplicates().fillna(0)
        
        # 1. Tự động tìm cột thời gian (giả sử có chứa chữ "thời gian" hoặc "time")
        time_col = next((col for col in df.columns if 'thời gian' in col.lower() or 'time' in col.lower()), None)
        
        if time_col:
            # Chuyển cột thời gian về định dạng Datetime
            df[time_col] = pd.to_datetime(df[time_col])
            
            # --- BỘ LỌC THỜI GIAN ---
            st.subheader("📅 Lọc khoảng thời gian")
            min_date = df[time_col].min().date()
            max_date = df[time_col].max().date()
            
            start_date, end_date = st.date_input(
                "Chọn khoảng thời gian:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Lọc dữ liệu dựa trên ngày được chọn
            mask = (df[time_col].dt.date >= start_date) & (df[time_col].dt.date <= end_date)
            df_filtered = df.loc[mask]
        else:
            df_filtered = df
            st.warning("Không tìm thấy cột thời gian chuẩn để lọc.")

        # 2. Xử lý các cột số
        for col in df_filtered.columns:
            if col != time_col:
                df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0)

        numeric_cols = df_filtered.select_dtypes(include=['number']).columns.tolist()

        # 3. Chọn biểu đồ
        st.subheader("✅ Chọn chỉ số hiển thị:")
        cols = st.columns(3)
        selected_keys = [key for i, key in enumerate(numeric_cols) if cols[i % 3].checkbox(key.upper())]
        
        # 4. Vẽ biểu đồ theo thời gian
        if selected_keys and time_col:
            st.subheader("📈 Biểu đồ biến động theo thời gian")
            # Thiết lập thời gian làm trục chính (index) để line_chart hiểu
            plot_df = df_filtered.set_index(time_col)
            for col in selected_keys:
                st.write(f"**Biểu đồ: {col.upper()}**")
                st.line_chart(plot_df[col])
                st.write("---")
        elif selected_keys:
            st.warning("Cần cột thời gian để vẽ biểu đồ theo thời gian.")

        with st.expander("📋 Xem dữ liệu sau lọc"):
            st.data_editor(df_filtered, use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi: {e}")
