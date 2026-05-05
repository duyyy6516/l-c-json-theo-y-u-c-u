import streamlit as st
import pandas as pd
import json

# Cấu hình giao diện
st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON & Thời gian")

uploaded_file = st.file_uploader("Tải lên file JSON của bạn", type=['json'])

def normalize_keys(data):
    """Đệ quy chuyển tất cả key về chữ thường để tránh trùng lặp"""
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    elif isinstance(data, dict):
        return {str(k).lower(): normalize_keys(v) for k, v in data.items()}
    return data

if uploaded_file is not None:
    try:
        # 1. Đọc và làm phẳng dữ liệu
        data = json.load(uploaded_file)
        clean_data = normalize_keys(data)
        if isinstance(clean_data, dict): clean_data = [clean_data]
        
        df = pd.json_normalize(clean_data)
        df = df.dropna(axis=1, how='all') # Xóa cột rỗng
        df = df.loc[:, ~df.columns.duplicated()] # Xóa cột trùng tên
        df = df.drop_duplicates()
        df = df.fillna(0)

        # 2. Xử lý cột thời gian (Tự động tìm kiếm cột có từ 'time' hoặc 'thời gian')
        time_col = next((col for col in df.columns if 'thời gian' in col.lower() or 'time' in col.lower()), None)
        
        if time_col:
            # Xử lý định dạng thời gian đặc biệt: "2025-02-18 16-43-37" -> "2025-02-18 16:43:37"
            df[time_col] = df[time_col].astype(str).str.replace('-', ':', regex=False)
            # Sửa lại ký tự giữa ngày và giờ nếu cần (đưa về chuẩn)
            # Giả sử format là YYYY:MM:DD HH:MM:SS, ta khôi phục dấu '-' cho ngày
            df[time_col] = df[time_col].apply(lambda x: x.replace(':', '-', 2) if len(x) > 10 else x)
            
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            df = df.dropna(subset=[time_col]) # Bỏ dòng lỗi thời gian

            # --- Bộ lọc thời gian ---
            st.subheader("📅 Lọc khoảng thời gian")
            min_date = df[time_col].min().date()
            max_date = df[time_col].max().date()
            
            start_date, end_date = st.date_input(
                "Chọn khoảng thời gian:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            df_filtered = df[(df[time_col].dt.date >= start_date) & (df[time_col].dt.date <= end_date)]
        else:
            df_filtered = df
            st.warning("Không tìm thấy cột thời gian chuẩn để lọc.")

        # 3. Chuẩn bị dữ liệu số để vẽ biểu đồ
        for col in df_filtered.columns:
            if col != time_col:
                df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0)

        numeric_cols = df_filtered.select_dtypes(include=['number']).columns.tolist()

        # 4. Giao diện chọn bằng ô vuông
        st.subheader("✅ Chọn các chỉ số để hiển thị biểu đồ:")
        cols = st.columns(4)
        selected_keys = []
        for i, key in enumerate(numeric_cols):
            if cols[i % 4].checkbox(key.upper(), key=f"check_{key}"):
                selected_keys.append(key)
        
        st.divider()

        # 5. Vẽ biểu đồ riêng biệt từng Key
        if selected_keys:
            st.subheader("📈 Biểu đồ biến động")
            plot_df = df_filtered.set_index(time_col) if time_col else df_filtered
            
            for col in selected_keys:
                st.write(f"**Biểu đồ: {col.upper()}**")
                st.line_chart(plot_df[col])
                st.write("---")

        # 6. Bảng dữ liệu tương tác
        with st.expander("📋 Xem toàn bộ bảng dữ liệu chi tiết"):
            st.data_editor(df_filtered, use_container_width=True)
            
        # Nút tải file
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Tải xuống kết quả (.csv)", csv, "data_cleaned.csv", "text/csv")

    except Exception as e:
        st.error(f"Lỗi khi xử lý file: {e}")
