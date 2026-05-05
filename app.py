import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")
st.title("📊 Debugger Dữ liệu JSON")

uploaded_file = st.file_uploader("Tải file JSON", type=['json'])

if uploaded_file is not None:
    try:
        raw_data = json.load(uploaded_file)
        
        # Nếu data là 1 dict, biến thành list
        if isinstance(raw_data, dict):
            raw_data = [raw_data]
            
        # Dùng json_normalize mạnh mẽ nhất của Pandas
        # Nó tự xử lý lồng nhau (nested) mà không cần hàm tự viết
        df = pd.json_normalize(raw_data)
        
        # DEBUG: Hiển thị tên cột để bạn biết tại sao nó không hiện
        st.write("Các cột được tìm thấy:", df.columns.tolist())
        
        # Làm sạch: xóa cột trống, xử lý None
        df = df.fillna("N/A")
        
        st.subheader("Bảng dữ liệu sau khi Load:")
        st.dataframe(df, use_container_width=True)
