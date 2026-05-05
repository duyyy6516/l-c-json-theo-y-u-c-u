import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📂 Trình lọc dữ liệu JSON Thông minh")

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        
        # 1. Chuyển đổi thành DataFrame phẳng
        if isinstance(data, dict):
            data = [data]
        df = pd.json_normalize(data)
        
        # 2. XỬ LÝ CỘT TRÙNG VÀ CỘT RỖNG
        # Loại bỏ các cột không có bất kỳ giá trị nào (giúp xóa các cột None/NaN vô nghĩa)
        df = df.dropna(axis=1, how='all')
        
        # Gộp các cột có tên giống nhau (nếu có trường hợp bị lặp)
        # Cách này lấy giá trị từ cột đầu tiên tìm thấy và bỏ qua các cột trùng lặp phía sau
        df = df.groupby(level=0, axis=1).first()

        # 3. Làm sạch dữ liệu hiển thị
        # Chuyển các giá trị 'None' hoặc 'NaN' về rỗng để bảng nhìn sạch hơn
        df = df.fillna('')
        
        st.success(f"Đã xử lý xong: {len(df)} dòng dữ liệu.")
        
        # 4. Hiển thị bảng tương tác
        st.write("### Dữ liệu sau khi làm sạch:")
        edited_df = st.data_editor(df, use_container_width=True)
        
        # 5. Xuất CSV
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button("Tải về file CSV", csv, "data_cleaned.csv", "text/csv")

    except Exception as e:
        st.error(f"Lỗi cấu trúc file: {e}")
