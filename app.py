import streamlit as st
import pandas as pd
import numpy as np
import json
import re

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích JSON ")

# 1. Đồng nhất Key (Viết thường và xóa khoảng trắng thừa)
def normalize_keys(data):
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    elif isinstance(data, dict):
        return {str(k).strip().lower(): normalize_keys(v) for k, v in data.items()}
    return data

# 2. Làm phẳng JSON (Flatten)
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

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

if uploaded_file is not None:
    try:
        raw_data = json.load(uploaded_file)
        if isinstance(raw_data, dict): raw_data = [raw_data]
        
        clean_json = normalize_keys(raw_data)
        df = pd.DataFrame([flatten_json(row) for row in clean_json])
        
        # Làm sạch cột
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()]
        df = df.replace(r'^\s*$', np.nan, regex=True)
        display_df = df.fillna("")

        # --- BẢNG DỮ LIỆU TỔNG ---
        st.subheader(f"📋 Bảng dữ liệu gốc ({len(df)} bản ghi)")
        st.data_editor(display_df, use_container_width=True)
        
        st.divider()

        # --- THIẾT LẬP ---
        st.subheader("⚙️ Thiết lập biểu đồ & Bảng đối chiếu")
        
        start_d, end_d = None, None
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if time_col:
                t_dates = pd.to_datetime(df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                valid_ts = t_dates.dropna()
                if not valid_ts.empty:
                    min_d, max_d = valid_ts.min().date(), valid_ts.max().date()
                    sel_date = st.date_input("Lọc theo ngày:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                    start_d, end_d = (sel_date[0], sel_date[1]) if len(sel_date) == 2 else (sel_date[0], sel_date[0])
                else:
                    st.warning("Không tìm thấy ngày hợp lệ")
            else:
                st.info("Không có cột thời gian")
                
            resample_choice = st.selectbox(
                "Độ chi tiết dữ liệu (Làm mượt):",
                ["Từng giây (Nguyên bản)", "Trung bình mỗi phút", "Trung bình mỗi 5 phút", "Trung bình mỗi 10 phút"]
            )
            resample_dict = {
                "Từng giây (Nguyên bản)": None,
                "Trung bình mỗi phút": "1min",
                "Trung bình mỗi 5 phút": "5min",
                "Trung bình mỗi 10 phút": "10min"
            }

        with col2:
            exclude = [time_col, 'stt', 'tên khu', 'trạng thái', 'phương thức hoạt động', 'người điều khiển']
            numeric_options = [c for c in df.columns if c not in exclude and '_id' not in c]
            st.write("Chọn các chỉ số muốn kiểm tra:")
            cols_ui = st.columns(4)
            selected_keys = [k for i, k in enumerate(numeric_options) if cols_ui[i % 4].checkbox(k.upper(), key=f"c_{k}")]

        # --- NÚT TẠO ---
        if st.button("🚀 TẠO BIỂU ĐỒ & BẢNG ĐỐI CHIẾU", type="primary"):
            if not selected_keys:
                st.warning("Hãy chọn ít nhất 1 chỉ số!")
            else:
                working_df = df.copy()
                if time_col and start_d and end_d:
                    working_df[time_col] = pd.to_datetime(working_df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                    working_df = working_df.dropna(subset=[time_col])
                    mask = (working_df[time_col].dt.date >= start_d) & (working_df[time_col].dt.date <= end_d)
                    working_df = working_df[mask]

                for col in selected_keys:
                    st.write(f"## Chỉ số: {col.upper()}")
                    
                    all_points = []
                    for idx, row in working_df.iterrows():
                        main_time = row[time_col]
                        val = str(row[col]).strip()
                        
                        if val and val.lower() != 'nan':
                            # Xử lý dữ liệu con (PH/EC/AS)
                            matches = re.findall(r'(\d{2}-\d{2}-\d{2})/([-+]?\d*\.?\d+)', val)
                            if matches:
                                for t_str, v_str in matches:
                                    try:
                                        full_t_str = f"{main_time.strftime('%Y-%m-%d')} {t_str.replace('-', ':')}"
                                        all_points.append({'Thời gian': pd.to_datetime(full_t_str), 'Giá trị': float(v_str)})
                                    except: pass
                            else:
                                # Dữ liệu số đơn giản
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match:
                                    try:
                                        all_points.append({'Thời gian': main_time, 'Giá trị': float(num_match.group())})
                                    except: pass

                    if all_points:
                        # Gom dữ liệu thành Series
                        chart_df = pd.DataFrame(all_points)
                        series = chart_df.groupby('Thời gian')['Giá trị'].mean().sort_index()
                        series = series.dropna()
                        
                        # Làm mượt (Resample)
                        rule = resample_dict[resample_choice]
                        if rule and not series.empty:
                            series = series.resample(rule).mean().dropna()

                        if not series.empty:
                            # 1. Vẽ biểu đồc
                            st.write("📈 **Biểu đồ xu hướng:**")
                            st.line_chart(series)
                            
                            # 2. Tạo bảng Excel để check giá trị
                            st.write("📂 **Bảng đối hiếu giá trị (Excel Style):**")
                            # Chuyển Series thành DataFrame để hiển thị đẹp hơn
                            check_df = series.reset_index()
                            check_df.columns = ['Mốc Thời Gian', f'Giá Trị {col.upper()}']
                            st.dataframe(check_df, use_container_width=True)
                            
                            st.success(f"Đã hiển thị {len(check_df)} điểm dữ liệu để đối chiếu.")
                        else:
                            st.warning(f"Cột {col} không có dữ liệu số sau khi lọc.")
                    else:
                        st.error(f"❌ Không tìm thấy dữ liệu cho {col}.")
                    st.write("---")

    except Exception as e:
        st.error(f"Lỗi: {e}")
