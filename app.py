import streamlit as st
import pandas as pd
import numpy as np
import json

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu Hệ thống")

# 1. Đồng nhất Key (Viết thường để tránh trùng cột)
def normalize_keys(data):
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    elif isinstance(data, dict):
        return {str(k).lower(): normalize_keys(v) for k, v in data.items()}
    return data

# 2. Làm phẳng cấu trúc JSON
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

uploaded_file = st.file_uploader("Tải lên file JSON chứa nhiều bản ghi", type=['json'])

if uploaded_file is not None:
    try:
        raw_data = json.load(uploaded_file)
        # Xử lý trường hợp file là 1 object hoặc 1 danh sách nhiều object
        if isinstance(raw_data, dict): raw_data = [raw_data]
        
        # Bước 1: Chuẩn hóa và làm phẳng toàn bộ danh sách bản ghi
        clean_json = normalize_keys(raw_data)
        df = pd.DataFrame([flatten_json(row) for row in clean_json])
        
        # Dọn dẹp bảng: Bỏ cột rỗng, bỏ trùng, thay ô trống bằng khoảng trắng cho sạch
        df = df.dropna(axis=1, how='all').loc[:, ~df.columns.duplicated()]
        df = df.replace(r'^\s*$', np.nan, regex=True)
        display_df = df.fillna("")

        # HIỂN THỊ BẢNG GỐC (Chứa toàn bộ các bản ghi bạn tải lên)
        st.subheader(f"📋 Danh sách bản ghi gốc ({len(df)} dòng)")
        st.data_editor(display_df, use_container_width=True)
        
        st.divider()

        # THIẾT LẬP BIỂU ĐỒ
        st.subheader("⚙️ Thiết lập biểu đồ tổng hợp")
        
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if time_col:
                # Chuyển đổi cột thời gian chính
                t_dates = pd.to_datetime(df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                valid_ts = t_dates.dropna()
                if not valid_ts.empty:
                    min_d, max_d = valid_ts.min().date(), valid_ts.max().date()
                    sel_date = st.date_input("Lọc theo ngày:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                    start_d, end_d = (sel_date[0], sel_date[1]) if len(sel_date) == 2 else (sel_date[0], sel_date[0])
                else:
                    st.warning("Không tìm thấy ngày hợp lệ")
                    start_d, end_d = None, None
            else:
                st.info("Không có cột thời gian")
                start_d, end_d = None, None

        with col2:
            # Lọc các cột có thể vẽ biểu đồ (bỏ STT, tên khu, ID...)
            exclude = [time_col, 'stt', 'tên khu', 'trạng thái', 'phương thức hoạt động', 'người điều khiển']
            numeric_options = [c for c in df.columns if c not in exclude and '_id' not in c]
            cols_ui = st.columns(4)
            selected_keys = [k for i, k in enumerate(numeric_options) if cols_ui[i % 4].checkbox(k.upper(), key=f"c_{k}")]

        ignore_zero = st.checkbox("🚫 Loại bỏ giá trị 0 (giúp biểu đồ mượt hơn)", value=True)

        # NÚT TẠO BIỂU ĐỒ TỔNG HỢP
        if st.button("🚀 TẠO BIỂU ĐỒ TỔNG HỢP", type="primary"):
            if not selected_keys:
                st.warning("Hãy chọn ít nhất 1 chỉ số!")
            else:
                # Chuẩn bị dữ liệu lọc
                working_df = df.copy()
                if time_col:
                    working_df[time_col] = pd.to_datetime(working_df[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                    working_df = working_df.dropna(subset=[time_col])
                    if start_d and end_d:
                        mask = (working_df[time_col].dt.date >= start_d) & (working_df[time_col].dt.date <= end_d)
                        working_df = working_df[mask]

                for col in selected_keys:
                    st.write(f"### Phân tích: {col.upper()}")
                    
                    all_points = []
                    # Duyệt qua TẤT CẢ các bản ghi (dòng) trong file
                    for idx, row in working_df.iterrows():
                        main_time = row[time_col]
                        val = str(row[col]).strip()
                        
                        if '/' in val:
                            # TRƯỜNG HỢP DỮ LIỆU CON PHỨC TẠP (PH/EC)
                            parts = val.split()
                            for p in parts:
                                if '/' in p:
                                    try:
                                        sub_t_str, sub_v_str = p.split('/', 1)
                                        # Ghép ngày của bản ghi với giờ của dữ liệu con
                                        full_t = pd.to_datetime(f"{main_time.strftime('%Y-%m-%d')} {sub_t_str.replace('-', ':')}")
                                        all_points.append({'Time': full_t, 'Value': float(sub_v_str)})
                                    except: pass
                        else:
                            # TRƯỜNG HỢP SỐ ĐƠN LẺ (Lưu lượng...)
                            try:
                                v = float(val)
                                all_points.append({'Time': main_time, 'Value': v})
                            except: pass

                    if all_points:
                        # Gom tất cả điểm từ tất cả bản ghi vào 1 DataFrame duy nhất
                        chart_df = pd.DataFrame(all_points).sort_values('Time').set_index('Time')
                        series = chart_df['Value']
                        
                        # Lọc bỏ số 0 nếu cần
                        if ignore_zero:
                            series = series.replace(0, np.nan).dropna()
                        
                        st.line_chart(series)
                        st.caption(f"Biểu đồ tổng hợp từ {len(all_points)} điểm dữ liệu.")
                    else:
                        st.info(f"Không có dữ liệu số cho cột {col}")
                    st.write("---")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
