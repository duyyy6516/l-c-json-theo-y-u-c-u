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

# Áp dụng cấu hình CSS an toàn tránh lỗi xử lý chuỗi trên hệ thống mới Python 3.14+
st.html(
    """
    <style>
    html, body, [data-testid='stAppViewContainer'] { overflow-y: auto !important; scroll-behavior: smooth; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; padding-left: 1.5rem; padding-right: 1.5rem; }
    .danger-box-red { padding: 12px; background-color: #C0392B; border-left: 6px solid #17202A; color: #FFFFFF; border-radius: 4px; margin-bottom: 10px; font-weight: bold; }
    .danger-box-blue { padding: 12px; background-color: #2980B9; border-left: 6px solid #1B4F72; color: #FFFFFF; border-radius: 4px; margin-bottom: 10px; font-weight: bold; }
    .danger-box-yellow { padding: 12px; background-color: #D35400; border-left: 6px solid #2C3E50; color: #FFFFFF; border-radius: 4px; margin-bottom: 10px; font-weight: bold; }
    </style>
    """
)

st.title("🌿 VPD Smart Farm Monitor Pro — Hệ Thống Giám Sát Vi Khí Hậu Thông Minh")
st.write("Giải pháp phân tích chỉ số Thâm hụt áp suất hơi (VPD) nông nghiệp công nghệ cao.")

# CHIA TÁCH WEB THÀNH 2 MỤC ĐỘC LẬP: REALTIME VS ĐỌC FILE JSON
tab_realtime, tab_json = st.tabs(["⚡ PHÂN TÍCH VPD REALTIME", "📂 ĐỌC VÀ XỬ LÝ FILE JSON"])

# Hàm tiện ích lấy ma trận sinh học cây trồng chuẩn hóa tương thích với analytics.py của bạn
def get_plant_matrix_by_choice(choice):
    if "Dâu Tây" in choice:
        return {
            "🌅 Sáng (05h-10h)": [0.6, 1.0],
            "☀️ Trưa (10h-15h)": [0.9, 1.2],
            "🌇 Chiều (15h-19h)": [0.7, 1.1],
            "🌌 Tối (19h-23h)": [0.5, 0.8],
            "🌙 Khuya (23h-05h)": [0.3, 0.6]
        }
    elif "Hoa Hồng" in choice:
        return {
            "🌅 Sáng (05h-10h)": [0.7, 1.1],
            "☀️ Trưa (10h-15h)": [1.0, 1.4],
            "🌇 Chiều (15h-19h)": [0.8, 1.2],
            "🌌 Tối (19h-23h)": [0.5, 0.9],
            "🌙 Khuya (23h-05h)": [0.4, 0.7]
        }
    else:  # Cà chua
        return {
            "🌅 Sáng (05h-10h)": [0.6, 1.0],
            "☀️ Trưa (10h-15h)": [1.0, 1.3],
            "🌇 Chiều (15h-19h)": [0.7, 1.2],
            "🌌 Tối (19h-23h)": [0.5, 0.8],
            "🌙 Khuya (23h-05h)": [0.3, 0.6]
        }

# =====================================================================
# MỤC 1: PHÂN TÍCH VPD REALTIME 
# =====================================================================
with tab_realtime:
    st.header("⚡ Trạm Mô Phỏng & Giám Sát Môi Trường Realtime")
    
    col_left, col_right = st.columns([1, 3])
    
    with col_left:
        st.subheader("⚙️ Cấu Hình Mô Phỏng")
        preset_choice = st.selectbox(
            "Chọn loại cây trồng mục tiêu:",
            ["🍓 Dâu Tây Tây Nguyên (VPD tối ưu: 0.6 - 1.2)", 
             "🌹 Hoa Hồng Nhà Kính (VPD: 0.8 - 1.4)", 
             "🍅 Cà Chua Công Nghệ Cao (VPD: 0.7 - 1.3)"],
            key="sb_plant_realtime"
        )
        
        current_time = datetime.now()
        sim_hour = st.slider("Mô phỏng giờ trong ngày:", 0, 23, current_time.hour, key="sl_hour_rt")
        sim_minute = st.slider("Mô phỏng phút:", 0, 59, current_time.minute, key="sl_min_rt")
        
        target_dt = current_time.replace(hour=sim_hour, minute=sim_minute, second=0, microsecond=0)
        temp_sim, rh_sim = get_weather_by_time(target_dt)
        
        st.markdown("---")
        st.markdown(f"**⏰ Thời gian giả lập:** `{target_dt.strftime('%H:%M')}`")
        st.markdown(f"**🌡️ Nhiệt độ nền:** `{temp_sim:.1f} °C`")
        st.markdown(f"**💦 Độ ẩm nền:** `{rh_sim:.1f} %`")
        
        vpd_sim = calculate_vpd(temp_sim, rh_sim)
        current_block = get_biological_block(sim_hour)
        
        current_matrix = get_plant_matrix_by_choice(preset_choice)
        vpd_min, vpd_max = current_matrix[current_block]

    with col_right:
        st.subheader("📊 Kết Quả Phân Tích Chỉ Số Vi Khí Hậu")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Nhiệt Độ", f"{temp_sim:.1f} °C")
        m_col2.metric("Độ Ẩm Không Khí", f"{rh_sim:.1f} %")
        m_col3.metric("Điểm Sương (Dew Point)", f"{calculate_dew_point(temp_sim, rh_sim):.1f} °C")
        m_col4.metric("Chỉ Số VPD Hiện Tại", f"{vpd_sim:.2f} kPa")
        
        history_sim = [
            {"VPD (kPa)": calculate_vpd(*get_weather_by_time(target_dt - timedelta(minutes=30)))},
            {"VPD (kPa)": calculate_vpd(*get_weather_by_time(target_dt - timedelta(minutes=15)))},
            {"VPD (kPa)": vpd_sim}
        ]
        trend_msg, trend_status = predict_vpd_trend_v3(history_sim, sim_hour, current_matrix)
        st.info(f"🔮 **Xu hướng biến động kế tiếp:** {trend_msg}")
        
        if vpd_sim > vpd_max:
            st.html(f"<div class='danger-box-red'>🚨 CẢNH BÁO NGUY HIỂM: VPD ({vpd_sim:.2f} kPa) vượt ngưỡng tối ưu buổi ({vpd_max} kPa) cho {preset_choice.split()[0]}. Cây trồng đang bị stress nhiệt/khô nghiêm trọng!</div>")
        elif vpd_sim < vpd_min:
            st.html(f"<div class='danger-box-blue'>🚨 CẢNH BÁO NGUY HIỂM: VPD ({vpd_sim:.2f} kPa) thấp hơn mức tối thiểu ({vpd_min} kPa). Nguy cơ đọng sương, nấm bệnh bùng phát!</div>")
        elif (vpd_max - 0.1 <= vpd_sim <= vpd_max) or (vpd_min <= vpd_sim <= vpd_min + 0.1):
            st.html(f"<div class='danger-box-yellow'>⚠️ CẢNH BÁO SỚM (EARLY WARNING): VPD ({vpd_sim:.2f} kPa) đang tiệm cận biên giới nguy hiểm vùng sinh học. Hãy chú ý giám sát!</div>")
        else:
            st.success("🟩 Môi trường lý tưởng! Chỉ số vi khí hậu đang nằm trong dải phát triển sinh sinh học tối ưu của cây.")

        # Tạo tập dữ liệu lịch sử tuần hoàn 24h đầy đủ
        records_24h = []
        base_today = datetime.now().replace(hour=0, minute=0, second=0)
        for h in range(24):
            for m in [0, 30]:
                dt_loop = base_today + timedelta(hours=h, minutes=m)
                t_l, r_l = get_weather_by_time(dt_loop)
                # Đảm bảo gán thêm cột 'Buổi' để tương thích tuyệt đối với hàm gộp groupby() của analytics.py
                records_24h.append({
                    "Hiển thị Giờ": dt_loop.strftime("%H:%M"),
                    "Nhiệt độ (°C)": t_l,
                    "Độ ẩm (%)": r_l,
                    "VPD (kPa)": calculate_vpd(t_l, r_l),
                    "Giờ": h,
                    "Buổi": get_biological_block(h)
                })
        df_sim_24h = pd.DataFrame(records_24h)
        
        st.altair_chart(draw_vpd_chart(df_sim_24h, vpd_min, vpd_max), use_container_width=True)
        st.altair_chart(draw_combined_temp_humidity_chart(df_sim_24h), use_container_width=True)
        
        st.subheader("📋 Phân Tích Khối Chu Kỳ & Đề Xuất Thiết Bị")
        
        # SỬA LỖI TYPEERROR: Thực hiện bọc try-except an toàn, đồng thời đảm bảo cấu trúc cột đầu vào luôn có 'Buổi'
        try:
            df_report_rt = analyze_day_by_blocks_rt(df_sim_24h, current_matrix)
            st.dataframe(df_report_rt, use_container_width=True, hide_index=True)
        except Exception as report_err:
            st.error(f"⚠️ Không thể trích xuất bảng báo cáo phân tích tự động. Chi tiết lỗi hệ thống: {str(report_err)}")
        
        if st.button("📤 Phát Lệnh Cảnh Báo Khẩn Cấp Lên Telegram", type="primary", key="btn_tele_realtime"):
            if TELE_TOKEN and TELE_CHAT_ID:
                alert_text = (
                    f"⚠️ *VPD SMART FARM EMERGENCY ALERT*\\n"
                    f"⏰ Giờ giả lập: `{target_dt.strftime('%H:%M')}`\\n"
                    f"🎯 Đối tượng: {preset_choice.split()[0]}\\n"
                    f"📊 Thông số mốc: {temp_sim:.1f}°C | {rh_sim}%\\n"
                    f"📉 *Chỉ số VPD: {vpd_sim:.2f} kPa* (Ngưỡng chuẩn: {vpd_min}-{vpd_max} kPa)\\n"
                    f"⚡ Trạng thái: *{ '🔴 Nguy cơ stress khô' if vpd_sim > vpd_max else '🔵 Nguy cơ đọng sương nấm' if vpd_sim < vpd_min else '🟩 Bình thường lý tưởng' }*\\n"
                    f"🔮 Xu hướng: _{trend_msg}_"
                )
                if send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, alert_text):
                    st.success("✅ Đã phát lệnh gửi bức điện thông tin khẩn cấp qua Bot Telegram thành công!")
                else:
                    st.error("❌ Kết nối API Telegram thất bại.")

# =====================================================================
# MỤC 2: ĐỌC VÀ XỬ LÝ FILE JSON 
# =====================================================================
with tab_json:
    st.header("📂 Hệ Thống Phân Tích Chỉ Số Từ Tệp Tin JSON")
    st.write("Tải lên tệp tin cấu trúc `.json` chứa lịch sử dữ liệu cảm biến IoT để trích xuất báo cáo chu kỳ sinh học và vẽ biểu đồ tương thích.")

    uploaded_json = st.file_uploader("Chọn file dữ liệu IoT cần phân tích (.json):", type=["json"], key="uploader_json_section")

    if uploaded_json is not None:
        try:
            json_data = json.load(uploaded_json)
            
            raw_records = []
            if isinstance(json_data, list):
                raw_records = json_data
            elif isinstance(json_data, dict) and "data" in json_data:
                raw_records = json_data["data"]
            else:
                st.error("❌ Cấu trúc dữ liệu JSON không hợp lệ. File cần chứa một danh sách (mảng) các bản ghi cảm biến.")
            
            if raw_records:
                records_parsed = []
                for idx, item in enumerate(raw_records):
                    temp = float(item.get("temperature", item.get("Nhiệt độ (°C)", item.get("Nhiệt độ", 25.0))))
                    rh = float(item.get("humidity", item.get("Độ ẩm (%)", item.get("Độ ẩm", 70.0))))
                    ts_str = item.get("timestamp", item.get("Hiển thị Giờ", item.get("Thời gian")))
                    
                    if ts_str:
                        ts_str = str(ts_str)
                        if ":" in ts_str and len(ts_str) <= 5:
                            display_time = ts_str
                            try:
                                hour_val = int(ts_str.split(":")[0])
                            except:
                                hour_val = 12
                        else:
                            try:
                                dt_parsed = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                                display_time = dt_parsed.strftime("%H:%M")
                                hour_val = dt_parsed.hour
                            except:
                                display_time = ts_str[:5]
                                hour_val = 12
                    else:
                        hour_val = int((idx * 24 / len(raw_records)) % 24)
                        display_time = f"{hour_val:02d}:00"
                    
                    vpd_val = calculate_vpd(temp, rh)
                    
                    # Luôn gán kèm cột 'Buổi' tương tự để bảo vệ dữ liệu khỏi lỗi TypeError
                    records_parsed.append({
                        "Hiển thị Giờ": display_time,
                        "Nhiệt độ (°C)": temp,
                        "Độ ẩm (%)": rh,
                        "VPD (kPa)": vpd_val,
                        "Giờ": hour_val,
                        "Buổi": get_biological_block(hour_val)
                    })
                
                df_json = pd.DataFrame(records_parsed)
                st.success(f"📥 Nạp dữ liệu thành công! Đã bóc tách được `{len(df_json)}` mốc thời gian từ file JSON.")
                
                st.subheader("🎯 Cấu Hình Đối Chiếu Sinh Học")
                json_preset_choice = st.selectbox(
                    "Chọn loại cây trồng mục tiêu để phân tích dữ liệu JSON:",
                    ["🍓 Dâu Tây Tây Nguyên (VPD tối ưu: 0.6 - 1.2)", 
                     "🌹 Hoa Hồng Nhà Kính (VPD: 0.8 - 1.4)", 
                     "🍅 Cà Chua Công Nghệ Cao (VPD: 0.7 - 1.3)"],
                    key="sb_plant_json_section"
                )
                json_matrix = get_plant_matrix_by_choice(json_preset_choice)
                
                json_stress_hours, _ = calculate_plant_stress_hours(df_json, json_matrix)
                st.warning(f"⚠️ **Thống kê tích lũy JSON:** Tổng thời lượng cây chịu áp lực Stress VPD nguy hại: **{json_stress_hours:.1f} giờ**")
                
                st.subheader("📊 Số Liệu Cảm Biến Trung Bình Chu Kỳ File")
                m_j1, m_j2, m_j3, m_j4 = st.columns(4)
                m_j1.metric("Nhiệt Độ TB", f"{df_json['Nhiệt độ (°C)'].mean():.1f} °C")
                m_j2.metric("Độ Ẩm Không Khí TB", f"{df_json['Độ ẩm (%)'].mean():.1f} %")
                m_j3.metric("Điểm Sương TB", f"{calculate_dew_point(df_json['Nhiệt độ (°C)'].mean(), df_json['Độ ẩm (%)'].mean()):.1f} °C")
                m_j4.metric("VPD Trung Bình", f"{df_json['VPD (kPa)'].mean():.2f} kPa")
                
                st.subheader("📈 Đồ Thị Diễn Biến Chỉ Số Vi Khí Hậu Từ File JSON")
                st.altair_chart(draw_vpd_chart(df_json), use_container_width=True)
                st.altair_chart(draw_combined_temp_humidity_chart(df_json), use_container_width=True)
                
                st.subheader("📋 Báo Cáo Phân Tích Chu Kỳ Buổi & Giải Pháp Kỹ Thuật")
                
                try:
                    df_json_report = analyze_day_by_blocks_rt(df_json, json_matrix)
                    st.dataframe(df_json_report, use_container_width=True, hide_index=True)
                    
                    # Chỉ hiện nút gửi Telegram khi bảng dữ liệu phân tích thành công
                    if st.button("📤 Gửi Toàn Bộ Báo Cáo JSON Qua Telegram", type="primary", key="btn_tele_json_section"):
                        if TELE_TOKEN and TELE_CHAT_ID:
                            json_tele_msg = (
                                f"📂 *BÁO CÁO CHU KỲ IOT (FILE JSON)*\\n"
                                f"📦 Tên file: `{uploaded_json.name}`\\n"
                                f"🎯 Đối tượng: *{json_preset_choice.split()[0]}*\\n"
                                f"⚠️ Tích lũy Stress: *{json_stress_hours:.1f} giờ*\\n"
                                f"━━━━━━━━━━━━━━━━━━━━\\n\\n"
                            )
                            for _, r_data in df_json_report.iterrows():
                                json_tele_msg += (
                                    f"Buổi *{r_data['Khoảng Buổi']}*\\n"
                                    f"▪️ Môi trường: {r_data['Nhiệt độ TB']} | {r_data['Độ ẩm TB']}\\n"
                                    f"▪️ VPD TB: *{r_data['VPD Trung Bình']}*\\n"
                                    f"▪️ Đánh giá: *{r_data['Đánh giá sinh học']}*\\n"
                                    f"▪️ Giải pháp: {r_data['Giải pháp kỹ thuật']}\\n"
                                    f"────────────────────\\n"
                                )
                            json_tele_msg += "\\n📊 _Hệ thống tự động xử lý và kết xuất dữ liệu thành công._"
                            
                            if send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, json_tele_msg):
                                st.success("✅ Đã truyền dữ liệu báo cáo tệp tin JSON qua Telegram Bot thành công!")
                            else:
                                st.error("❌ Không thể kết nối tới API Telegram.")
                except Exception as json_report_err:
                    st.error(f"⚠️ Không thể tạo bảng phân tích chu kỳ từ tệp JSON này. Lỗi: {str(json_report_err)}")
            
        except Exception as err:
            st.error(f"❌ Cấu trúc file JSON bị lỗi cú pháp hoặc sai định dạng. Chi tiết lỗi: {str(err)}")
