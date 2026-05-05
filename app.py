import streamlit as st
import pandas as pd
import json

# Cấu hình trang
st.set_page_config(page_title="JSON Data Viewer", layout="wide")

st.title("📊 Công cụ Lọc & Sắp xếp dữ liệu JSON")
st.markdown("Tải lên file JSON của bạn để xem, lọc và sắp xếp dữ liệu như Excel.")

# 1. Widget tải file
uploaded_file = st.file_uploader("Kéo thả hoặc chọn file JSON tại đây", type=['json'])

if uploaded_file is not None:
    try:
        # Đọc file
        raw_data = json.load(uploaded_file)
        
        # CHUẨN HÓA DỮ LIỆU: Xử lý cấu trúc lồng nhau
        # Nếu data là một dict đơn, chuyển thành list để normalize
        if isinstance(raw_data, dict):
            raw_data = [raw_data]
        
        # Làm phẳng dữ liệu JSON (giải quyết vấn đề các key bị lặp hoặc lồng nhau)
        df = pd.json_normalize(raw_data)
        
        # Loại bỏ các hàng trùng lặp hoàn toàn
        df = df.drop_duplicates()
        
        st.success(f"Đã tải thành công {len(df)} dòng dữ liệu!")
        
        # 2. Hiển thị dữ liệu (Data Editor hỗ trợ sắp xếp và chỉnh sửa)
        st.subheader("Bảng dữ liệu")
        st.info("💡 Mẹo: Nhấp vào tiêu đề cột để sắp xếp, hoặc dùng ô tìm kiếm để lọc dữ liệu.")
        
        # Sử dụng data_editor để người dùng thao tác như Excel
        edited_df = st.data_editor(df, use_container_width=True)
        
        # 3. Tính năng xuất dữ liệu đã lọc/chỉnh sửa
        st.divider()
        st.subheader("Xuất dữ liệu")
        csv = edited_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="Tải về file CSV",
            data=csv,
            file_name='processed_data.csv',
            mime='text/csv',
        )
        
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý file: {e}")
        st.write("Vui lòng kiểm tra định dạng file JSON của bạn.")
else:
    st.warning("Vui lòng tải file lên để bắt đầu.")
