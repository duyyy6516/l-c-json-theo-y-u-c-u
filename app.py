import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime, timedelta

from calculations import calculate_vpd, get_weather_by_time
from services import send_telegram_message, get_quick_solution
from analytics import (
    analyze_day_by_blocks_dynamic, 
    predict_vpd_trend_dynamic, 
    calculate_dynamic_plant_stress, 
    calculate_dew_point, 
    get_biological_block
)
from charts import draw_temperature_chart, draw_humidity_chart, draw_vpd_chart, draw_combined_chart

TELE_TOKEN = "8917951413:AAE6LKUEfYEYiQrFWGoKsQn0tumZc_XbcHg"
TELE_CHAT_ID = "7290661009"

st.set_page_config(page_title="VPD Smart Farm Matrix", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { overflow-y: auto !important; scroll-behavior: smooth; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; padding-left: 1.5rem; padding-right: 1.5rem; }
    .danger-box-red { padding: 12px; background-color: #FFEBEE; border-left: 6px solid #FF1744; color: #B71C1C; font-weight: bold; border-radius: 4px; margin-bottom: 8px; }
    .danger-box-blue { padding: 12px; background-color: #E3F2FD; border-left: 6px solid #2979FF; color: #0D47A1; font-weight: bold; border-radius: 4px; margin-bottom: 8px; }
    .upload-header { font-size: 15px; font-weight: bold; color: #1A5276; border-bottom: 2px solid #D4E6F1; padding-bottom: 4px; margin-bottom: 10px; }
    .metric-card-upload { background-color: #F4F6F7; border: 1px solid #E5E7E9; padding: 10px; border-radius: 6px; text-align: center; }
    .matrix-title { font-size: 13px; font-weight: bold; color: #2E7D32; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session State
if 'temp' not in st.session_state: st.session_state.temp = 0.0
if 'rh' not in st.session_state: st.session_state.rh = 0.0
if 'countdown' not in st.session_state: st.session_state.countdown = 15 
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'is_completed' not in st.session_state: st.session_state.is_completed = False 
if 'history' not in st.session_state: st.session_state.history = []
if 'stt_counter' not in st.session_state: st.session_state.stt_counter = 0 
if 'simulated_time' not in st.session_state: st.session_state.simulated_time = "2026-05-24 07:00:00"
if 'automation_webhook' not in st.session_state: st.session_state.automation_webhook = ""

# MA TRẬN VPD ĐỘNG CHUẨN SINH HỌC 24H CHO CÁC LOẠI CÂY ĐÀ LẠT
MA_TRAN_MAC_DINH = {
    "🍓 Dâu tây Đà Lạt (Trái)": {
        "🌅 Sáng (05h - 10h)": (0.5, 0.9), "☀️ Trưa (10h - 15h)": (0.7, 1.2), 
        "🌇 Chiều (15h - 19h)": (0.6, 1.0), "🌌 Tối (19h - 23h)": (0.4, 0.8), "🌙 Khuya (23h - 05h)": (0.3, 0.7)
    },
    "🌹 Hoa hồng nhà kính": {
        "🌅 Sáng (05h - 10h)": (0.6, 1.0), "☀️ Trưa (10h - 15h)": (0.8, 1.4), 
        "🌇 Chiều (15h - 19h)": (0.7, 1.2), "🌌 Tối (19h - 23h)": (0.5, 0.9), "🌙 Khuya (23h - 05h)": (0.4, 0.8)
    },
    "🍅 Cà chua bi / Ớt chuông": {
        "🌅 Sáng (05h - 10h)": (0.6, 1.1), "☀️ Trưa (10h - 15h)": (0.8, 1.5), 
        "🌇 Chiều (15h - 19h)": (0.7, 1.3), "🌌 Tối (19h - 23h)": (0.5, 1.0), "🌙 Khuya (23h - 05h)": (0.4, 0.8)
    },
    "🛠️ Tùy chỉnh thủ công ma trận": {
        "🌅 Sáng (05h - 10h)": (0.5, 1.0), "☀️ Trưa (10h - 15h)": (0.8, 1.2), 
        "🌇 Chiều (15h - 19h)": (0.6, 1.1), "🌌 Tối (19h - 23h)": (0.4, 0.9), "🌙 Khuya (23h - 05h)": (0.3, 0.8)
    }
}

def style_status_rows(row):
    styles = [''] * len(row)
    status = str(row['Trạng thái'])
    if "Lý tưởng" in status: styles[row.index.get_loc('Trạng thái')] = 'background-color: #E8F5E9; color: #1B5E20; font-weight: bold;'
    elif "Quá khô" in status: styles[row.index.get_loc('Trạng thái')] = 'background-color: #FFEBEE; color: #B71C1C; font-weight: bold;'
    elif "Quá ẩm" in status: styles[row.index.get_loc('Trạng thái')] = 'background-color: #E3F2FD; color: #0D47A1; font-weight: bold;'
    return styles

def trigger_new_data_dynamic(matrix_config):
    current_sim_datetime = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
    current_date_str = current_sim_datetime.strftime("Ngày %d/%m")
    st.session_state.temp, st.session_state.rh = get_weather_by_time(current_sim_datetime)
    st.session_state.countdown = 15 
    st.session_state.stt_counter += 1
    new_vpd = calculate_vpd(st.session_state.temp, st.session_state.rh)
    
    # Lấy ngưỡng của ĐÚNG buổi hiện tại để so sánh
    current_buoi = get_biological_block(current_sim_datetime.hour)
    v_min, v_max = matrix_config[current_buoi]
    
    status_text = "⚠️ Quá ẩm" if new_vpd < v_min else ("✅ Lý tưởng" if new_vpd <= v_max else "🚨 Quá khô")
    
    st.session_state.history.insert(0, {
        "STT": st.session_state.stt_counter, "Ngày": current_date_str,
        "Thời gian mô phỏng": current_sim_datetime, "Hiển thị Giờ": current_sim_datetime.strftime("%H:%M"),
        "datetime_internal": current_sim_datetime, "Nhiệt độ (°C)": st.session_state.temp, "Độ ẩm (%)": st.session_state.rh,
        "VPD (kPa)": round(new_vpd, 2), "Trạng thái": f"{status_text} (Ngưỡng buổi: {v_min}-{v_max})"
    })
    
    # Gửi tín hiệu tự động điều khiển Edge
    if st.session_state.automation_webhook:
        try: requests.post(st.session_state.automation_webhook, json={"vpd": new_vpd, "buoi": current_buoi, "status": status_text}, timeout=2)
        except: pass

    if TELE_TOKEN and TELE_CHAT_ID:
        unique_days = sorted(list(set([r["Ngày"] for r in st.session_state.history])), reverse=True)
        h_latest = [r for r in st.session_state.history if r["Ngày"] == (unique_days[0] if unique_days else current_date_str)]
        trend, _ = predict_vpd_trend_dynamic(h_latest, current_sim_datetime.hour, matrix_config)
        
        msg = (f"🌿 *VPD ĐỘNG THEO BUỔI*\n⏰ {current_date_str} - {current_sim_datetime.strftime('%H:%M')} ({current_buoi})\n"
               f"📊 {st.session_state.temp}°C | {st.session_state.rh}%\n"
               f"*VPD:* *{new_vpd:.2f} kPa* — Ngưỡng chuẩn: {v_min}-{v_max} kPa\n"
               f"📢 *Đánh giá:* {status_text}\n🔮 *Dự báo:* _{trend}_")
        send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, msg)
    
    next_dt = current_sim_datetime + timedelta(minutes=10)
    if next_dt.hour == 0 and next_dt.minute == 0:
        st.session_state.is_running = False; st.session_state.is_completed = True   
    st.session_state.simulated_time = next_dt.strftime("%Y-%m-%d %H:%M:%S")

tab_future, tab_past, tab_edge = st.tabs(["🔮 THEO DÕI REALTIME THEO BUỔI", "📁 PHÂN TÍCH FILE MA TRẬN", "⚙️ WEBHOOK ĐIỀU KHIỂN"])

with tab_edge:
    st.markdown("### ⚙️ CẤU HÌNH WEBHOOK AUTOMATION")
    st.session_state.automation_webhook = st.text_input("Nhập API Webhook điều khiển thiết bị phần cứng nhà kính:", value=st.session_state.automation_webhook)

# --- XỬ LÝ ĐỒNG BỘ MA TRẬN LÊN REALTIME VÀ FILE ---
with tab_future:
    left_col, right_col = st.columns([4, 6])
    with left_col:
        st.markdown("<h3 style='color: #2E7D32; font-size: 17px;'>📋 MA TRẬN VPD ĐỘNG SINH HỌC</h3>", unsafe_allow_html=True)
        
        plant_choice = st.selectbox("Chọn mô hình cây trồng vận hành:", list(MA_TRAN_MAC_DINH.keys()))
        
        # Tạo bảng thiết lập dải cấu hình cho từng buổi thẳng trên UI
        matrix_live_config = {}
        is_custom = (plant_choice == "🛠️ Tùy chỉnh thủ công ma trận")
        
        for buoi, default_range in MA_TRAN_MAC_DINH[plant_choice].items():
            st.markdown(f"<div class='matrix-title'>{buoi}</div>", unsafe_allow_html=True)
            v_rng = st.slider(f"Dải tối ưu cho {buoi}", min_value=0.0, max_value=3.0, value=default_range, step=0.1, key=f"sl_{buoi}", disabled=not is_custom, label_visibility="collapsed")
            matrix_live_config[buoi] = v_rng

        with st.container(border=True):
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                if st.button("▶️ Khởi chạy hệ thống", type="primary", use_container_width=True):
                    if st.session_state.is_completed: 
                        st.session_state.simulated_time = "2026-05-24 07:00:00"
                        st.session_state.is_completed = False
                    st.session_state.is_running = True; st.rerun()
            with c_b2:
                if st.button("⏸️ Dừng hệ thống", type="secondary", use_container_width=True):
                    st.session_state.is_running = False; st.rerun()

        run_interval = 1 if st.session_state.is_running else 999999
        @st.fragment(run_every=run_interval)
        def live_monitor_panel():
            if st.session_state.is_running:
                st.session_state.countdown -= 1
                if st.session_state.countdown < 0: trigger_new_data_dynamic(matrix_live_config); st.rerun()
            
            sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
            cur_buoi = get_biological_block(sim_dt.hour)
            b_min, b_max = matrix_live_config[cur_buoi]
            
            with st.container(border=True):
                st.markdown(f"⏰ **{sim_dt.strftime('%d/%m — %H:%M')}** | Hiện tại là: **{cur_buoi}**")
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("🌡️ Nhiệt độ", f"{st.session_state.temp}°C")
                col_m2.metric("💧 Độ ẩm", f"{st.session_state.rh}%")
                
                v_calc = calculate_vpd(st.session_state.temp, st.session_state.rh)
                dp_calc = calculate_dew_point(st.session_state.temp, st.session_state.rh)
                
                st.markdown(f"📊 **VPD Thực Tế:** `{v_calc:.2f} kPa` (Ngưỡng đích của buổi: `{b_min}-{b_max} kPa`)")
                st.markdown(f"🥶 *Điểm ngưng tụ sương trên lá:* `{dp_calc} °C`")
        live_monitor_panel()

    with right_col:
        st.markdown("<h3 style='color: #2E7D32; font-size: 17px;'>📊 BIỂU ĐỒ VÀ NHẬT KÝ ĐỐI CHIẾU</h3>", unsafe_allow_html=True)
        if not st.session_state.history:
            st.info("Nhấn 'Khởi chạy hệ thống' để bắt đầu vẽ biểu đồ động 24h.")
        else:
            u_days = sorted(list(set([r["Ngày"] for r in st.session_state.history])), reverse=True)
            sel_day = st.selectbox("Chọn ngày xem đồ thị:", u_days, label_visibility="collapsed")
            df_all = pd.DataFrame(st.session_state.history)
            df_f = df_all[df_all["Ngày"] == sel_day].iloc[::-1].copy()
            
            # Lấy min max tổng quan để vẽ vùng dải nền an toàn cho biểu đồ
            cur_sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
            c_buoi = get_biological_block(cur_sim_dt.hour)
            v_min, v_max = matrix_live_config[c_buoi]
            
            st.altair_chart(draw_vpd_chart(df_f, v_min, v_max), use_container_width=True)
            
            st.markdown("##### 📋 Nhật ký đối chiếu chi tiết")
            st.dataframe(df_f[["STT", "Hiển thị Giờ", "Nhiệt độ (°C)", "Độ ẩm (%)", "VPD (kPa)", "Trạng thái"]], use_container_width=True, hide_index=True)


# --- TAB 2: ĐỌC FILE VÀ QUÉT MA TRẬN ĐỘNG THEO TỪNG DÒNG THỜI GIAN ---
with tab_past:
    st.markdown("<h3 style='color: #1A5276; font-size: 18px;'>📁 QUÉT FILE IOT THEO NỀN TẢNG MA TRẬN CHU KỲ</h3>", unsafe_allow_html=True)
    f_left, f_right = st.columns([4, 6])
    
    with f_left:
        with st.container(border=True):
            f_plant_choice = st.selectbox("Chọn cấu hình ma trận áp dụng cho File:", list(MA_TRAN_MAC_DINH.keys()), key="sb_f_plant")
            
            matrix_file_config = {}
            f_is_custom = (f_plant_choice == "🛠️ Tùy chỉnh thủ công ma trận")
            for buoi, default_range in MA_TRAN_MAC_DINH[f_plant_choice].items():
                st.markdown(f"<div class='matrix-title'>{buoi}</div>", unsafe_allow_html=True)
                v_rng = st.slider(f"Dải cho {buoi}", min_value=0.0, max_value=3.0, value=default_range, step=0.1, key=f"sl_f_{buoi}", disabled=not f_is_custom, label_visibility="collapsed")
                matrix_file_config[buoi] = v_rng
                
    with f_right:
        uploaded_file = st.file_uploader("Kéo thả file log IoT vào đây để quét áp lực sinh học:", type=["json", "csv", "xlsx"])
        filter_mode = st.selectbox("Chế độ gom nhóm hiển thị dữ liệu file:", ["📊 Xem toàn bộ dữ liệu gốc", "⏱️ 1 Ngày gần nhất (Gom 10 phút)"])
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.json'): df_upload = pd.DataFrame(json.load(uploaded_file))
                elif uploaded_file.name.endswith('.csv'): df_upload = pd.read_csv(uploaded_file)
                else: df_upload = pd.read_excel(uploaded_file)
                
                col_temp, col_rh, col_time = df_upload.columns[0], df_upload.columns[1], df_upload.columns[2]
                
                df_file_calc = pd.DataFrame()
                df_file_calc["datetime_internal"] = pd.to_datetime(df_upload[col_time], errors='coerce')
                df_file_calc["Nhiệt độ (°C)"] = pd.to_numeric(df_upload[col_temp], errors='coerce')
                df_file_calc["Độ ẩm (%)"] = pd.to_numeric(df_upload[col_rh], errors='coerce')
                df_file_calc = df_file_calc.dropna().sort_values("datetime_internal")
                df_file_calc["VPD (kPa)"] = df_file_calc.apply(lambda r: calculate_vpd(r["Nhiệt độ (°C)"], r["Độ ẩm (%)"]), axis=1)
                
                # Áp dụng thuật toán tính toán giờ stress động theo ma trận
                adv_results = calculate_dynamic_plant_stress(df_file_calc, matrix_file_config, filter_mode)
                
                st.markdown("<div style='font-weight:bold; color:#1A5276; margin-top:10px;'>🧠 ĐÁNH GIÁ CHUYÊN SÂU MA TRẬN BIOLOGICAL STRESS</div>", unsafe_allow_html=True)
                k_c1, k_c2, k_c3 = st.columns(3)
                k_c1.metric("⏳ Stress Khô Tích Lũy", f"{adv_results['dry_hours']} giờ")
                k_c2.metric("⏳ Stress Ẩm Tích Lũy", f"{adv_results['wet_hours']} giờ")
                k_c3.metric("🍄 Nguy cơ bùng dịch nấm", f"{adv_results['fungus_risk']}%")
                
                st.progress(adv_results['fungus_risk'] / 100.0)
                
                st.markdown("##### 📈 Đồ thị biến động tổng thể chu kỳ file")
                st.altair_chart(draw_vpd_chart(df_file_calc, 0.5, 1.2), use_container_width=True)
                
                st.markdown("##### 📊 Báo cáo thống kê chi tiết theo Buổi sinh học thực tế")
                df_block_rep = analyze_day_by_blocks_dynamic(df_file_calc.rename(columns={"VPD (kPa)": "VPD (kPa)"}).assign(Ngày="Dữ liệu File"), matrix_file_config, "Dữ liệu File")
                st.dataframe(df_block_rep, use_container_width=True, hide_index=True)
                
            except Exception as ex:
                st.error(f"❌ File không tương thích ma trận thời gian: {ex}")
