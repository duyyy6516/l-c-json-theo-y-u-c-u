import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

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

        # CÁCH LÀM AN TOÀN: Thay vì dùng errors='ignore', ta dùng to_numeric đơn giản
        # Nếu cột nào không thể chuyển thành số, ta để nguyên hoặc điền 0
        numeric_cols = []
        for col in df.columns:
            # Chuyển sang kiểu số, nếu lỗi thì chuyển thành NaN, sau đó thay bằng 0
            converted = pd.to_numeric(df[col], errors='coerce')
            if not converted.isna().all(): # Nếu cột này có chứa ít nhất một số
                df[col] = converted.fillna(0)
                numeric_cols.append(col)

        # --- GIAO DIỆN CHỌN BẰNG Ô VUÔNG ---
        st.subheader("✅ Chọn các chỉ số cần hiển thị biểu đồ:")
        cols = st.columns(3)
        selected_keys = []
        
        for i, key in enumerate(numeric_cols):
            if cols[i % 3].checkbox(key.upper(), key=f"check_{key}"):
                selected_keys.append(key)
        
        st.divider()

        # --- VẼ BIỂU ĐỒ TỪNG KEY ---
        if selected_keys:
            st.subheader("📈 Biểu đồ chi tiết")
            for col in selected_keys:
                st.write(f"**Biểu đồ: {col.upper()}**")
                st.line_chart(df[col])
                st.write("---")

        # --- BẢNG DỮ LIỆU ---
        with st.expander("📋 Xem toàn bộ bảng dữ liệu"):
            st.data_editor(df, use_container_width=True)

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi đọc file: {e}")
