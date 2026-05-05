import streamlit as st
import pandas as pd
import json

# Cấu hình giao diện
st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

# Hàm làm phẳng JSON (Xử lý mọi cấp độ lồng nhau và ký tự tiếng Việt)
def flatten_json(y):
    out = {}
    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x: flatten(x[a], name + a + '.')
        elif isinstance(x, list):
            i = 0
            for a in x:
                flatten(a, name + str(i) + '.')
                i += 1
        else: out[name[:-1]] = x
    flatten(y)
    return out

uploaded_file = st.file_uploader("Tải lên file JSON của bạn", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        
        # Đảm bảo dữ liệu luôn là một danh sách để xử lý đồng nhất
        if isinstance(data, dict):
            data = [data]
        
        # Làm phẳng dữ liệu và tạo DataFrame
        df = pd.DataFrame([flatten_json(row) for row in data])
        
        # Làm sạch cột: loại bỏ cột toàn rỗng và các cột trùng tên
        df = df.dropna(axis=1, how='all')
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Thay thế dữ liệu rỗng bằng "N/A" để bảng hiển thị rõ ràng
        df = df.fillna("N/A")
        df = df.replace(r'^\s*$', "N/A", regex=True)

        # 1. Tự động nhận diện cột thời gian
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        if time_col:
            # Xử lý định dạng thời gian của bạn: "2024-08-26 20-06-26"
            df[time_col] = df[time_col].astype(str).str.replace('-', ':', regex=False)
            df[time_col] = df[time_col].apply(lambda x: x.replace(':', '-', 2) if len(x) > 10 else x)
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            df = df.dropna(subset=[time_col])

        # 2. Chuyển cột sang số để vẽ biểu đồ (lấy ra các cột không phải thời gian)
        numeric_cols = []
        for col in df.columns:
            if col != time_col:
                # Chuyển kiểu, giá trị lỗi thành 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                numeric_cols.append(col)

        # 3. BẢNG DỮ LIỆU GỐC (Hiển thị toàn bộ, không bị ảnh hưởng bởi bộ lọc)
        st.subheader("📋 Bảng dữ liệu gốc (Hiển thị tất cả)")
        st.data_editor(df, use_container_width=True)
        
        st.divider()

        # 4. KHU VỰC ĐIỀU KHIỂN & BIỂU ĐỒ (Áp dụng bộ lọc thời gian)
        st.subheader("⚙️ Thiết lập & Vẽ biểu đồ")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if time_col:
                st.write("Khoảng thời gian:")
                min_date = df[time_col].min().date()
                max_date = df[time_col].max().date()
                start_date, end_date = st.date_input("Chọn:", value=(min_date, max_date))
            else:
                st.info("Không tìm thấy cột thời gian.")

        with col2:
            st.write("Chọn các chỉ số để tạo biểu đồ:")
            cols_check = st.columns(4)
            selected_keys = [key for i, key in enumerate(numeric_cols) if cols_check[i % 4].checkbox(key.upper(), key=f"check_{key}")]

        # 5. NÚT TẠO BIỂU ĐỒ
        if st.button("🚀 TẠO BIỂU ĐỒ", type="primary"):
            if not selected_keys:
                st.warning("Vui lòng chọn ít nhất một chỉ số!")
            else:
                # Lọc dữ liệu theo thời gian
                if time_col:
                    mask = (df[time_col].dt.date >= start_date) & (df[time_col].dt.date <= end_date)
                    df_filtered = df[mask]
                else:
                    df_filtered = df
                
                # Vẽ biểu đồ
                plot_df = df_filtered.set_index(time_col) if time_col else df_filtered
                
                for col in selected_keys:
                    st.write(f"**Biểu đồ: {col.upper()}**")
                    st.line_chart(plot_df[col])

    except Exception as e:
        st.error(f"Lỗi cấu trúc file: {e}")
