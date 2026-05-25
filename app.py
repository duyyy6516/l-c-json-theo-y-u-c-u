import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

from calculations import calculate_vpd, get_weather_by_time
from services import send_telegram_message
from analytics import (
    analyze_day_by_blocks_rt, 
    predict_vpd_trend_v3, 
    calculate_plant_stress_hours, 
    calculate_dew_point, 
    get_biological_block
)
from charts import draw_vpd_chart, draw_combined_temp_humidity_chart

TELE_TOKEN = "8917951413:AAE6LKUEfYEYiQrFWGoKsQn0tumZc_XbcHg"
TELE_CHAT_ID = "7290661009"

st.set_page_config(page_title="VPD Smart Farm Monitor Pro", page_icon="🌿", layout="wide")

# SỬA LỖI PYTHON 3.14: Gộp toàn bộ CSS thành chuỗi một dòng phẳng để tránh lỗi phân tích cú pháp xuống dòng
st.markdown("<style>html, body, [data-testid=\"stAppViewContainer\"] { overflow-y: auto !important; scroll-behavior: smooth; } .block-container { padding-top: 1rem; padding-bottom: 2rem; padding-left: 1.5rem; padding-right: 1.5rem; } .danger-box-red { padding: 12px; background-color: #C0392B; border-left: 6px solid #17202A; color: #FFFFFF; font-weight: bold; border-radius: 4px; margin-bottom: 8px; } .danger-box-yellow { padding: 12px; background-color: #D4AC0D; border-left: 6px solid #17202A; color: #17202A; font-weight: bold; border-radius: 4px; margin-bottom: 8px; } .danger-box-blue { padding: 12px; background-color: #2E86C1; border-left: 6px solid #17202A; color: #FFFFFF; font-weight: bold; border-radius: 4px; margin-bottom: 8px; } .normal-box { padding: 12px; background-color: #27AE60; border-left: 6px solid #117A65; color: #FFFFFF; font-weight: bold; border-radius: 4px; margin-bottom: 8px; }</style>", unsafe_with_html=True)

PRESETS = {
    "🌱 Cây con / Nhân giống (0.4 - 0.8 kPa)": {"min": 0.4, "max": 0.8},
    "🌿 Sinh trưởng / Phát triển lá (0.8 - 1.2 kPa)": {"min": 0.8, "max": 1.2},
    "🌸 Ra hoa & Tạo quả (1.2 - 1.6 kPa)": {"min": 1.2, "max": 1.6},
    "⚠️ Ngưỡng stress giới hạn tối đa (> 2.0 kPa)": {"min": 1.6, "max": 2.0}
}

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🌿 Hệ Thống Giám Sát Sinh Học VPD Smart Farm Monitor Pro")
st.caption("Ứng dụng phân tích thời gian thực dữ liệu Áp suất thâm hụt hơi (VPD) tiêu chuẩn nông nghiệp thông minh công nghệ cao Đà Lạt")

tab1, tab2 = st.tabs(["📊 Giám Sát Thời Gian Thực (Realtime)", "📂 Phân Tích Chu Kỳ File Dữ Liệu"])

# ==========================================
# TAB 1: REALTIME MONITORING
# ==========================================
with tab1:
    st.subheader("🤖 Giả Lập Môi Trường Nhà Kính Tự Nhiên")
    
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c1:
        preset_choice = st.selectbox("🎯 Chọn giai đoạn phát triển của cây trồng:", list(PRESETS.keys()))
        vpd_min = PRESETS[preset_choice]["min"]
        vpd_max = PRESETS[preset_choice]["max"]
    with col_c2:
        sim_time = st.slider("⏰ Thay đổi mốc thời gian trong ngày:", min_value=0, max_value=23, value=datetime.now().hour, step=1)
    with col_c3:
        auto_sim = st.checkbox("🔄 Kích hoạt chế độ cập nhật chu kỳ liên tục (Mô phỏng ngẫu nhiên)", value=False)

    now_dt = datetime.now().replace(hour=sim_time, minute=0, second=0, microsecond=0)
    sim_temp, sim_rh = get_weather_by_time(now_dt)
    
    if auto_sim:
        import random
        sim_temp += random.uniform(-1.5, 1.5)
        sim_rh += random.uniform(-4.0, 4.0)
        sim_rh = max(0.0, min(100.0, sim_rh))

    sim_vpd = calculate_vpd(sim_temp, sim_rh)
    sim_dew = calculate_dew_point(sim_temp, sim_rh)

    if not st.session_state.history or st.session_state.history[-1]["Thời Gian"] != now_dt.strftime("%H:%M"):
        st.session_state.history.append({
            "Thời Gian": now_dt.strftime("%H:%M"),
            "Nhiệt độ (°C)": sim_temp,
            "Độ ẩm (%)": sim_rh,
            "VPD (kPa)": sim_vpd,
            "Điểm sương (°C)": sim_dew
        })
        if len(st.session_state.history) > 24:
            st.session_state.history.pop(0)

    st.markdown("---")
    st.subheader("📡 Các Chỉ Số Cảm Biến Hiện Tại")
    
    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    with m_c1:
        st.metric(label="🌡️ Nhiệt độ môi trường", value=f"{sim_temp:.1f} °C")
    with m_c2:
        st.metric(label="💧 Độ ẩm không khí", value=f"{sim_rh:.1f} %")
    with m_c3:
        st.metric(label="📊 Áp suất hơi thâm hụt (VPD)", value=f"{sim_vpd:.2f} kPa")
    with m_c4:
        st.metric(label="❄️ Nhiệt độ điểm sương", value=f"{sim_dew:.1f} °C")

    st.markdown("### 🔍 Đánh Giá Trạng thái Sinh Học & Giải Pháp Điều Khiển Phần Cứng")
    
    plant_matrix_rt = {
        "🌅 Sáng (05h-10h)": (vpd_min, vpd_max),
        "☀️ Trưa (10h-15h)": (vpd_min, vpd_max),
        "🌇 Chiều (15h-19h)": (vpd_min, vpd_max),
        "🌌 Tối (19h-23h)": (vpd_min, vpd_max),
        "🌙 Khuya (23h-05h)": (vpd_min, vpd_max)
    }

    trend_txt, trend_status = predict_vpd_trend_v3(st.session_state.history, sim_time, plant_matrix_rt)
    st.info(f"🔮 Dự báo xu hướng chu kỳ: {trend_txt}")

    if sim_vpd >= vpd_max + 0.5:
        st.markdown("<div class='danger-box-red'>🚨 TRẠNG THÁI KHẨN CẤP: Môi trường QUÁ NÓNG & KHÔ GẮT. Khí khổng của cây đóng chặt, quá trình quang hợp ngừng trệ.<br>👉 GIẢI PHÁP: Kích hoạt xả rèm đỉnh mái, phun sương hạt mịn công suất 100%, bật quạt thông gió tối đa để giải nhiệt gấp.</div>", unsafe_with_html=True)
    elif sim_vpd > vpd_max:
        st.markdown("<div class='danger-box-yellow'>⚠️ CẢNH BÁO SINH HỌC: VPD vượt ngưỡng lý tưởng (Hơi khô). Cây có dấu hiệu mất nước nhẹ.<br>👉 GIẢI PHÁP: Kéo rèm lưới cắt nắng, kích hoạt hệ thống tưới phun sương nhẹ định kỳ giữ ẩm.</div>", unsafe_with_html=True)
    elif sim_vpd < vpd_min - 0.2:
        st.markdown("<div class='danger-box-blue'>🚨 CẢNH BÁO SINH HỌC: Môi trường QUÁ ẨM ƯỚT. Áp suất bão hòa gây đọng nước trên lá, kích thích nấm bệnh phát triển mạnh.<br>👉 GIẢI PHÁP: Tắt toàn bộ hệ thống phun sương/tưới nước, bật hết công suất hệ thống quạt đối lưu không khí.</div>", unsafe_with_html=True)
    elif sim_vpd < vpd_min:
        st.markdown("<div class='danger-box-blue'>⚠️ THÔNG BÁO: Độ ẩm hơi cao. Sự thoát hơi nước qua lá chậm lại, làm giảm khả năng hấp thụ dinh dưỡng.<br>👉 GIẢI PHÁP: Mở rèm hông thông gió tự nhiên, tăng tuần hoàn quạt gió đối lưu.</div>", unsafe_with_html=True)
    else:
        st.markdown("<div class='normal-box'>✅ MÔI TRƯỜNG LÝ TƯỞNG: Chỉ số VPD hoàn hảo. Khí khổng mở tối ưu, cây hấp thụ dinh dưỡng và quang hợp mạnh nhất.<br>👉 GIẢI PHÁP: Duy trì trạng thái vận hành tự động hiện tại. Thỉnh thoảng thông gió nhẹ.</div>", unsafe_with_html=True)

    if st.button("📤 Gửi thông báo khẩn cấp (Realtime) qua Telegram", type="primary", key="btn_rt_tele"):
        if TELE_TOKEN and TELE_CHAT_ID:
            bio_block = get_biological_block(sim_time)
            msg = (
                f"🚨 *CẢNH BÁO GIÁM SÁT REALTIME*\n"
                f"⏰ Thời gian mốc: `{now_dt.strftime('%H:%M')}` ({bio_block})\n"
                f"🌡 Nhiệt độ: `{sim_temp:.1f} °C` | 💧 Độ ẩm: `{sim_rh:.1f} %`\n"
                f"📊 Chỉ số VPD: *{sim_vpd:.2f} kPa* (Ngưỡng chuẩn: {vpd_min}-{vpd_max} kPa)\n"
                f"❄️ Điểm sương: `{sim_dew:.1f} °C`\n"
                f"🔮 Xu hướng: _{trend_txt}_\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
            )
            if sim_vpd >= vpd_max + 0.5:
                msg += "🚨 *Trạng thái:* QUÁ NÓNG KHÔ\n🛠 *Hành động:* Xả rèm đỉnh, phun sương hạt mịn hết công suất, bật quạt hút nhiệt!"
            elif sim_vpd > vpd_max:
                msg += "⚠️ *Trạng thái:* HƠI KHÔ\n🛠 *Hành động:* Kéo lưới che nắng, kích hoạt phun sương nhẹ giữ ẩm."
            elif sim_vpd < vpd_min - 0.2:
                msg += "🔵 *Trạng thái:* QUÁ ẨM\n🛠 *Hành động:* TẮT phun sương, bật quạt đối lưu, kiểm tra đọng nước."
            elif sim_vpd < vpd_min:
                msg += "⚠️ *Trạng thái:* HƠI ẨM\n🛠 *Hành động:* Mở thoáng rèm hông, bật quạt thông gió nhẹ."
            else:
                msg += "✅ *Trạng thái:* LÝ TƯỞNG\n🛠 *Hành động:* Giữ nguyên hệ thống tự động, duy trì thông gió."
            
            msg += "\n\n🌿 _Hệ thống giám sát Smart Farm Autonomous_"
            
            success = send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, msg)
            if success:
                st.success("✅ Đã gửi thông báo Realtime tới Telegram thành công!")
            else:
                st.error("❌ Gửi tin nhắn thất bại. Vui lòng kiểm tra Token hoặc Chat ID.")

    st.markdown("---")
    st.subheader("📈 Biểu Đồ Diễn Biến Dữ Liệu Trong Chu Kỳ Gần Nhất")
    df_rt = pd.DataFrame(st.session_state.history)
    if not df_rt.empty:
        df_rt['Hiển thị Giờ'] = df_rt['Thời Gian']
        
        c_rt_1, c_rt_2 = st.columns(2)
        with c_rt_1:
            st.markdown("#### Diễn biến chỉ số VPD")
            st.altair_chart(draw_vpd_chart(df_rt, vpd_min, vpd_max), use_container_width=True)
        with c_rt_2:
            st.markdown("#### Kết hợp Nhiệt độ & Độ ẩm song song")
            st.altair_chart(draw_combined_temp_humidity_chart(df_rt), use_container_width=True)
            
        st.markdown("#### 🗒️ Bảng tổng hợp nhật ký dữ liệu realtime")
        st.dataframe(df_rt, use_container_width=True, hide_index=True)

# ==========================================
# TAB 2: FILE ANALYTICS CHU KỲ
# ==========================================
with tab2:
    st.subheader("📂 Tải Lên Nhật Ký Dữ Liệu Farm (Hỗ trợ: CSV, Excel XLSX)")
    st.markdown("Yêu cầu các cột dữ liệu bắt buộc gồm: `Thời Gian` (định dạng YYYY-MM-DD HH:MM hoặc HH:MM), `Nhiệt độ (°C)`, `Độ ẩm (%)`")
    
    uploaded_file = st.file_uploader("Chọn tệp nhật ký dữ liệu từ cảm biến của bạn:", type=["csv", "xlsx"])
    
    f_preset_choice = st.selectbox("🎯 Mô hình cây trồng áp dụng cho tệp dữ liệu:", list(PRESETS.keys()), key="file_preset")
    f_vpd_min = PRESETS[f_preset_choice]["min"]
    f_vpd_max = PRESETS[f_preset_choice]["max"]

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_f = pd.read_csv(uploaded_file)
            else:
                df_f = pd.read_excel(uploaded_file)
                
            required_cols = ["Thời Gian", "Nhiệt độ (°C)", "Độ ẩm (%)"]
            missing_cols = [c for c in required_cols if c not in df_f.columns]
            
            if missing_cols:
                st.error(f"❌ Tệp tải lên thiếu các cột bắt buộc sau: {missing_cols}")
                st.stop()

            df_f["VPD (kPa)"] = df_f.apply(lambda r: calculate_vpd(r["Nhiệt độ (°C)"], r["Độ ẩm (%)"]), axis=1)
            df_f["Điểm sương (°C)"] = df_f.apply(lambda r: calculate_dew_point(r["Nhiệt độ (°C)"], r["Độ ẩm (%)"]), axis=1)

            def extract_hour(val):
                try:
                    dt_obj = pd.to_datetime(val)
                    return dt_obj.hour
                except:
                    try:
                        return int(str(val).split(":")[0])
                    except:
                        return 12

            df_f["Giờ"] = df_f["Thời Gian"].apply(extract_hour)
            df_f["Buổi"] = df_f["Giờ"].apply(get_biological_block)
            df_f["Hiển thị Giờ"] = df_f["Thời Gian"].apply(lambda x: str(x).split(" ")[-1][:5])

            st.success(f"✅ Xử lý thành công tệp `{uploaded_file.name}` với {len(df_f)} dòng dữ liệu cảm biến.")

            # Tính toán số giờ stress của cây trồng dựa trên file dữ liệu
            stress_hours_results = calculate_plant_stress_hours(df_f, f_vpd_min, f_vpd_max)
            
            st.markdown("### 📊 Thống Kê Tổng Quan Chu Kỳ Sinh Học File")
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            with s_col1:
                st.metric("📈 VPD Cao Nhất", f"{df_f['VPD (kPa)'].max():.2f} kPa")
            with s_col2:
                st.metric("📉 VPD Thấp Nhất", f"{df_f['VPD (kPa)'].min():.2f} kPa")
            with s_col3:
                st.metric("📊 VPD Trung Bình", f"{df_f['VPD (kPa)'].mean():.2f} kPa")
            with s_col4:
                st.metric("⚠️ Số mốc Cây bị Stress", f"{stress_hours_results['total_stress_records']} mốc")

            # Hiển thị phân tích chi tiết mức độ stress
            st.markdown("#### 🔬 Báo cáo mức độ stress chi tiết của cây trồng:")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.info(f"🔵 **Môi trường Quá Ẩm (< {f_vpd_min} kPa):** {stress_hours_results['under_vpd_records']} mốc dữ liệu")
            with sc2:
                st.success(f"✅ **Môi trường Lý Tưởng ({f_vpd_min} - {f_vpd_max} kPa):** {stress_hours_results['optimal_records']} mốc dữ liệu")
            with sc3:
                st.warning(f"🔴 **Môi trường Quá Khô (> {f_vpd_max} kPa):** {stress_hours_results['over_vpd_records']} mốc dữ liệu")

            st.markdown("---")
            st.subheader("📉 Biểu Đồ Phân Tích Toàn Diện Từ Nhật Ký")
            
            c_f_1, c_f_2 = st.columns(2)
            with c_f_1:
                st.markdown("#### Diễn biến chỉ số VPD trong file")
                st.altair_chart(draw_vpd_chart(df_f, f_vpd_min, f_vpd_max), use_container_width=True)
            with c_f_2:
                st.markdown("#### Diễn biến cấu trúc Nhiệt độ & Độ ẩm")
                st.altair_chart(draw_combined_temp_humidity_chart(df_f), use_container_width=True)

            st.markdown("---")
            st.subheader("🧮 Trích Xuất Báo Cáo Ma Trận Khung Giờ Sinh Học (Biological Blocks)")
            
            plant_matrix_file = {
                "🌅 Sáng (05h-10h)": (f_vpd_min, f_vpd_max),
                "☀️ Trưa (10h-15h)": (f_vpd_min, f_vpd_max),
                "🌇 Chiều (15h-19h)": (f_vpd_min, f_vpd_max),
                "🌌 Tối (19h-23h)": (f_vpd_min, f_vpd_max),
                "🌙 Khuya (23h-05h)": (f_vpd_min, f_vpd_max)
            }
            
            df_block_report = analyze_day_by_blocks_rt(df_f, plant_matrix_file)
            
            if df_block_report is not None and not df_block_report.empty:
                st.markdown("#### Bảng phân tích và đề xuất giải pháp kỹ thuật theo từng Buổi Sinh Học:")
                st.dataframe(df_block_report, use_container_width=True, hide_index=True)
                
                if st.button("📤 Gửi báo cáo ma trận qua Telegram", type="primary", key="btn_send_file_tele"):
                    if TELE_TOKEN and TELE_CHAT_ID:
                        file_tele_msg = f"📂 *BÁO CÁO CHU KỲ FILE*\n📦 File: `{uploaded_file.name}`\n🎯 Mô hình: *{f_preset_choice}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
                        for _, r_data in df_block_report.iterrows():
                            file_tele_msg += f"Buổi *{r_data['Khoảng Buổi']}*\n▪️ Môi trường: {r_data['Nhiệt độ TB']} | {r_data['Độ ẩm TB']}\n▪️ VPD TB: *{r_data['VPD Trung Bình']}*\n▪️ Đánh giá: *{r_data['Đánh giá sinh học']}*\n▪️ Giải pháp: {r_data['Giải pháp kỹ thuật']}\n────────────────────\n"
                        file_tele_msg += f"\n📊 _Hệ thống tự động chấm điểm sinh học VPD Smart Farm_"
                        success = send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, file_tele_msg)
                        if success: 
                            st.success("✅ Đã gửi toàn bộ dữ liệu báo cáo qua Telegram thành công!")
            else:
                st.info("Chưa có đủ dữ liệu thích hợp để bóc tách chu kỳ buổi.")

        except Exception as err:
            st.error(f"❌ Đã xảy ra lỗi trong quá trình xử lý tệp tin: {err}")
