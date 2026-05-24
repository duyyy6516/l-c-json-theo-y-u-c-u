import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

# Import các module từ Git của bạn
from calculations import calculate_vpd, get_weather_by_time
from services import send_telegram_message, get_quick_solution
from analytics import analyze_day_by_blocks_rt, predict_vpd_trend_v3
from charts import draw_temperature_chart, draw_humidity_chart, draw_vpd_chart, draw_combined_chart

# Cấu hình trang
st.set_page_config(page_title="VPD Farm Analytics", page_icon="🌿", layout="wide")

# CSS tối ưu không gian
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# 1. KHỞI TẠO TABS CHÍNH
tab_realtime, tab_upload = st.tabs(["🔮 THEO DÕI & DỰ BÁO TƯƠNG LAI", "📁 PHÂN TÍCH FILE DỮ LIỆU CỦA BẠN"])

# =========================================================================
# 🔮 TAB 1: THEO DÕI & DỰ BÁO (Logic cũ của bạn)
# =========================================================================
with tab_realtime:
    # (Tại đây dán toàn bộ logic cũ đã chia 2 cột của bạn vào)
    # Để code gọn hơn, tôi tóm tắt lại cấu trúc:
    left_col, right_col = st.columns([3.5, 6.5])
    
    # Logic xử lý Session State (giữ nguyên các biến cũ)
    if 'temp' not in st.session_state: st.session_state.temp = 0.0
    if 'rh' not in st.session_state: st.session_state.rh = 0.0
    if 'history' not in st.session_state: st.session_state.history = []
    # ... (Các biến session state khác của bạn)

    with left_col:
        st.markdown("<h3 style='color: #2E7D32;'>🤖 TRẠM ĐIỀU HÀNH THÔNG MINH</h3>", unsafe_allow_html=True)
        # Nút bấm, Slider cấu hình cây trồng, Thông số Realtime...
        # (Copy toàn bộ nội dung with left_col từ bản cũ của bạn vào đây)

    with right_col:
        st.markdown("<h3 style='color: #2E7D32;'>📊 TRUNG TÂM PHÂN TÍCH CHU KỲ</h3>", unsafe_allow_html=True)
        # Tabs biểu đồ, bảng phân tích buổi...
        # (Copy toàn bộ nội dung with right_col từ bản cũ của bạn vào đây)

# =========================================================================
# 📁 TAB 2: PHÂN TÍCH FILE DỮ LIỆU (Chức năng mới)
# =========================================================================
with tab_upload:
    st.markdown("<h3 style='color: #1A5276;'>📁 TẢI LÊN FILE NHẬT KÝ NHÀ KÍNH</h3>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Chọn file dữ liệu (Hỗ trợ .csv hoặc .xlsx):", type=["csv", "xlsx"])
    
    if uploaded_file:
        # Đọc dữ liệu
        try:
            if uploaded_file.name.endswith('.csv'):
                df_user = pd.read_csv(uploaded_file)
            else:
                df_user = pd.read_excel(uploaded_file)
            
            st.success(f"Đã tải file '{uploaded_file.name}' thành công! Vui lòng kiểm tra các cột.")
            
            # Chọn cột tương ứng (để app linh hoạt với mọi loại file)
            col_list = df_user.columns.tolist()
            c1, c2, c3, c4 = st.columns(4)
            with c1: t_col = st.selectbox("Cột Nhiệt độ (°C):", col_list)
            with c2: h_col = st.selectbox("Cột Độ ẩm (%):", col_list)
            with c3: time_col = st.selectbox("Cột Thời gian:", col_list)
            with c4: date_col = st.selectbox("Cột Ngày (nếu có):", ["Tự động"] + col_list)

            # Xử lý tính toán VPD hàng loạt
            df_user['VPD (kPa)'] = df_user.apply(lambda row: calculate_vpd(row[t_col], row[h_col]), axis=1)
            df_user['Hiển thị Giờ'] = pd.to_datetime(df_user[time_col]).dt.strftime('%H:%M')
            
            if date_col == "Tự động":
                df_user['Ngày'] = "Dữ liệu tải lên"
            else:
                df_user['Ngày'] = df_user[date_col]

            # Hiển thị kết quả phân tích
            st.divider()
            an1, an2 = st.columns([7, 3])
            
            with an1:
                st.markdown("#### 📈 Biểu đồ xu hướng từ File")
                # Tận dụng các hàm vẽ biểu đồ từ charts.py
                st.altair_chart(draw_vpd_chart(df_user, 0.6, 1.2), use_container_width=True)
            
            with an2:
                st.markdown("#### 📋 Thống kê nhanh")
                st.write(df_user[[time_col, t_col, h_col, 'VPD (kPa)']].head(10))
                st.download_button("Tải xuống kết quả phân tích (.csv)", df_user.to_csv(index=False), "vpd_analysis.csv", "text/csv")

        except Exception as e:
            st.error(f"Lỗi khi xử lý file: {e}")
    else:
        st.info("💡 Mẹo: File của bạn nên có các cột về Nhiệt độ, Độ ẩm và Thời gian để hệ thống phân tích chính xác nhất.")
