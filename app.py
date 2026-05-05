import streamlit as st
import pandas as pd
import json

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

uploaded_file = st.file_uploader("Tải lên file JSON của bạn", type=['json'])

if uploaded_file is not None:
    try:
        # Load dữ liệu
        data = json.load(uploaded_file)
        if isinstance(data, dict): data = [data]
        
        # Làm phẳng dữ liệu
        df = pd.DataFrame([flatten_json(row) for row in data])
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()].fillna("N/A")

        # 1. BẢNG DỮ LIỆU GỐC (Hiển thị ngay, không lọc)
        st.subheader("📋 Bảng dữ liệu gốc (Excel Style)")
        st.data_editor(df, use_container_width=True)
        
        st.divider()

        # 2. KHU VỰC THIẾT LẬP (Dashboard)
        st.subheader("⚙️ Thiết lập biểu đồ")
        
        # Tự tìm cột thời gian
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("Chọn khoảng thời gian:")
            if time_col:
                # Ép kiểu thời gian tạm thời để lấy min/max cho bộ lọc
                temp_dates = pd.to_datetime(df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                min_date = temp_dates.min().date() if pd.notna(temp_dates.min()) else pd.to_datetime('today').date()
                max_date = temp_dates.max().date() if pd.notna(temp_dates.max()) else pd.to_datetime('today').date()
                start_date, end_date = st.date_input("Chọn:", value=(min_date, max_date))
            else:
                st.info("Không tìm thấy cột thời gian.")

        with col2:
            st.write("Chọn các chỉ số (tích vào ô):")
            # Chỉ chọn các cột có khả năng là số
            numeric_cols = [c for c in df.columns if c != time_col and '_id' not in c]
            cols_check = st.columns(4)
            selected_keys = [key for i, key in enumerate(numeric_cols) if cols_check[i % 4].checkbox(key.upper(), key=f"check_{key}")]

        # 3. NÚT TẠO BIỂU ĐỒ (Chỉ chạy khi bấm nút)
        if st.button("🚀 TẠO BIỂU ĐỒ", type="primary"):
            if not selected_keys:
                st.warning("Vui lòng chọn ít nhất một chỉ số!")
            else:
                plot_df = df.copy()
                
                # Xử lý thời gian cho biểu đồ
                if time_col:
                    plot_df[time_col] = pd.to_datetime(plot_df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                    plot_df = plot_df.dropna(subset=[time_col])
                    # Lọc theo thời gian đã chọn
                    mask = (plot_df[time_col].dt.date >= start_date) & (plot_df[time_col].dt.date <= end_date)
                    plot_df = plot_df[mask]
                    plot_df = plot_df.set_index(time_col)
                
                # Vẽ biểu đồ
                for col in selected_keys:
                    st.write(f"**Biểu đồ: {col.upper()}**")
                    # Chuyển dữ liệu sang số, lỗi thành 0
                    series = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)
                    st.line_chart(series)
                    st.write("---")

    except Exception as e:
        st.error(f"Lỗi xử lý file: {e}")
