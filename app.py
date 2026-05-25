import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

# Import các module nội bộ từ kho hệ thống
from calculations import calculate_vpd, get_weather_by_time
from services import send_telegram_message, get_quick_solution
from analytics import analyze_day_by_blocks_dynamic, predict_vpd_trend_dynamic, calculate_dynamic_plant_stress, get_biological_block
from charts import draw_temperature_chart, draw_humidity_chart, draw_vpd_chart, draw_combined_chart

TELE_TOKEN = "8917951413:AAE6LKUEfYEYiQrFWGoKsQn0tumZc_XbcHg"
TELE_CHAT_ID = "7290661009"

st.set_page_config(page_title="Dynamic VPD Farm Analytics", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { overflow-y: auto !important; scroll-behavior: smooth; }
    .block-container { padding-top: 1.5rem; padding-bottom: 4rem; padding-left: 1.5rem; padding-right: 1.5rem; }
    h3 { margin-top: 0.2rem; margin-bottom: 0.8rem; padding-top: 0.2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 45px; font-weight: bold; font-size: 16px; }
    .danger-box-red { padding: 12px; background-color: #FFEBEE; border-left: 6px solid #FF1744; color: #B71C1C; font-weight: bold; font-size: 15px; border-radius: 4px; margin-bottom: 8px; }
    .danger-box-blue { padding: 12px; background-color: #E3F2FD; border-left: 6px solid #2979FF; color: #0D47A1; font-weight: bold; font-size: 15px; border-radius: 4px; margin-bottom: 8px; }
    .metric-card-upload { background-color: #F4F6F7; border: 1px solid #E5E7E9; padding: 10px; border-radius: 6px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# MA TRẬN VPD ĐỘNG CHUẨN ĐÀ LẠT CHO 9 LOẠI CÂY TRỒNG PHỔ BIẾN
DANH_SACH_MA_TRAN_CAY = {
    "🍓 Dâu tây Đà Lạt (Hoa / Trái)": {
        "🌅 Sáng (05h - 10h)": (0.6, 1.0), "☀️ Trưa (10h - 15h)": (0.8, 1.2), "🌇 Chiều (15h - 19h)": (0.6, 1.0), "🌌 Tối (19h - 23h)": (0.4, 0.8), "🌙 Khuya (23h - 05h)": (0.3, 0.6)
    },
    "🍓 Dâu tây Đà Lạt (Ngó / Cây con)": {
        "🌅 Sáng (05h - 10h)": (0.4, 0.7), "☀️ Trưa (10h - 15h)": (0.5, 0.9), "🌇 Chiều (15h - 19h)": (0.4, 0.8), "🌌 Tối (19h - 23h)": (0.3, 0.6), "🌙 Khuya (23h - 05h)": (0.2, 0.5)
    },
    "🌹 Hoa hồng nhà kính (Đà Lạt)": {
        "🌅 Sáng (05h - 10h)": (0.7, 1.1), "☀️ Trưa (10h - 15h)": (0.9, 1.4), "🌇 Chiều (15h - 19h)": (0.8, 1.2), "🌌 Tối (19h - 23h)": (0.5, 0.9), "🌙 Khuya (23h - 05h)": (0.4, 0.7)
    },
    "🍅 Cà chua bi / 🫑 Ớt chuông Palermo": {
        "🌅 Sáng (05h - 10h)": (0.7, 1.2), "☀️ Trưa (10h - 15h)": (0.9, 1.5), "🌇 Chiều (15h - 19h)": (0.8, 1.3), "🌌 Tối (19h - 23h)": (0.5, 0.9), "🌙 Khuya (23h - 05h)": (0.4, 0.8)
    },
    "🥬 Xà lách Thủy canh Đà Lạt": {
        "🌅 Sáng (05h - 10h)": (0.4, 0.8), "☀️ Trưa (10h - 15h)": (0.6, 1.0), "🌇 Chiều (15h - 19h)": (0.5, 0.9), "🌌 Tối (19h - 23h)": (0.3, 0.7), "🌙 Khuya (23h - 05h)": (0.3, 0.6)
    },
    "🛠️ Tùy chỉnh thủ công ma trận riêng": {
        "🌅 Sáng (05h - 10h)": (0.6, 1.0), "☀️ Trưa (10h - 15h)": (0.8, 1.2), "🌇 Chiều (15h - 19h)": (0.6, 1.0), "🌌 Tối (19h - 23h)": (0.4, 0.8), "🌙 Khuya (23h - 05h)": (0.3, 0.6)
    }
}
plant_keys = list(DANH_SACH_MA_TRAN_CAY.keys())

# Khởi tạo bộ nhớ tạm Session State
if 'history' not in st.session_state: st.session_state.history = []
if 'stt_counter' not in st.session_state: st.session_state.stt_counter = 0 
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'is_completed' not in st.session_state: st.session_state.is_completed = False
if 'countdown' not in st.session_state: st.session_state.countdown = 15
if 'simulated_time' not in st.session_state: st.session_state.simulated_time = "2026-05-24 07:00:00"
if 'current_matrix' not in st.session_state: st.session_state.current_matrix = DANH_SACH_MA_TRAN_CAY[plant_keys[0]].copy()
if 'file_matrix' not in st.session_state: st.session_state.file_matrix = DANH_SACH_MA_TRAN_CAY[plant_keys[0]].copy()

def style_status_rows(row):
    styles = [''] * len(row)
    status = str(row['Trạng thái'])
    if "Lý tưởng" in status: styles[row.index.get_loc('Trạng thái')] = 'background-color: #E8F5E9; color: #1B5E20; font-weight: bold;'
    elif "Quá khô" in status: styles[row.index.get_loc('Trạng thái')] = 'background-color: #FFEBEE; color: #B71C1C; font-weight: bold;'
    elif "Quá ẩm" in status: styles[row.index.get_loc('Trạng thái')] = 'background-color: #E3F2FD; color: #0D47A1; font-weight: bold;'
    return styles

def trigger_new_data_dynamic():
    current_sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
    st.session_state.temp, st.session_state.rh = get_weather_by_time(current_sim_dt)
    st.session_state.countdown = 15
    st.session_state.stt_counter += 1
    
    new_vpd = calculate_vpd(st.session_state.temp, st.session_state.rh)
    block_name = get_biological_block(current_sim_dt.hour)
    vpd_min, vpd_max = st.session_state.current_matrix[block_name]
    
    status_text = "⚠️ Quá ẩm" if new_vpd < vpd_min else ("✅ Lý tưởng" if new_vpd <= vpd_max else "🚨 Quá khô")
    tele_status = "🟦 QUÁ ẨM" if new_vpd < vpd_min else ("🟩 LÝ TƯỞNG" if new_vpd <= vpd_max else "🟥 QUÁ KHÔ")
    
    st.session_state.history.insert(0, {
        "STT": st.session_state.stt_counter, "Ngày": current_sim_dt.strftime("Ngày %d/%m"),
        "Thời gian mô phỏng": current_sim_dt, "Hiển thị Giờ": current_sim_dt.strftime("%H:%M"),
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
        st.session_state.is_running = False
        st.session_state.is_completed = True
    st.session_state.simulated_time = next_dt.strftime("%Y-%m-%d %H:%M:%S")

tab_future, tab_past = st.tabs(["🔮 XEM DỰ BÁO & THEO DÕI TƯƠNG LAI", "📁 TẢI FILE & PHÂN TÍCH LỊCH SỬ"])

# --------------------------------------------------------
# TAB 1: REALTIME MONITORING WITH DYNAMIC MATRIX
# --------------------------------------------------------
with tab_future:
    left_col, right_col = st.columns([3.8, 6.2])
    with left_col:
        st.markdown("<h3 style='color: #2E7D32; font-size: 18px;'>🤖 TRẠM ĐIỀU HÀNH MA TRẬN ĐỘNG</h3>", unsafe_allow_html=True)
        with st.container(border=True):
            cb1, cb2 = st.columns(2)
            with cb1:
                if st.button("▶️ Kích hoạt", type="primary", use_container_width=True, disabled=st.session_state.is_running):
                    if st.session_state.is_completed:
                        st.session_state.simulated_time = "2026-05-24 07:00:00"
                        st.session_state.is_completed = False
                    st.session_state.is_running = True
                    if st.session_state.stt_counter == 0: trigger_new_data_dynamic()
                    st.rerun()
            with cb2:
                if st.button("⏸️ Dừng trạm", type="secondary", use_container_width=True, disabled=not st.session_state.is_running):
                    st.session_state.is_running = False
                    st.rerun()

        with st.container(border=True):
            st.markdown("**1. Chọn mô hình cây trồng:**")
            p_opt = st.selectbox("Cây trồng:", plant_keys, label_visibility="collapsed")
            
            if p_opt != "🛠️ Tùy chỉnh thủ công ma trận riêng":
                st.session_state.current_matrix = DANH_SACH_MA_TRAN_CAY[p_opt].copy()
                st.caption("⚙️ *Hệ thống tự động khóa dải tối ưu theo nhịp sinh học đặc thù.*")
            
            st.markdown("**2. Cấu hình chi tiết dải VPD từng buổi (kPa):**")
            for block, (vmin, vmax) in st.session_state.current_matrix.items():
                is_disabled = (p_opt != "🛠️ Tùy chỉnh thủ công ma trận riêng")
                nv = st.slider(f"{block}:", 0.0, 3.0, (vmin, vmax), step=0.1, key=f"sl_{block}", disabled=is_disabled)
                st.session_state.current_matrix[block] = nv

        run_interval = 1 if st.session_state.is_running else 999999

        @st.fragment(run_every=run_interval)
        def left_panel_live():
            if st.session_state.is_running:
                st.session_state.countdown -= 1
                if st.session_state.countdown < 0:
                    trigger_new_data_dynamic()
                    st.rerun()
            
            curr_sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
            curr_block = get_biological_block(curr_sim_dt.hour)
            b_min, b_max = st.session_state.current_matrix[curr_block]
            
            with st.container(border=True):
                st.markdown(f"⏰ **{curr_sim_dt.strftime('Ngày %d/%m — %H:%M')}** ({curr_block})")
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
                st.markdown(f"**Giải pháp ứng phó:** _{get_quick_solution(vpd_now, b_min, b_max, curr_sim_dt.hour)}_")
                
        left_panel_live()

    with right_col:
        st.markdown("<h3 style='color: #2E7D32; font-size: 18px;'>📊 TRUNG TÂM PHÂN TÍCH MA TRẬN CHU KỲ REALTIME</h3>", unsafe_allow_html=True)
        if not st.session_state.history:
            st.info("Chưa có số liệu. Vui lòng nhấn '▶️ Kích hoạt' để chạy mô phỏng.")
        else:
            u_days = sorted(list(set([r["Ngày"] for r in st.session_state.history])), reverse=True)
            f1, f2 = st.columns([7, 3])
            with f1: s_day = st.selectbox("Lọc ngày:", u_days, label_visibility="collapsed")
            with f2:
                if st.button("🗑️ Reset Trạm", use_container_width=True):
                    st.session_state.stt_counter = 0; st.session_state.history = []; st.session_state.simulated_time = "2026-05-24 07:00:00"
                    st.session_state.is_completed = False; st.session_state.is_running = False
                    st.rerun()

            df_all = pd.DataFrame(st.session_state.history)
            df_fil = df_all[df_all["Ngày"] == s_day].iloc[::-1].copy()
            
            curr_sim_dt = datetime.strptime(st.session_state.simulated_time, "%Y-%m-%d %H:%M:%S")
            curr_block = get_biological_block(curr_sim_dt.hour)
            b_min, b_max = st.session_state.current_matrix[curr_block]

            m_t1, m_t2, m_t3 = st.tabs(["📈 Biểu đồ trực quan", "📊 Đối chiếu Ma Trận Buổi", "📋 Nhật ký chi tiết"])
            with m_t1:
                st.altair_chart(draw_vpd_chart(df_fil, b_min, b_max), use_container_width=True)
            with m_t2:
                st.dataframe(analyze_day_by_blocks_dynamic(st.session_state.history, st.session_state.current_matrix, s_day), use_container_width=True, hide_index=True)
            with m_t3:
                styled_df = df_fil[["STT", "Hiển thị Giờ", "Nhiệt độ (°C)", "Độ ẩm (%)", "VPD (kPa)", "Trạng thái"]].style.apply(style_status_rows, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --------------------------------------------------------
# TAB 2: UPLOAD & BULK FILE DYNAMIC ANALYTICS
# --------------------------------------------------------
with tab_past:
    st.markdown("<h3 style='color: #1A5276; font-size: 19px;'>📁 PHÂN TÍCH FILE IOT THEO MA TRẬN ĐỘNG CHUYÊN SÂU</h3>", unsafe_allow_html=True)
    tl, tr = st.columns([5, 5])
    with tl:
        with st.container(border=True):
            st.markdown("**⚙️ Cấu hình ma trận dải lọc file:**")
            f_p_opt = st.selectbox("Chọn mô hình cây trồng áp dụng cho file:", plant_keys, key="file_plant_sel")
            if f_p_opt != "🛠️ Tùy chỉnh thủ công ma trận riêng":
                st.session_state.file_matrix = DANH_SACH_MA_TRAN_CAY[f_p_opt].copy()
            for block, (vmin, vmax) in st.session_state.file_matrix.items():
                f_nv = st.slider(f"File - {block}:", 0.0, 3.0, (vmin, vmax), step=0.1, key=f"f_sl_{block}", disabled=(f_p_opt != "🛠️ Tùy chỉnh thủ công ma trận riêng"))
                st.session_state.file_matrix[block] = f_nv
    with tr:
        with st.container(border=True):
            uploaded_file = st.file_uploader("Tải file IoT (JSON, CSV, Excel):", type=["json", "csv", "xlsx"])
            t_filter_opt = st.selectbox("Chế độ xử lý thời gian:", ["📊 Xem toàn bộ dữ liệu gốc của File", "📆 Tự chọn một ngày cụ thể trên lịch"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.json'):
                js = json.load(uploaded_file)
                df_up = pd.DataFrame([js]) if isinstance(js, dict) and not isinstance(list(js.values())[0], (dict, list)) else pd.DataFrame(js)
            elif uploaded_file.name.endswith('.csv'): df_up = pd.read_csv(uploaded_file)
            else: df_up = pd.read_excel(uploaded_file)
            
            c_t, c_h, c_time = None, None, None
            for c in df_up.columns:
                cl = str(c).lower().strip()
                if 'temp' in cl or 'nhiet' in cl: c_t = c
                if 'humi' in cl or 'rh' in cl or 'do am' in cl: c_h = c
                if any(k in cl for k in ['time', 'thời gian', 'date', 'timestamp']): c_time = c

            if not c_t: c_t = df_up.columns[0]
            if not c_h: c_h = df_up.columns[1]
            if not c_time: c_time = df_up.columns[2]

            r_dts = [pd.to_datetime(str(v).strip(), errors='coerce') for v in df_up[c_time]]
            df_calc = pd.DataFrame()
            df_calc["datetime_internal"] = r_dts
            df_calc["Nhiệt độ (°C)"] = pd.to_numeric(df_up[c_t], errors='coerce')
            df_calc["Độ ẩm (%)"] = pd.to_numeric(df_up[c_h], errors='coerce')
            df_calc = df_calc.dropna().sort_values("datetime_internal")
            df_calc["VPD (kPa)"] = df_calc.apply(lambda r: calculate_vpd(r["Nhiệt độ (°C)"], r["Độ ẩm (%)"]), axis=1)
            df_calc["only_date"] = df_calc["datetime_internal"].dt.date

            if "Tự chọn một ngày cụ thể" in t_filter_opt:
                av_dates = sorted(df_calc["only_date"].unique())
                s_date = st.date_input("Chọn ngày trên lịch:", value=av_dates[-1] if av_dates else datetime.now().date())
                df_calc = df_calc[df_calc["only_date"] == s_date]

            df_calc["Hiển thị Giờ"] = df_calc["datetime_internal"].dt.strftime("%H:%M")
            df_calc["Trạng thái"] = df_calc.apply(lambda r: "⚠️ Quá ẩm" if r["VPD (kPa)"] < st.session_state.file_matrix[get_biological_block(r["datetime_internal"].hour)][0] else ("✅ Lý tưởng" if r["VPD (kPa)"] <= st.session_state.file_matrix[get_biological_block(r["datetime_internal"].hour)][1] else "🚨 Quá khô"), axis=1)

            # KPIs
            st.markdown("#### 📊 TỔNG QUAN CHU KỲ MA TRẬN FILE")
            k1, k2, k3 = st.columns(3)
            k1.metric("VPD Trung Bình", f"{df_calc['VPD (kPa)'].mean():.2f} kPa")
            k2.metric("Nhiệt độ TB", f"{df_calc['Nhiệt độ (°C)'].mean():.1f} °C")
            k3.metric("Độ ẩm TB", f"{df_calc['Độ ẩm (%)'].mean():.1f} %")

            # Stress analysis
            stress = calculate_dynamic_plant_stress(df_calc, st.session_state.file_matrix, t_filter_opt)
            st.markdown(f"⚠️ **Đánh giá Agronomy chuyên sâu:** Tích lũy Stress Khô: `{stress['dry_hours']} giờ` | Tích lũy Stress Ẩm: `{stress['wet_hours']} giờ` (Nguy cơ bùng phát nấm: `{stress['fungus_risk']}%`)")

            st.altair_chart(draw_vpd_chart(df_calc, 0.6, 1.2), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Lỗi cấu trúc file tải lên: {str(e)}")
