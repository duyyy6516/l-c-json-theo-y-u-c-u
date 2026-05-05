import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide") # Mở rộng giao diện ra full màn hình
st.title("Web lọc & Sắp xếp dữ liệu JSON")

# 1. Widget tải file lên
uploaded_file = st.file_uploader("Chọn file JSON của bạn", type=['json'])

if uploaded_file is not None:
    # Đọc dữ liệu từ file được tải lên
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        st.success("File đã tải lên thành công!")

        # 2. Hiển thị bảng có khả năng lọc và sắp xếp
        # st.data_editor cho phép người dùng chỉnh sửa trực tiếp trên giao diện
        # st.dataframe (bản mới) hỗ trợ mặc định việc bấm vào tiêu đề cột để sắp xếp
        st.write("### Dữ liệu của bạn:")
        st.info("💡 Mẹo: Bấm vào tiêu đề cột để sắp xếp tăng/giảm dần.")
        
        # Sử dụng data_editor để người dùng có thể lọc/tìm kiếm trong trình duyệt
        edited_df = st.data_editor(df, use_container_width=True)
        
        # 3. Tính năng xuất file sau khi đã lọc/chỉnh sửa (giống Excel)
        st.download_button(
            label="Tải về file CSV đã chỉnh sửa",
            data=edited_df.to_csv(index=False).encode('utf-8'),
            file_name='data_processed.csv',
            mime='text/csv',
        )
        
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
else:
    st.warning("Vui lòng tải lên một file JSON để bắt đầu.")
