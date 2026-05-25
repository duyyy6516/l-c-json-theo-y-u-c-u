import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

# Import các module nội bộ từ kho hệ thống (Hợp nhất chính xác tất cả các hàm đang được gọi)
from calculations import calculate_vpd, get_weather_by_time
from services import send_telegram_message, get_quick_solution
from analytics import (
    analyze_day_by_blocks_rt, 
    predict_vpd_trend_v3, 
    calculate_plant_stress_hours,
    analyze_day_by_blocks_dynamic, 
    predict_vpd_trend_dynamic, 
    calculate_static_plant_stress, 
    get_biological_block
)
from charts import draw_temperature_chart, draw_humidity_chart, draw_vpd_chart, draw_combined_chart

TELE_TOKEN = "8917951413:AAE6LKUEfYEYiQrFWGoKsQn0tumZc_XbcHg"
TELE_CHAT_ID = "7290661009"

# Cấu hình giao diện trang duy nhất ở đầu file
st.set_page_config(page_title="VPD Hybrid Farm Analytics", page_icon="🌿", layout="wide")

# CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP CAO (CSS)
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        scroll-behavior: smooth;
    }
    .block-container { padding-top: 1.5rem; padding-bottom: 4rem; padding-left: 1.5rem; padding-right: 1.5rem; }
    h3 { margin-top: 0.2rem; margin-bottom: 0.8rem; padding-top: 0.2rem; }
    div[st-delegate="element-container"] { margin-bottom: 0.3rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 45px; font-weight: bold; font-size: 16px; }
    .danger-box-red { padding: 12px; background-color: #FFEBEE; border-left: 6px solid #FF1744; color: #B71C1C; font-weight: bold; font-size: 15px; border-radius: 4px; margin-bottom: 8px; }
    .danger-box-blue { padding: 12px; background-color: #E3F2FD; border-left: 6px solid #2979FF; color: #0D47A1; font-weight: bold; font-size: 15px; border-radius: 4px; margin-bottom: 8px; }
    .upload-header { font-size: 16px; font-weight: bold; color: #1A5276; border-bottom: 2px solid #D4E6F1; padding-bottom: 5px; margin-bottom: 12px; }
    .metric-card-upload { background-color: #F4F6F7; border: 1px solid #E5E7E9; padding: 10px; border-radius: 6px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo bộ nhớ tạm Session State (Hợp nhất đầy đủ các biến)
if 'temp' not in st.session_state: st.session_state.temp = 0.0
if 'rh' not in st.session_state: st.session_state.rh = 0.0
if 'countdown' not in st.session_state: st.session_state.countdown = 15 
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'is_completed' not in st.session_state: st.session_state.is_completed = False 
if 'history' not in st.session_state: st.session_state.history = []
if 'stt_counter' not in st.session_state: st.session_state.stt_counter = 0 
if 'plant_idx' not in st.session_state: st.session_state.plant_idx = 0
if 'vpd_range_val' not in st.session_state: st.session_state.vpd_range_val = (0.6, 1.1)
if 'simulated_time' not in st.session_state: st.session_state.simulated_time = "2026-05-24 07:00:00"

if 'file_plant_idx' not in st.session_state: st.session_state.file_plant_idx = 0
if 'file_vpd_range_val' not in st.session_state: st.session_state.file_vpd_range_val = (0.6, 1.1)

# CẤU HÌNH CÁC LOẠI CÂY TRỒNG ĐÀ LẠT PHỔ BIẾN
DANH_SACH_CAY = {
    "🍓 Dâu tây Đà Lạt (Hoa / Trái)": (0.6, 1.1),
    "🍓 Dâu tây Đà Lạt (Giai đoạn ngó/cây con)": (0.4, 0.8),
    "🌹 Hoa hồng nhà kính (Đà Lạt)": (0.8, 1.3),
    "🌼 Hoa cúc / Hoa đồng tiền": (0.7, 1.2),
    "🍅 Cà chua bi / 🫑 Ớt chuông Sweet Palermo": (0.8, 1.4),
    "🥦 Súp lơ xanh / Bắp cabbage baby (Rau ăn lá)": (0.5, 1.0),
    "🥬 Xà lách Thủy canh (Lô lô, Romaine)": (0.4, 0.9),
    "🌱 Cây giống trong vườn ươm (Cần ẩm cao)": (0.3, 0.7),
    "🛠️ Tùy chỉnh thủ công ngưỡng riêng": (0.8, 1.2)
}
plant_list_keys = list(DANH_SACH_CAY.keys())

# MA TRẬN ĐỘNG THEO CHU KỲ BUỔI SINH HỌC
DANH_SACH_MA_TRAN_CAY = {
    "🍓 Dâu tây Đà Lạt (Hoa / Trái)": {
        "🌅 Sáng (05h - 10h)": (0.6, 1.0), "☀️ Trưa (10h - 15h)": (0.8, 1.2), "🌇 Chiều (15h - 19h)": (0.6, 1.0), "🌌 Tối (19h - 23h)": (0.4, 0.8), "🌙 Khuya (23h - 05h)": (0.3, 0.6)
    },
    "🌹 Hoa hồng nhà kính (Đà Lạt)": {
        "🌅 Sáng (05h - 10h)": (0.7, 1.1), "☀️ Trưa (10h - 15h)": (0.9, 1.4), "🌇 Chiều (15h - 19h)": (0.8, 1.2), "🌌 Tối (19h - 23h)": (0.5, 0.9), "🌙 Khuya (23h - 05h)": (0.4, 0.7)
    },
    "🍅 Cà chua bi / 🫑 Ớt chuông Palermo": {
        "🌅 Sáng (05h - 10h)": (0.7, 1.2), "☀️ Trưa (10h - 15h)": (0.9, 1.5), "🌇 Chiều (15h - 19h)": (0.8, 1.3), "🌌 Tối (19h - 23h)": (0.5, 0.9), "🌙 Khuya (23h - 05h)": (0.4, 0.8)
    },
    "🛠️ Tùy chỉnh thủ công ma trận riêng": {
        "🌅 Sáng (05h - 10h)": (0.6, 1.0), "☀️ Trưa (10h - 15h)": (0.8, 1.2), "🌇 Chiều (15h - 19h)": (0.6, 1.0), "🌌 Tối (19h - 23h)": (0.4, 0.8), "🌙 Khuya (23h - 05h)": (0.3, 0.6)
    }
}
plant_keys = list(DANH_SACH_MA_TRAN_CAY.keys())

if 'current_matrix' not in st.session_state: 
    st.session_state.current_matrix = DANH_SACH_MA_TRAN_CAY[plant_keys[0]].copy()

# Hàm tạo màu nền cho các dòng trạng thái (Chỉ khai báo 1 lần duy nhất)
def style_status_rows(row):
    styles = [''] * len(row)
    status = str(row['Trạng thái'])
    if "Lý tưởng" in status:
        styles[row.index.get_loc('Trạng thái')] = 'background-color: #E8F5E9; color: #1B5E20; font-weight: bold; border-radius: 4px;'
    elif "Quá khô" in status:
        styles[row.index.get_loc('Trạng thái')] = 'background-color: #FFEBEE; color: #B71C1C; font-weight: bold; border-radius: 4px;'
    elif "Quá ẩm" in status:
        styles[row.index.get_loc('Trạng thái')] = 'background-color: #E3F2FD; color: #0D47A1; font-weight: bold; border-radius: 4px;'
    return styles

def setup_next_day():
    current_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
    next_day_dt = current_dt + timedelta(hours=7) if current_dt.hour == 0 and current_dt.minute == 0 else current_dt + timedelta(days=1)
    if not (current_dt.hour == 0 and current_dt.minute == 0):
        next_day_dt = next_day_dt.replace(hour=7, minute=0, second=0)
    st.session_state.simulated_time = next_day_dt.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.is_completed = False
    st.session_state.countdown = 15

def trigger_new_data(vpd_min, vpd_max):
    current_sim_datetime = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
    current_date_str = current_sim_datetime.strftime("Ngày %d/%m")
    st.session_state.temp, st.session_state.rh = get_weather_by_time(current_sim_datetime)
    st.session_state.countdown = 15 
    st.session_state.stt_counter += 1
    new_vpd = calculate_vpd(st.session_state.temp, st.session_state.rh)
    
    status_text = "⚠️ Quá ẩm" if new_vpd < vpd_min else ("✅ Lý tưởng" if new_vpd <= vpd_max else "🚨 Quá khô")
    tele_status = "🟦 QUÁ ẨM" if new_vpd < vpd_min else ("🟩 LÝ TƯỞNG" if new_vpd <= vpd_max else "🟥 QUÁ KHÔ")
    
    st.session_state.history.insert(0, {
        "STT": st.session_state.stt_counter, "Ngày": current_date_str,
        "Thời gian mô phỏng": current_sim_datetime, "Hiển thị Giờ": current_sim_datetime.strftime("%H:%M"),
        "datetime_internal": current_sim_datetime,
        "Nhiệt độ (°C)": st.session_state.temp, "Độ ẩm (%)": st.session_state.rh,
        "VPD (kPa)": round(new_vpd, 2), "Trạng thái": status_text
    })
    
    if TELE_TOKEN and TELE_CHAT_ID:
        sol = get_quick_solution(new_vpd, vpd_min, vpd_max, current_sim_datetime.hour)
        unique_days = sorted(list(set([r["Ngày"] for r in st.session_state.history])), reverse=True)
        history_of_latest_day = [r for r in st.session_state.history if r["Ngày"] == (unique_days[0] if unique_days else current_date_str)]
        trend, trend_type = predict_vpd_trend_v3(history_of_latest_day, current_sim_datetime.hour, vpd_min, vpd_max)
        
        prefix = "🚨 [CẢNH BÁO SỚM] " if "CẢNH BÁO SỚM" in trend else ""
        telegram_msg = (
            f"🌿 *HỆ THỐNG VPD ĐÀ LẠT REALTIME*\n⏰ {current_date_str} - {current_sim_datetime.strftime('%H:%M')}\n"
            f"📊 Môi trường: {st.session_state.temp}°C | {st.session_state.rh}%\n\n"
            f"*1️⃣ Hiện trạng:* *{new_vpd:.2f} kPa* — {tele_status}\n"
            f"*2️⃣ Biện pháp:* _{sol}_\n"
            f"*3️⃣ Dự báo:* {prefix}_{trend}_"
        )
        send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, telegram_msg)
    
    next_sim_datetime = current_sim_datetime + timedelta(minutes=10)
    if next_sim_datetime.hour == 0 and next_sim_datetime.minute == 0:
        st.session_state.is_running = False     
        st.session_state.is_completed = True   
    st.session_state.simulated_time = next_sim_datetime.strftime("%Y-%m-%d %H:%M:%S")

def trigger_next_manual_point():
    current_sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
    st.session_state.temp, st.session_state.rh = get_weather_by_time(current_sim_dt)
    st.session_state.stt_counter += 1
    
    new_vpd = calculate_vpd(st.session_state.temp, st.session_state.rh)
    block_name = get_biological_block(current_sim_dt.hour)
    vpd_min, vpd_max = st.session_state.current_matrix[block_name]
    
    status_text = "⚠️ Quá ẩm" if new_vpd < vpd_min else ("✅ Lý tưởng" if new_vpd <= vpd_max else "🚨 Quá khô")
    tele_status = "🟦 QUÁ ẨM" if new_vpd < vpd_min else ("🟩 LÝ TƯỞNG" if new_vpd <= vpd_max else "🟥 QUÁ KHÔ")
    
    st.session_state.history.insert(0, {
        "STT": st.session_state.stt_counter, "Ngày": current_sim_dt.strftime("Ngày %d/%m"),
        "Thời gian mô phỏng": current_sim_dt, "Hiển thị Giờ": current_sim_dt.strftime("%H:%M"), # Sửa lỗi chính tả biến từ file gốc
        "datetime_internal": current_sim_dt, "Nhiệt độ (°C)": st.session_state.temp, "Độ ẩm (%)": st.session_state.rh,
        "VPD (kPa)": round(new_vpd, 2), "Trạng thái": status_text
    })
    
    if TELE_TOKEN and TELE_CHAT_ID:
        sol = get_quick_solution(new_vpd, vpd_min, vpd_max, current_sim_dt.hour)
        unique_days = sorted(list(set([r["Ngày"] for r in st.session_state.history])), reverse=True)
        hist_latest = [r for r in st.session_state.history if r["Ngày"] == (unique_days[0] if unique_days else current_sim_dt.strftime("Ngày %d/%m"))]
        trend, trend_type = predict_vpd_trend_dynamic(hist_latest, current_sim_dt.hour, st.session_state.current_matrix)
        
        telegram_msg = (
            f"🌿 *HỆ THỐNG VPD ĐỘNG ĐÀ LẠT*\n⏰ Buổi: {block_name} | Giờ: {current_sim_dt.strftime('%H:%M')}\n"
            f"📊 Môi trường: {st.session_state.temp}°C | {st.session_state.rh}%\n"
            f"🎯 Mục tiêu dải: {vpd_min}-{vpd_max} kPa\n\n"
            f"*1️⃣ Hiện trạng:* *{new_vpd:.2f} kPa* — {tele_status}\n"
            f"*2️⃣ Biện pháp:* _{sol}_\n"
            f"*3️⃣ Dự báo chu kỳ:* _{trend}_"
        )
        send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, telegram_msg)
        
    next_dt = current_sim_dt + timedelta(minutes=10)
    if next_dt.hour == 0 and next_dt.minute == 0:
        st.session_state.is_completed = True
    st.session_state.simulated_time = next_dt.strftime("%Y-%m-%d %H:%M:%S")

# Chia ứng dụng làm 2 Tab chức năng lớn
tab_future, tab_past = st.tabs(["🔮 XEM DỰ BÁO & THEO DÕI TƯƠNG LAI", "📁 TẢI FILE & PHÂN TÍCH LỊCH SỬ"])

# --------------------------------------------------------
# TAB 1: MA TRẬN ĐỘNG THEO BUỔI & GIÁM SÁT REALTIME
# --------------------------------------------------------
with tab_future:
    left_col, right_col = st.columns([3.8, 6.2])
    with left_col:
        st.markdown("<h3 style='color: #2E7D32; font-size: 18px;'>🤖 TRẠM ĐIỀU HÀNH THÔNG MINH</h3>", unsafe_allow_html=True)
        with st.container(border=True):
            if st.session_state.is_completed:
                st.success("🏁 Đã hoàn thành chu kỳ ngày mô phỏng!")
                if st.button("🔄 Khởi động lại ngày mới", type="primary", use_container_width=True):
                    st.session_state.simulated_time = "2026-05-24 07:00:00"
                    st.session_state.is_completed = False
                    st.rerun()
            else:
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("▶️ Bắt đầu Chạy Tự Động", type="primary", use_container_width=True, disabled=st.session_state.is_running):
                        if st.session_state.is_completed: setup_next_day()
                        st.session_state.is_running = True
                        if st.session_state.stt_counter == 0: 
                            trigger_new_data(st.session_state.vpd_range_val[0], st.session_state.vpd_range_val[1])
                        st.rerun()
                with col_btn2:
                    if st.button("⏸️ Tạm dừng", type="secondary", use_container_width=True, disabled=not st.session_state.is_running):
                        st.session_state.is_running = False
                        st.rerun()
                
                if st.button("⏭️ Cập nhật thủ công (Thêm 10 phút)", type="secondary", use_container_width=True, disabled=st.session_state.is_running):
                    trigger_next_manual_point()
                    st.rerun()

        with st.container(border=True):
            st.markdown("**1. Chọn mô hình cây trồng áp dụng:**")
            p_opt = st.selectbox("Cây trồng:", plant_keys, index=st.session_state.plant_idx, label_visibility="collapsed")
            st.session_state.plant_idx = plant_keys.index(p_opt)
            
            if p_opt != "🛠️ Tùy chỉnh thủ công ma trận riêng":
                st.session_state.current_matrix = DANH_SACH_MA_TRAN_CAY[p_opt].copy()
            
            st.markdown("**2. Cấu hình chi tiết dải VPD từng buổi (kPa):**")
            for block, (vmin, vmax) in st.session_state.current_matrix.items():
                nv = st.slider(f"{block}:", 0.0, 3.0, (vmin, vmax), step=0.1, key=f"sl_{block}", disabled=(p_opt != "🛠️ Tùy chỉnh thủ công ma trận riêng"))
                st.session_state.current_matrix[block] = nv

        run_interval = 1 if st.session_state.is_running else 999999

        @st.fragment(run_every=run_interval)
        def left_panel_monitor_dynamic():
            curr_sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
            curr_block = get_biological_block(curr_sim_dt.hour)
            b_min, b_max = st.session_state.current_matrix[curr_block]

            if st.session_state.is_running:
                st.session_state.countdown -= 1
                if st.session_state.countdown < 0: 
                    trigger_new_data(b_min, b_max)
                    st.rerun()
                    
            if st.session_state.is_running: st.caption(f"⏳ Đổi số tự động sau: **{st.session_state.countdown}s**")
            
            with st.container(border=True):
                st.markdown(f"⏰ **Mốc mô phỏng:** {curr_sim_dt.strftime('%H:%M')} ({curr_block})")
                col1, col2 = st.columns(2)
                with col1: st.metric(label="🌡️ Nhiệt độ", value=f"{st.session_state.temp}°C" if st.session_state.stt_counter > 0 else "--°C")
                with col2: st.metric(label="💧 Độ ẩm", value=f"{st.session_state.rh}%" if st.session_state.stt_counter > 0 else "--%")

            if st.session_state.stt_counter > 0:
                vpd_now = calculate_vpd(st.session_state.temp, st.session_state.rh)
                trend, trend_type = predict_vpd_trend_dynamic([r for r in st.session_state.history], curr_sim_dt.hour, st.session_state.current_matrix)
                if trend_type == "danger_red": st.markdown(f"<div class='danger-box-red'>🚨 {trend}</div>", unsafe_allow_html=True)
                elif trend_type == "danger_blue": st.markdown(f"<div class='danger-box-blue'>🚨 {trend}</div>", unsafe_allow_html=True)
                
                text_color = "#0068C9" if vpd_now < b_min else ("#2E7D32" if vpd_now <= b_max else "#FF4B4B")
                st.markdown(f"**VPD Hiện Tại:** <span style='color:{text_color}; font-weight:bold; font-size:17px;'>{vpd_now:.2f} kPa</span> (Mục tiêu: {b_min}-{b_max})", unsafe_allow_html=True)
                st.markdown(f"**Giải pháp khuyến nghị:** _{get_quick_solution(vpd_now, b_min, b_max, curr_sim_dt.hour)}_")

        left_panel_monitor_dynamic()

    with right_col:
        st.markdown("<h3 style='color: #2E7D32; font-size: 18px;'>📊 TRUNG TÂM PHÂN TÍCH MA TRẬN CHU KỲ</h3>", unsafe_allow_html=True)
        if not st.session_state.history:
            st.info("Chưa có số liệu. Vui lòng bấm kích hoạt trạm điều hành bên trái để hiển thị biểu đồ.")
        else:
            u_days = sorted(list(set([r["Ngày"] for r in st.session_state.history])), reverse=True)
            f1, f2 = st.columns([7, 3])
            with f1: s_day = st.selectbox("Lọc ngày:", u_days, label_visibility="collapsed")
            with f2:
                if st.button("🗑️ Reset Trạm Realtime", use_container_width=True):
                    st.session_state.stt_counter = 0; st.session_state.history = []; st.session_state.simulated_time = "2026-05-24 07:00:00"
                    st.session_state.is_completed = False; st.session_state.is_running = False; st.session_state.temp = 0.0; st.session_state.rh = 0.0
                    st.rerun()

            df_all = pd.DataFrame(st.session_state.history)
            df_fil = df_all[df_all["Ngày"] == s_day].iloc[::-1].copy()

            curr_sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
            curr_block = get_biological_block(curr_sim_dt.hour)
            b_min, b_max = st.session_state.current_matrix[curr_block]

            m_t1, m_t2, m_t3 = st.tabs(["📈 Biểu đồ trực quan", "📊 Đối chiếu Ma Trận Buổi", "📋 Nhật ký chi tiết"])
            with m_t1: 
                sub_tab_g1, sub_tab_g2 = st.tabs(["🎯 Chỉ số VPD", "📊 Tổ hợp chỉ số"])
                with sub_tab_g1: st.altair_chart(draw_vpd_chart(df_fil, b_min, b_max), use_container_width=True)
                with sub_tab_g2: st.altair_chart(draw_combined_chart(df_fil), use_container_width=True)
            with m_t2: 
                st.dataframe(analyze_day_by_blocks_dynamic(st.session_state.history, st.session_state.current_matrix, s_day), use_container_width=True, hide_index=True)
            with m_t3:
                styled_df = df_fil[["STT", "Hiển thị Giờ", "Nhiệt độ (°C)", "Độ ẩm (%)", "VPD (kPa)", "Trạng thái"]].style.apply(style_status_rows, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --------------------------------------------------------
# 📁 TAB 2: PHÂN TÍCH FILE IOT THEO DẢI CỐ ĐỊNH PHIÊN BẢN GỐC
# --------------------------------------------------------
with tab_past:
    st.markdown("<h3 style='color: #1A5276; font-size: 19px;'>📁 PHÂN TÍCH CHUYÊN SÂU FILE IOT NHÀ KÍNH</h3>", unsafe_allow_html=True)
    tl, tr = st.columns([5, 5])
    with tl:
        with st.container(border=True):
            st.markdown("<div class='upload-header'>⚙️ Cấu hình dải VPD mục tiêu áp dụng cho File:</div>", unsafe_allow_html=True)
            f_vpd_range = st.slider("Dải lý tưởng cố định (kPa):", 0.0, 3.0, (0.6, 1.2), step=0.1, key="file_static_range")
    with tr:
        with st.container(border=True):
            st.markdown("<div class='upload-header'>📥 Tải tệp dữ liệu đầu vào:</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Chọn file IoT (JSON, CSV, Excel):", type=["json", "csv", "xlsx"], label_visibility="collapsed")
            t_filter_opt = st.selectbox("Chế độ xử lý chu kỳ dữ liệu:", ["📊 Xem toàn bộ dữ liệu gốc của File", "📆 Tự chọn một ngày cụ thể trên lịch"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.json'):
                raw_data = json.load(uploaded_file)
                if isinstance(raw_data, dict):
                    df_up = pd.DataFrame([raw_data]) if not isinstance(list(raw_data.values())[0], (dict, list)) else pd.DataFrame(raw_data)
                else:
                    df_up = pd.DataFrame(raw_data)
            elif uploaded_file.name.endswith('.csv'): 
                df_up = pd.read_csv(uploaded_file)
            else: 
                df_up = pd.read_excel(uploaded_file)
            
            c_t, c_h, c_time = None, None, None
            for c in df_up.columns:
                cl = str(c).lower().strip()
                if 'temp' in cl or 'nhiet' in cl: c_t = c
                if 'humi' in cl or 'rh' in cl or 'do am' in cl: c_h = c
                if any(k in cl for k in ['time', 'thời gian', 'date', 'timestamp', 'ngày']): c_time = c

            if not c_t: c_t = df_up.columns[0]
            if not c_h: c_h = df_up.columns[1]
            if not c_time: c_time = df_up.columns[2]

            df_calc = pd.DataFrame()
            df_calc["datetime_internal"] = pd.to_datetime(df_up[c_time].astype(str).str.strip(), errors='coerce')
            df_calc["Nhiệt độ (°C)"] = pd.to_numeric(df_up[c_t], errors='coerce')
            df_calc["Độ ẩm (%)"] = pd.to_numeric(df_up[c_h], errors='coerce')
            
            df_calc = df_calc.dropna().sort_values("datetime_internal").copy()
            
            if df_calc.empty:
                st.error("❌ Không trích xuất được dữ liệu hợp lệ từ File. Vui lòng kiểm tra lại định dạng tệp.")
                st.stop()
                
            df_calc["VPD (kPa)"] = df_calc.apply(lambda r: calculate_vpd(r["Nhiệt độ (°C)"], r["Độ ẩm (%)"]), axis=1)
            df_calc["only_date"] = df_calc["datetime_internal"].dt.date

            if "Tự chọn một ngày cụ thể" in t_filter_opt:
                av_dates = sorted(df_calc["only_date"].unique())
                s_date = st.date_input("Chọn ngày trên lịch cụ thể:", value=av_dates[-1] if av_dates else datetime.now().date())
                df_calc = df_calc[df_calc["only_date"] == s_date].copy()

            if df_calc.empty:
                st.warning("⚠️ Không tìm thấy dữ liệu nào trùng khớp với ngày đã chọn trên lịch.")
            else:
                df_calc["Hiển thị Giờ"] = df_calc["datetime_internal"].dt.strftime("%H:%M")
                df_calc["Trạng thái"] = df_calc.apply(lambda r: "⚠️ Quá ẩm" if r["VPD (kPa)"] < f_vpd_range[0] else ("✅ Lý tưởng" if r["VPD (kPa)"] <= f_vpd_range[1] else "🚨 Quá khô"), axis=1)

                st.markdown("<div style='font-weight:bold; color:#1A5276; margin-top:15px;'>📊 TỔNG QUAN CHU KỲ KHAI THÁC TỪ FILE</div>", unsafe_allow_html=True)
                k1, k2, k3, k4 = st.columns(4)
                with k1: st.markdown(f"<div class='metric-card-upload'><span style='font-size:12px;color:grey;'>📈 VPD TRUNG BÌNH</span><br><b style='font-size:18px;color:#2E7D32;'>{df_calc['VPD (kPa)'].mean():.2f} kPa</b></div>", unsafe_allow_html=True)
                with k2: st.markdown(f"<div class='metric-card-upload'><span style='font-size:12px;color:grey;'>🌡️ NHIỆT ĐỘ TRUNG BÌNH</span><br><b style='font-size:18px;color:#FF4B4B;'>{df_calc['Nhiệt độ (°C)'].mean():.1f} °C</b></div>", unsafe_allow_html=True)
                with k3: st.markdown(f"<div class='metric-card-upload'><span style='font-size:12px;color:grey;'>💧 ĐỘ ẨM TRUNG BÌNH</span><br><b style='font-size:18px;color:#0068C9;'>{df_calc['Độ ẩm (%)'].mean():.1f} %</b></div>", unsafe_allow_html=True)
                with k4: st.markdown(f"<div class='metric-card-upload'><span style='font-size:12px;color:grey;'>📋 TỔNG SỐ ĐIỂM SỐ GHI</span><br><b style='font-size:18px;color:#5D6D7E;'>{len(df_calc)} điểm</b></div>", unsafe_allow_html=True)

                # Tính toán Stress Nông học bản cũ ổn định
                stress = calculate_static_plant_stress(df_calc, f_vpd_range[0], f_vpd_range[1], t_filter_opt)
                st.error(f"⚠️ **Đánh giá Agronomy:** Tích lũy Stress Khô: `{stress['dry_hours']} giờ` | Tích lũy Stress Ẩm: `{stress['wet_hours']} giờ` | Nguy cơ bùng phát nấm bệnh tại vườn: `{stress['fungus_risk']}%`")

                m_v1, m_v2, m_v3 = st.tabs(["📉 Biểu đồ tích hợp VPD", "🌡️ Biểu đồ Nhiệt độ / Độ ẩm rời", "📋 Bảng dữ liệu trích xuất"])
                with m_v1:
                    st.altair_chart(draw_vpd_chart(df_calc, f_vpd_range[0], f_vpd_range[1]), use_container_width=True)
                with m_v2:
                    st.altair_chart(draw_temperature_chart(df_calc), use_container_width=True)
                    st.altair_chart(draw_humidity_chart(df_calc), use_container_width=True)
                with m_v3:
                    st.dataframe(df_calc[["Hiển thị Giờ", "Nhiệt độ (°C)", "Độ ẩm (%)", "VPD (kPa)", "Trạng thái"]].style.apply(style_status_rows, axis=1), use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"❌ Lỗi cấu trúc file tải lên hoặc định dạng cột: {str(e)}")
