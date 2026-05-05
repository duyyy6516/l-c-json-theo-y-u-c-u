import streamlit as st
import pandas as pd
import json
import re

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

# 1. Đồng nhất Key
def normalize_keys(data):
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    elif isinstance(data, dict):
        return {str(k).lower(): normalize_keys(v) for k, v in data.items()}
    return data

# 2. Làm phẳng JSON sâu (Flatten)
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

# 3. Trích xuất số từ chuỗi phức tạp (VD: 20-10-28/6.9)
def extract_complex_numbers(val):
    if pd.isna(val) or val == "N/A" or val == "":
        return None
    val_str = str(val).strip()
    if '/' in val_str:
        matches = re.findall(r'/([0-9.]+)', val_str)
        if matches:
            numbers = [float(m) for m in matches]
            return sum(numbers) / len(numbers)
    return val

uploaded_file = st.file_uploader("Tải lên file JSON của bạn", type=['json'])

if uploaded_file is not None:
    try:
        raw_data = json.load(uploaded_file)
        if isinstance(raw_data, dict): raw_data = [raw_data]
        
        # Bước 1: Đồng nhất và làm phẳng
        clean_json = normalize_keys(raw_data)
        df = pd.DataFrame([flatten_json(row) for row in clean_json])
        
        # Bước 2: Làm sạch cột, điền N/A cho bảng dữ liệu gốc
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()]
        display_df = df.fillna("N/A")

        # HIỂN THỊ BẢNG GỐC
        st.subheader("📋 Bảng dữ liệu gốc")
        st.data_editor(display_df, use_container_width=True)
        
        st.divider()

        # THIẾT LẬP BIỂU ĐỒ
        st.subheader("⚙️ Thiết lập & Vẽ biểu đồ")
        
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if time_col:
                t_dates = pd.to_datetime(df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                valid_ts = t_dates.dropna()
                if not valid_ts.empty:
                    min_d, max_d = valid_ts.min().date(), valid_ts.max().date()
                    sel_date = st.date_input("Khoảng thời gian:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                    if len(sel_date) == 2: start_d, end_d = sel_date
                    else: start_d, end_d = sel_date[0], sel_date[0]
                else:
                    st.warning("Thời gian không hợp lệ")
                    start_d, end_d = None, None
            else:
                st.info("Không có cột thời gian")
                start_d, end_d = None, None

        with col2:
            numeric_options = [c for c in df.columns if c != time_col and '_id' not in c]
            cols_ui = st.columns(4)
            selected_keys = [k for i, k in enumerate(numeric_options) if cols_ui[i % 4].checkbox(k.upper(), key=f"c_{k}")]

        # NÚT TẠO BIỂU ĐỒ
        if st.button("🚀 TẠO BIỂU ĐỒ", type="primary"):
            if not selected_keys:
                st.warning("Hãy chọn ít nhất 1 chỉ số!")
            else:
                plot_df = df.copy()
                
                if time_col and start_d and end_d:
                    plot_df[time_col] = pd.to_datetime(plot_df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                    plot_df = plot_df.dropna(subset=[time_col])
                    mask = (plot_df[time_col].dt.date >= start_d) & (plot_df[time_col].dt.date <= end_d)
                    plot_df = plot_df[mask].set_index(time_col)

                for col in selected_keys:
                    st.write(f"**Biểu đồ: {col.upper()}**")
                    
                    clean_data = plot_df[col].apply(extract_complex_numbers)
                    
                    # QUAN TRỌNG: KHÔNG DÙNG fillna(0) NỮA
                    # Biến N/A thành giá trị rỗng (NaN)
                    chart_series = pd.to_numeric(clean_data, errors='coerce')
                    
                    # XÓA BỎ CÁC ĐIỂM RỖNG ĐỂ BIỂU ĐỒ KHÔNG RỚT XUỐNG 0
                    chart_series = chart_series.dropna()
                    
                    # Kiểm tra xem sau khi lọc N/A, cột đó có còn dữ liệu nào không
                    if chart_series.empty:
                        st.info(f"Cột {col} chỉ chứa toàn 'N/A' hoặc lỗi, không có số để vẽ.")
                    else:
                        st.line_chart(chart_series)
                    st.write("---")

    except Exception as e:
        st.error(f"Lỗi: {e}")
