import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Cleaner", layout="wide")
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
        # Loại bỏ các cột trống hoàn toàn
        df = df.dropna(axis=1, how='all')
        
        # XỬ LÝ CỘT TRÙNG TÊN: 
        # Chúng ta sẽ giữ lại các cột có dữ liệu và loại bỏ các cột trùng tên nhưng rỗng
        # Cách này thay thế cho lệnh groupby bị lỗi
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Loại bỏ các hàng trùng lặp hoàn toàn
        df = df.drop_duplicates()
        
        # 3. Làm sạch dữ liệu hiển thị (chuyển NaN thành trống)
        df = df.fillna('')
        
        st.success(f"Đã xử lý xong: {len(df)} dòng dữ liệu.")
        
        # 4. Hiển thị bảng
        st.write("### Dữ liệu sau khi làm sạch:")
        edited_df = st.data_editor(df, use_container_width=True)
        
        # 5. Xuất CSV
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button("Tải về file CSV", csv, "data_cleaned.csv", "text/csv")

    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}")
