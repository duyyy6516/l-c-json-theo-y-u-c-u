import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Cleaner", layout="wide")
st.title("📂 Trình lọc dữ liệu JSON Thông minh")

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

def normalize_keys(data):
    """Đệ quy chuyển tất cả các key trong dictionary về chữ thường"""
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    elif isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            # Chuyển key về chữ thường để tránh trùng lặp do viết hoa/thường
            new_key = key.lower() 
            new_dict[new_key] = normalize_keys(value)
        return new_dict
    else:
        return data

if uploaded_file is not None:
    try:
        # Load dữ liệu
        raw_data = json.load(uploaded_file)
        
        # 1. CHUẨN HÓA: Chuyển tất cả key về chữ thường trước khi tạo bảng
        clean_data = normalize_keys(raw_data)
        
        # 2. Tạo DataFrame
        if isinstance(clean_data, dict):
            clean_data = [clean_data]
        df = pd.json_normalize(clean_data)
        
        # 3. Làm sạch các cột rỗng và trùng lặp
        df = df.dropna(axis=1, how='all')
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.drop_duplicates()
        df = df.fillna('')
        
        st.success(f"Dữ liệu đã được chuẩn hóa. Hiện có {len(df.columns)} cột.")
        
        # 4. Hiển thị bảng
        edited_df = st.data_editor(df, use_container_width=True)
        
        # 5. Xuất CSV
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button("Tải về file CSV", csv, "data_cleaned.csv", "text/csv")

    except Exception as e:
        st.error(f"Lỗi: {e}")
