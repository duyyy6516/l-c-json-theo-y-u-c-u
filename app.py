import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

# Import các module nội bộ từ kho Git của bạn
from calculations import calculate_vpd, get_weather_by_time
from services import send_telegram_message, get_quick_solution
from analytics import analyze_day_by_blocks_rt, predict_vpd_trend_v3
from charts import draw_temperature_chart, draw_humidity_chart, draw_vpd_chart, draw_combined_chart

TELE_TOKEN = "8917951413:AAE6LKUEfYEYiQrFWGoKsQn0tumZc_XbcHg"
TELE_CHAT_ID = "7290661009"

st.set_page_config(page_title="VPD Farm Analytics", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 2.5rem; padding-bottom: 0rem; padding-left: 1.5rem; padding-right: 1.5rem; }
    h3 { margin-top: 0.2rem; margin-bottom: 0.8rem; padding-top: 0.2rem; }
    div[st-delegate="element-container"] { margin-bottom: 0.3rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 45px; font-weight: bold; font-size: 16px; }
    .danger-box-red { padding: 12px; background-color: #FFEBEE; border-left: 6px solid #FF1744; color: #B71C1C; font-weight: bold; font-size: 15px; border-radius: 4px; margin-bottom: 8px; }
    .danger-box-blue { padding: 12px; background-color: #E3F2FD; border-left: 6px solid #2979FF; color: #0D47A1; font-weight: bold; font-size: 15px; border-radius: 4px; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

if 'temp' not in st.session_state: st.session_state.temp = 0.0
if 'rh' not in st.session_state: st.session_state.rh = 0.0
if 'countdown' not in st.session_state: st.session_state.countdown = 15 
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'is_completed' not in st.session_state: st.session_state.is_completed = False 
if 'history' not in st.session_state: st.session_state.history = []
if 'stt_counter' not in st.session_state: st.session_state.stt_counter = 0 
if 'plant_idx' not in st.session_state: st.session_state.plant_idx = 0
if 'vpd_range_val' not in st.session_state: st.session_state.vpd_range_val = (0.6, 1.0)
if 'simulated_time' not in st.session_state: st.session_state.simulated_time = "2026-05-24 07:00:00"

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

tab_future, tab_past = st.tabs(["🔮 XEM DỰ BÁO & THEO DÕI TƯƠNG LAI", "📁 TẢI FILE & PHÂN TÍCH LỊCH SỬ"])

# =========================================================================
# TAB 1: MÔ PHỎNG REALTIME TRONG TƯƠNG LAI
# =========================================================================
with tab_future:
    left_col, right_col = st.columns([3.5, 6.5])
    with left_col:
        st.markdown("<h3 style='color: #2E7D32; font-size: 18px;'>🤖 TRẠM ĐIỀU HÀNH THÔNG MINH</h3>", unsafe_allow_html=True)
        with st.container(border=True):
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("▶️ Bắt đầu", type="primary", use_container_width=True, key="btn_start", disabled=st.session_state.is_running):
                    if st.session_state.is_completed: setup_next_day()
                    st.session_state.is_running = True
                    if st.session_state.stt_counter == 0: trigger_new_data(st.session_state.vpd_range_val[0], st.session_state.vpd_range_val[1])
                    st.rerun()
            with col_btn2:
                if st.button("⏸️ Tạm dừng", type="secondary", use_container_width=True, key="btn_stop", disabled=not st.session_state.is_running):
                    st.session_state.is_running = False
                    st.rerun()
                    
        with st.container(border=True):
            plant_list = ["🍓 Dâu tây Đà Lạt", "🌹 Hoa hồng nhà kính", "🌼 Hoa cúc / Hoa đồng tiền", "🍅 Cà chua bi / 🫑 Ớt chuông", "🛠️ Tùy chỉnh thủ công"]
            plant_option = st.selectbox("Cây trồng:", plant_list, index=st.session_state.plant_idx, key="plant_select", disabled=st.session_state.is_running, label_visibility="collapsed")
            st.session_state.plant_idx = plant_list.index(plant_option)
            
            default_range = (0.6, 1.0) if plant_option == "🍓 Dâu tây Đà Lạt" else ((0.8, 1.2) if plant_option == "🌹 Hoa hồng nhà kính" else ((0.7, 1.1) if plant_option == "🌼 Hoa cúc / Hoa đồng tiền" else ((0.8, 1.4) if plant_option == "🍅 Cà chua bi / 🫑 Ớt chuông" else st.session_state.vpd_range_val)))
            vpd_range = st.slider("Khoảng tối ưu (kPa):", min_value=0.0, max_value=3.0, value=default_range, step=0.1, key="vpd_slider", disabled=st.session_state.is_running or (plant_option != "🛠️ Tùy chỉnh thủ công"))
            st.session_state.vpd_range_val = vpd_range
            vpd_min, vpd_max = vpd_range

        run_interval = 1 if st.session_state.is_running else 999999

        @st.fragment(run_every=run_interval)
        def left_panel_monitor():
            if st.session_state.is_running:
                st.session_state.countdown -= 1
                if st.session_state.countdown < 0: 
                    trigger_new_data(vpd_min, vpd_max)
                    st.rerun()
                    
            if st.session_state.is_running: st.caption(f"⏳ Đổi số sau: **{st.session_state.countdown}s**")
            elif st.session_state.is_completed: st.success("🏁 Hết ngày!")

            current_sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
            current_date_display = current_sim_dt.strftime("Ngày %d/%m")
            
            with st.container(border=True):
                st.markdown(f"⏰ **{current_date_display} — {current_sim_dt.strftime('%H:%M')}**")
                col1, col2 = st.columns(2)
                with col1: st.metric(label="🌡️ Nhiệt độ", value=f"{st.session_state.temp}°C" if st.session_state.stt_counter > 0 else "--°C")
                with col2: st.metric(label="💧 Độ ẩm", value=f"{st.session_state.rh}%" if st.session_state.stt_counter > 0 else "--%")

            vpd_result = calculate_vpd(st.session_state.temp, st.session_state.rh)
            with st.container(border=True):
                st.markdown("<p style='color:#2E7D32; font-weight:bold; margin-bottom:2px;'>🎯 TRUNG TÂM ĐIỀU HÀNH LỆNH</p>", unsafe_allow_html=True)
                if st.session_state.stt_counter == 0:
                    st.info("Đang chờ kích hoạt trạm...")
                else:
                    status_lbl = "🟦 QUÁ ẨM" if vpd_result < vpd_min else ("🟩 LÝ TƯỞNG" if vpd_result <= vpd_max else "🟥 QUÁ KHÔ")
                    text_color = "#0068C9" if vpd_result < vpd_min else ("#2E7D32" if vpd_result <= vpd_max else "#FF4B4B")
                    
                    unique_days = sorted(list(set([r["Ngày"] for r in st.session_state.history])), reverse=True)
                    history_of_latest_day = [r for r in st.session_state.history if r["Ngày"] == (unique_days[0] if unique_days else current_date_display)]
                    
                    trend, trend_type = predict_vpd_trend_v3(history_of_latest_day, current_sim_dt.hour, vpd_min, vpd_max)
                    
                    if trend_type == "danger_red":
                        st.markdown(f"<div class='danger-box-red'>🚨 {trend}</div>", unsafe_allow_html=True)
                    elif trend_type == "danger_blue":
                        st.markdown(f"<div class='danger-box-blue'>🚨 {trend}</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"**VPD Hiện Tại:** <span style='color: {text_color}; font-weight: bold; font-size:18px;'>{vpd_result:.2f} kPa</span> ({status_lbl})", unsafe_allow_html=True)
                    st.markdown(f"**Biện pháp kỹ thuật:** _{get_quick_solution(vpd_result, vpd_min, vpd_max, current_sim_dt.hour)}_")
                    if trend_type not in ["danger_red", "danger_blue"]:
                        st.markdown(f"**Dự báo chu kỳ:** {trend}")

        left_panel_monitor()

    with right_col:
        st.markdown("<h3 style='color: #2E7D32; font-size: 18px;'>📊 TRUNG TÂM PHÂN TÍCH CHU KỲ REALTIME</h3>", unsafe_allow_html=True)
        if len(st.session_state.history) == 0:
            st.info("Chưa có số liệu. Vui lòng bấm '▶️ Bắt đầu' để tải dữ liệu biểu đồ.")
        else:
            unique_days = sorted(list(set([r["Ngày"] for r in st.session_state.history])), reverse=True)
            filter_col1, filter_col2 = st.columns([7, 3])
            with filter_col1: selected_view_day = st.selectbox("Lọc ngày lịch sử:", unique_days, label_visibility="collapsed")
            with filter_col2:
                if st.button("🗑️ Reset All", use_container_width=True, key="btn_reset_rt"):
                    st.session_state.stt_counter = 0; st.session_state.history = []; st.session_state.simulated_time = "2026-05-24 07:00:00"
                    st.session_state.is_completed = False; st.session_state.is_running = False
                    st.rerun()

            df_all_records = pd.DataFrame(st.session_state.history)
            df_filtered = df_all_records[df_all_records["Ngày"] == selected_view_day].iloc[::-1].copy()

            main_tab1, main_tab2, main_tab3 = st.tabs(["📈 Biểu đồ trực quan", "📊 Thống kê theo buổi", "📋 Bảng Nhật ký số liệu"])
            with main_tab1:
                sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs(["🎯 Chỉ số VPD", "🌡️ Nhiệt độ", "💧 Độ ẩm", "📊 Tổ hợp 3 chỉ số"])
                with sub_t1: st.altair_chart(draw_vpd_chart(df_filtered, vpd_min, vpd_max), use_container_width=True)
                with sub_t2: st.altair_chart(draw_temperature_chart(df_filtered), use_container_width=True)
                with sub_t3: st.altair_chart(draw_humidity_chart(df_filtered), use_container_width=True)
                with sub_t4: st.altair_chart(draw_combined_chart(df_filtered), use_container_width=True)
            with main_tab2:
                st.dataframe(analyze_day_by_blocks_rt(st.session_state.history, vpd_min, vpd_max, selected_view_day), use_container_width=True, hide_index=True, height=180)
            with main_tab3:
                df_display = df_filtered.copy()
                df_display["Thời gian"] = df_display["Hiển thị Giờ"]
                st.dataframe(df_display[["STT", "Thời gian", "Nhiệt độ (°C)", "Độ ẩm (%)", "VPD (kPa)", "Trạng thái"]], use_container_width=True, hide_index=True, height=200)


# =========================================================================
# 📁 TAB 2: TỰ ĐỘNG PHÂN TÍCH FILE IOT (ĐÃ SỬA LỖI 10T THÀNH 10min CHO PANDAS)
# =========================================================================
with tab_past:
    st.markdown("<h3 style='color: #1A5276; font-size: 18px;'>📁 TỰ ĐỘNG PHÂN TÍCH FILE IOT (JSON / CSV / XLSX)</h3>", unsafe_allow_html=True)
    
    upload_col1, upload_col2 = st.columns([5, 5])
    with upload_col1:
        uploaded_file = st.file_uploader("Kéo thả file IoT nhà kính của bạn vào đây:", type=["json", "csv", "xlsx"])
    with upload_col2:
        time_filter_option = st.selectbox(
            "📆 Chọn chế độ xem / Khoảng cách thời gian:",
            ["📆 Tự chọn một ngày cụ thể trên lịch", "⏱️ 1 Ngày gần nhất (Gom trung bình 10 phút)", "📅 1 Tuần gần nhất (Gom trung bình Giờ)", "🗓️ 1 Tháng gần nhất (Gom trung bình Giờ)", "🏢 1 Quý gần nhất (Gom trung bình Ngày)", "📊 Xem toàn bộ dữ liệu thô file"]
        )
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.json'):
                json_data = json.load(uploaded_file)
                if isinstance(json_data, dict) and not isinstance(list(json_data.values())[0], (dict, list)):
                    df_upload = pd.DataFrame([json_data])
                else:
                    df_upload = pd.DataFrame(json_data)
            elif uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
                
            col_temp, col_rh, col_time = None, None, None
            for col in df_upload.columns:
                col_lower = str(col).lower().strip()
                if any(k in col_lower for k in ['tempkk', 'temp', 'nhiet', 't°', 't(°c)', 'temperature', 'value1']):
                    col_temp = col
                if any(k in col_lower for k in ['humikk', 'rh', 'hum', 'do am', 'humidity', 'h(%)', 'value2']):
                    col_rh = col
                if any(k in col_lower for k in ['thời gian', 'time', 'gio', 'date', 'timestamp', 'mốc', 'created_at']):
                    col_time = col

            if not col_temp and len(df_upload.columns) > 0: col_temp = df_upload.columns[0]
            if not col_rh and len(df_upload.columns) > 1: col_rh = df_upload.columns[1]
            if not col_time and len(df_upload.columns) > 2: col_time = df_upload.columns[2]

            raw_datetimes = []
            for val in df_upload[col_time].astype(str):
                cleaned_val = val.strip()
                try:
                    if " " in cleaned_val and "-" in cleaned_val.split(" ")[1]:
                        date_p, time_p = cleaned_val.split(" ")
                        time_p = time_p.replace("-", ":")
                        dt_obj = datetime.strptime(f"{date_p} {time_p}", "%Y-%m-%d %H:%M:%S")
                    else:
                        dt_obj = pd.to_datetime(cleaned_val)
                    raw_datetimes.append(dt_obj)
                except:
                    raw_datetimes.append(datetime.now())

            df_raw_calc = pd.DataFrame()
            df_raw_calc["datetime_internal"] = raw_datetimes
            df_raw_calc["Nhiệt độ (°C)"] = pd.to_numeric(df_upload[col_temp], errors='coerce')
            df_raw_calc["Độ ẩm (%)"] = pd.to_numeric(df_upload[col_rh], errors='coerce')
            df_raw_calc = df_raw_calc.dropna(subset=["Nhiệt độ (°C)", "Độ ẩm (%)"]).sort_values("datetime_internal")

            # Xử lý cắt mốc thời gian và gán lịch chọn ngày tùy chọn
            if len(df_raw_calc) > 0:
                df_raw_calc["only_date"] = df_raw_calc["datetime_internal"].dt.date
                available_dates = sorted(df_raw_calc["only_date"].unique())
                
                if "Tự chọn một ngày cụ thể" in time_filter_option:
                    st.write("")
                    selected_date = st.date_input(
                        "👇 Hãy chọn ngày bạn muốn trích xuất dữ liệu:",
                        value=available_dates[-1] if available_dates else datetime.now().date(),
                        min_value=available_dates[0] if available_dates else None,
                        max_value=available_dates[-1] if available_dates else None
                    )
                    df_raw_calc = df_raw_calc[df_raw_calc["only_date"] == selected_date]
                else:
                    max_time_in_file = df_raw_calc["datetime_internal"].max()
                    if "1 Ngày gần nhất" in time_filter_option:
                        df_raw_calc = df_raw_calc[df_raw_calc["datetime_internal"] >= (max_time_in_file - timedelta(days=1))]
                    elif "1 Tuần gần nhất" in time_filter_option:
                        df_raw_calc = df_raw_calc[df_raw_calc["datetime_internal"] >= (max_time_in_file - timedelta(days=7))]
                    elif "1 Tháng gần nhất" in time_filter_option:
                        df_raw_calc = df_raw_calc[df_raw_calc["datetime_internal"] >= (max_time_in_file - timedelta(days=30))]
                    elif "1 Quý gần nhất" in time_filter_option:
                        df_raw_calc = df_raw_calc[df_raw_calc["datetime_internal"] >= (max_time_in_file - timedelta(days=90))]

            # 🛠️ THUẬT TOÁN GOM NHÓM ĐÃ FIX LỖI: Sử dụng "10min" và "1h" thay cho chữ "T" bị loại bỏ ở bản Pandas mới
            if len(df_raw_calc) > 0:
                df_raw_calc.set_index("datetime_internal", inplace=True)
                
                if "1 Tuần gần nhất" in time_filter_option or "1 Tháng gần nhất" in time_filter_option:
                    df_resampled = df_raw_calc.resample("1h").mean().dropna()
                    df_resampled["Hiển thị Giờ"] = df_resampled.index.strftime("%d/%m %H:00")
                elif "1 Quý gần nhất" in time_filter_option:
                    df_resampled = df_raw_calc.resample("1d").mean().dropna()
                    df_resampled["Hiển thị Giờ"] = df_resampled.index.strftime("%d/%m")
                elif "Xem toàn bộ" in time_filter_option:
                    df_resampled = df_raw_calc.copy()
                    df_resampled["Hiển thị Giờ"] = df_resampled.index.strftime("%d/%m %H:%M:%S")
                else:
                    # ✨ ĐÃ SỬA LỖI TẠI ĐÂY: Sử dụng "10min" (Chuẩn mới) thay cho "10T" cũ
                    df_resampled = df_raw_calc.resample("10min").mean().dropna()
                    df_resampled["Hiển thị Giờ"] = df_resampled.index.strftime("%H:%M")
                
                df_resampled.reset_index(inplace=True)
            else:
                df_resampled = pd.DataFrame(columns=["Nhiệt độ (°C)", "Độ ẩm (%)", "Hiển thị Giờ"])

            df_processed = pd.DataFrame()
            df_processed["Nhiệt độ (°C)"] = df_resampled["Nhiệt độ (°C)"].round(2)
            df_processed["Độ ẩm (%)"] = df_resampled["Độ ẩm (%)"].round(2)
            df_processed["Hiển thị Giờ"] = df_resampled["Hiển thị Giờ"]
            df_processed["VPD (kPa)"] = df_processed.apply(lambda row: round(calculate_vpd(row["Nhiệt độ (°C)"], row["Độ ẩm (%)"]), 2), axis=1)
            df_processed["Ngày"] = "Dữ liệu File"
            df_processed["Trạng thái"] = df_processed["VPD (kPa)"].apply(lambda x: "⚠️ Quá ẩm" if x < vpd_min else ("✅ Lý tưởng" if x <= vpd_max else "🚨 Quá khô"))
            
            st.write("") 
            
            res_left, res_right = st.columns([6.5, 3.5])
            with res_left:
                st.markdown(f"##### 📈 Hệ thống Biểu đồ trích xuất từ File")
                
                file_sub_tab1, file_sub_tab2, file_sub_tab3, file_sub_tab4 = st.tabs([
                    "🎯 Chỉ số VPD", "🌡️ Nhiệt độ", "💧 Độ ẩm", "📊 Tổ hợp 3 chỉ số"
                ])
                with file_sub_tab1: 
                    st.altair_chart(draw_vpd_chart(df_processed, vpd_min, vpd_max), use_container_width=True)
                with file_sub_tab2: 
                    st.altair_chart(draw_temperature_chart(df_processed), use_container_width=True)
                with file_sub_tab3: 
                    st.altair_chart(draw_humidity_chart(df_processed), use_container_width=True)
                with file_sub_tab4: 
                    st.altair_chart(draw_combined_chart(df_processed), use_container_width=True)
                
            with res_right:
                st.markdown("##### 📋 Nhật ký VPD đã xử lý")
                st.caption(f"Tổng số mốc dữ liệu hiển thị (sau gom nhóm): {len(df_processed)} điểm.")
                preview_cols = ["Hiển thị Giờ", "Nhiệt độ (°C)", "Độ ẩm (%)", "VPD (kPa)", "Trạng thái"]
                st.dataframe(df_processed[preview_cols].head(300), use_container_width=True, hide_index=True, height=210)
                
                st.download_button(
                    label="📥 Tải xuống kết quả tính toán (.csv)",
                    data=df_processed.to_csv(index=False).encode('utf-8'),
                    file_name=f"vpd_calculated_smart.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        except Exception as err:
            st.error(f"❌ Cấu trúc tệp không tương thích hoặc lỗi xử lý lịch ngày tùy chỉnh. Chi tiết lỗi: {err}")
    else:
        st.info("💡 Hệ thống tự động bóc tách: Gom trung bình 10 phút cho chu kỳ xem ngày giúp tối ưu tốc độ biểu đồ và xử lý mượt mà.")
