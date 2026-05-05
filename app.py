import streamlit as st
import pandas as pd
import json
import re  # Thư viện dùng để trích xuất số từ chuỗi phức tạp

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

# Hàm làm phẳng mọi cấu trúc JSON lồng nhau
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

# Hàm xử lý các chuỗi đo đạc lồng nhau (vd: "20-10-28/6.9 ...")
def extract_complex_numbers(val):
    if pd.isna(val) or val == "N/A":
        return val
    val_str = str(val).strip()
    if '/' in val_str:
        # Tìm tất cả các số đứng ngay sau dấu '/'
        matches = re.findall(r'/([0-9.]+)', val_str)
        if matches:
            # Tính trung bình cộng của các lần đo trong ô đó
            numbers = [float(m) for m in matches]
            return sum(numbers) / len(numbers)
    return val

uploaded_file = st.file_uploader("Tải lên file JSON của bạn", type=['json'])

if uploaded_file is not None:
    try:
        # Load dữ liệu
        data = json.load(uploaded_file)
        if isinstance(data, dict): data = [data]
        
        # Làm phẳng dữ liệu
        df = pd.DataFrame([flatten_json(row) for row in data])
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()].fillna("N/A")

        # 1. BẢNG DỮ LIỆU GỐC
        st.subheader("📋 Bảng dữ liệu gốc")
        st.data_editor(df, use_container_width=True)
        
        st.divider()

        # 2. KHU VỰC THIẾT LẬP
        st.subheader("⚙️ Thiết lập biểu đồ")
        
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("Chọn khoảng thời gian:")
            if time_col:
                temp_dates = pd.to_datetime(df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                valid_dates = temp_dates.dropna()
                
                if not valid_dates.empty:
                    min_date = valid_dates.min().date()
                    max_date = valid_dates.max().date()
                    
                    date_selection = st.date_input(
                        "Chọn (Khóa trong khoảng dữ liệu thật):", 
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    if len(date_selection) == 2:
                        start_date, end_date = date_selection
                    else:
                        start_date, end_date = date_selection[0], date_selection[0]
                else:
                    st.warning("Không có dữ liệu thời gian hợp lệ.")
                    start_date, end_date = None, None
            else:
                st.info("Không tìm thấy cột thời gian.")
                start_date, end_date = None, None

        with col2:
            st.write("Chọn các chỉ số:")
            numeric_cols = [c for c in df.columns if c != time_col and '_id' not in c]
            cols_check = st.columns(4)
            selected_keys = [key for i, key in enumerate(numeric_cols) if cols_check[i % 4].checkbox(key.upper(), key=f"check_{key}")]

        # 3. NÚT TẠO BIỂU ĐỒ
        if st.button("🚀 TẠO BIỂU ĐỒ", type="primary"):
            if not selected_keys:
                st.warning("Vui lòng chọn ít nhất một chỉ số!")
            else:
                plot_df = df.copy()
                
                if time_col and start_date and end_date:
                    plot_df[time_col] = pd.to_datetime(plot_df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                    plot_df = plot_df.dropna(subset=[time_col])
                    
                    mask = (plot_df[time_col].dt.date >= start_date) & (plot_df[time_col].dt.date <= end_date)
                    plot_df = plot_df[mask]
                    plot_df = plot_df.set_index(time_col)
                
                # Vẽ biểu đồ
                for col in selected_keys:
                    st.write(f"**Biểu đồ: {col.upper()}**")
                    
                    # BƯỚC XỬ LÝ MỚI: Trích xuất số từ chuỗi có dấu '/'
                    clean_series = plot_df[col].apply(extract_complex_numbers)
                    
                    # Chuyển dữ liệu sang số, lỗi thành 0
                    series = pd.to_numeric(clean_series, errors='coerce').fillna(0)
                    st.line_chart(series)
                    st.write("---")

    except Exception as e:
        st.error(f"Lỗi xử lý file: {e}")
