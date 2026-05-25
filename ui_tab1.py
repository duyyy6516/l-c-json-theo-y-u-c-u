# ui_tab1.py
import streamlit as st
from datetime import datetime
from config import VPD_THRESHOLDS_SMART

def get_smart_threshold(hour):
    for period, cfg in VPD_THRESHOLDS_SMART.items():
        if cfg["start"] <= cfg["end"]:
            if cfg["start"] <= hour < cfg["end"]: return cfg["min"], cfg["max"], period
        else: # Khuya
            if hour >= cfg["start"] or hour < cfg["end"]: return cfg["min"], cfg["max"], period
    return 0.6, 1.1, "Mặc định"

def render_tab1():
    st.markdown("### 🤖 TRẠM ĐIỀU HÀNH THÔNG MINH")
    mode = st.radio("Chọn chế độ:", ["Trạm thông minh (Tự động theo giờ)", "Cấu hình thủ công (Tag 2)"])
    
    if mode == "Trạm thông minh (Tự động theo giờ)":
        st.info("Hệ thống sẽ tự động áp dụng ngưỡng dựa trên thời gian thực.")
        current_hour = datetime.now().hour
        min_v, max_v, period = get_smart_threshold(current_hour)
        st.write(f"Đang áp dụng khung giờ: **{period}** (Ngưỡng: {min_v} - {max_v} kPa)")
    else:
        vpd_range = st.slider("Thiết lập ngưỡng thủ công (kPa):", 0.0, 3.0, (0.6, 1.1))
        st.write(f"Đang dùng ngưỡng thủ công: {vpd_range[0]} - {vpd_range[1]} kPa")
    
    if st.button("Chạy mô phỏng"):
        st.success("Đang bắt đầu chạy quy trình theo thiết lập trên...")
