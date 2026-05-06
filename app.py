import streamlit as st
import pandas as pd
import numpy as np
import json

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

uploaded_file = st.file_uploader("Tải lên file JSON của bạn", type=['json'])

if uploaded_file is not None:
    try:
        raw_data = json.load(uploaded_file)
        if isinstance(raw_data, dict): raw_data = [raw_data]
        
        clean_json = normalize_keys(raw_data)
        df = pd.DataFrame([flatten_json(row) for row in clean_json])
        
        # Dọn dẹp bảng
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()]
        df = df.replace(r'^\s*$', np.nan, regex=True)
        display_df = df.fillna("")

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

        ignore_zero = st.checkbox("🚫 Bỏ qua các giá trị 0 trên biểu đồ (coi như thiết bị lỗi / mất kết nối)", value=True)

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
                    
                    # KIỂM TRA: Cột này là số thường hay chuỗi phức tạp chứa "/"?
                    is_complex = plot_df[col].astype(str).str.contains('/').any()
                    
                    if is_complex:
                        # Bóc tách từng mốc thời gian chi tiết
                        detailed_data = []
                        for main_time, row in plot_df.iterrows():
                            val = str(row[col]).strip()
                            if val and val.lower() != "nan":
                                # Tách các cụm "20-10-28/6.9"
                                pairs = val.split()
                                for p in pairs:
                                    if '/' in p:
                                        try:
                                            # Tách thời gian và giá trị
                                            t_str, v_str = p.split('/', 1)
                                            # Lấy "Ngày" từ main_time ghép với "Giờ:Phút:Giây" từ chuỗi
                                            date_part = main_time.strftime('%Y-%m-%d')
                                            exact_time_str = f"{date_part} {t_str.replace('-', ':')}"
                                            
                                            exact_time = pd.to_datetime(exact_time_str)
                                            detailed_data.append({'Time': exact_time, 'Value': float(v_str)})
                                        except:
                                            pass
                        
                        if detailed_data:
                            # Tạo DataFrame mới từ các điểm chi tiết này
                            chart_df = pd.DataFrame(detailed_data).set_index('Time')
                            chart_df = chart_df.sort_index() # Sắp xếp thời gian theo thứ tự chuẩn
                            chart_series = chart_df['Value']
                        else:
                            chart_series = pd.Series(dtype=float)
                    else:
                        # Nếu là số bình thường (như Lưu lượng m2/h)
                        chart_series = pd.to_numeric(plot_df[col], errors='coerce')
                    
                    # Lọc N/A và số 0
                    if ignore_zero:
                        chart_series = chart_series.replace(0, np.nan)
                    chart_series = chart_series.dropna()
                    
                    if chart_series.empty:
                        st.info(f"Cột {col} trống hoặc không có dữ liệu hợp lệ để vẽ.")
                    else:
                        st.line_chart(chart_series)
                    st.write("---")

    except Exception as e:
        st.error(f"Lỗi: {e}")
