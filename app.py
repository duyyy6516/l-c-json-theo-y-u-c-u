import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Universal JSON Viewer", layout="wide")
st.title("📂 Trình xem dữ liệu JSON đa năng")

# 1. Widget tải file
uploaded_file = st.file_uploader("Tải lên bất kỳ file JSON nào", type=['json'])

if uploaded_file is not None:
    try:
        # Load dữ liệu
        data = json.load(uploaded_file)
        
        # 2. XỬ LÝ DỮ LIỆU ĐỘNG:
        # Nếu file là dict đơn, biến thành list. Nếu list thì giữ nguyên.
        if isinstance(data, dict):
            data = [data]
            
        # Dùng json_normalize để làm phẳng mọi cấu trúc lồng nhau tự động
        df = pd.json_normalize(data)
        
        # 3. LOẠI BỎ LỖI DỮ LIỆU:
        # Loại bỏ các cột trống hoàn toàn (đôi khi JSON có các key rỗng)
        df = df.dropna(axis=1, how='all')
        
        # Xóa các dòng trùng lặp (tránh hiện tượng lặp bản ghi)
        df = df.drop_duplicates()
        
        # 4. GIAO DIỆN XỬ LÝ NHƯ EXCEL
        st.success(f"Đã tải thành công: {len(df)} dòng, {len(df.columns)} cột.")
        
        # Dùng data_editor để người dùng tự lọc/sắp xếp
        st.subheader("Bảng dữ liệu")
        edited_df = st.data_editor(df, use_container_width=True)
        
        # 5. Xuất dữ liệu
        st.download_button(
            label="Xuất ra CSV",
            data=edited_df.to_csv(index=False).encode('utf-8'),
            file_name='data_exported.csv',
            mime='text/csv',
        )
        
    except Exception as e:
        st.error(f"File này có định dạng lạ, không thể đọc được: {e}")
        st.write("Vui lòng kiểm tra xem file có phải là định dạng JSON hợp lệ không.")
