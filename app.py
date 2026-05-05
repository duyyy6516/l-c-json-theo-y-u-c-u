import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Lọc & Vẽ biểu đồ Từng cột")

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

def normalize_keys(data):
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    elif isinstance(data, dict):
        return {k.lower(): normalize_keys(v) for k, v in data.items()}
    return data

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        clean_data = normalize_keys(data)
        
        if isinstance(clean_data, dict):
            clean_data = [clean_data]
            
        df = pd.json_normalize(clean_data)
        df = df.dropna(axis=1, how='all')
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.drop_duplicates()
        df = df.fillna(0)

        # Chuyển kiểu dữ liệu sang số để vẽ
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass

        # Lọc các cột số
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        st.subheader("📈 Vẽ biểu đồ cho từng cột")
        selected_cols = st.multiselect("Chọn các cột muốn vẽ:", numeric_cols)
        
        # Vẽ biểu đồ tách biệt cho từng cột
        for col in selected_cols:
            st.write(f"### Biểu đồ: {col.upper()}")
            st.line_chart(df[col])
            st.divider() # Tạo đường kẻ phân cách giữa các biểu đồ

        # Hiển thị bảng dữ liệu
        st.subheader("📋 Bảng dữ liệu chi tiết")
        st.data_editor(df, use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi: {e}")
