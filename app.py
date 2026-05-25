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

# SỬA LỖI CHUỖI DÀI PYTHON 3.14+: Tách nhỏ CSS thành list để nối chuỗi an toàn
css_styles = [
    "<style>",
    "html, body, [data-testid='stAppViewContainer'] { overflow-y: auto !important; scroll-behavior: smooth; }",
    ".block-container { padding-top: 1rem; padding-bottom: 2rem; padding-left: 1.5rem; padding-right: 1.5rem; }",
    ".danger-box-red { padding: 12px; background-color: #C0392B; border-left: 6px solid #17202A; color: #FFFFFF; border-radius: 4px; margin-bottom: 10px; font-weight: bold; }",
    ".danger-box-blue { padding: 12px; background-color: #2980B9; border-left: 6px solid #1B4F72; color: #FFFFFF; border-radius: 4px; margin-bottom: 10px; font-weight: bold; }",
    ".danger-box-yellow { padding: 12px; background-color: #D35400; border-left: 6px solid #2C3E50; color: #FFFFFF; border-radius: 4px; margin-bottom: 10px; font-weight: bold; }",
    "</style>"
]
st.markdown("".join(css_styles), unsafe_allow_unsafe_html=True)

st.title("🌿 VPD Smart Farm Monitor Pro — Hệ Thống Giám Sát Vi Khí Hậu Thông Minh")
st.write("Giải pháp phân tích chỉ số Thâm hụt áp suất hơi (VPD) thời gian thực và quản lý chu kỳ sinh học tối ưu nông nghiệp.")

# Khởi tạo tabs bao gồm cả chức năng đọc file JSON mới
tab1, tab2, tab3 = st.tabs(["MÔ PHỎNG & XEM REALTIME", "QUÉT FILE IOT HỆ THỐNG", "📂 PHÂN TÍCH TỪ FILE JSON"])

# 💡 HÀM TIỆN ÍCH DÙNG CHUNG CHO CẢ TAB 1 VÀ TAB 3 ĐỂ LẤY NGƯỠNG CÂY TRỒNG
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

# ==========================================
# TAB 1: MÔ PHỎNG & XEM REALTIME
# ==========================================
with tab1:
    st.header("⚡ Trạm Mô Phỏng Môi Trường Đà Lạt Realtime")
    
    col_left, col_right = st.columns([1, 3])
    
    with col_left:
        st.subheader("⚙️ Cấu Hình Mô Phỏng")
        preset_choice = st.selectbox(
            "Chọn loại cây trồng mục tiêu:",
            ["🍓 Dâu Tây Tây Nguyên (VPD tối ưu: 0.6 - 1.2)", 
             "🌹 Hoa Hồng Nhà Kính (VPD: 0.8 - 1.4)", 
             "🍅 Cà Chua Công Nghệ Cao (VPD: 0.7 - 1.3)"],
            key="sb_plant_tab1"
        )
        
        current_time = datetime.now()
        sim_hour = st.slider("Mô phỏng giờ trong ngày:", 0, 23, current_time.hour)
        sim_minute = st.slider("Mô phỏng phút:", 0, 59, current_time.minute)
        
        target_dt = current_time.replace(hour=sim_hour, minute=sim_minute, second=0, microsecond=0)
        temp_sim, rh_sim = get_weather_by_time(target_dt)
        
        st.markdown("---")
        st.markdown(f"**⏰ Thời gian giả lập:** `{target_dt.strftime('%H:%M')}`")
        st.markdown(f"**🌡️ Nhiệt độ nền:** `{temp_sim:.1f} °C`")
        st.markdown(f"**💦 Độ ẩm nền:** `{rh_sim:.1f} %`")
        
        vpd_sim = calculate_vpd(temp_sim, rh_sim)
        current_block = get_biological_block(sim_hour)
        
        # Lấy ma trận ngưỡng tối ưu cho cây trồng
        current_matrix = get_plant_matrix_by_choice(preset_choice)
        vpd_min, vpd_max = current_matrix[current_block]

    with col_right:
        st.subheader("📊 Kết Quả Phân Tích Chỉ Số Vi Khí Hậu")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Nhiệt Độ", f"{temp_sim:.1f} °C")
        m_col2.metric("Độ Ẩm Không Khí", f"{rh_sim:.1f} %")
        m_col3.metric("Điểm Sương (Dew Point)", f"{calculate_dew_point(temp_sim, rh_sim):.1f} °C")
        m_col4.metric("Chỉ Số VPD Hiện Tại", f"{vpd_sim:.2f} kPa")
        
        # Tạo chuỗi lịch sử 3 mốc gần nhất để chạy thuật toán dự báo xu hướng
        history_sim = [
            {"VPD (kPa)": calculate_vpd(*get_weather_by_time(target_dt - timedelta(minutes=30)))},
            {"VPD (kPa)": calculate_vpd(*get_weather_by_time(target_dt - timedelta(minutes=15)))},
            {"VPD (kPa)": vpd_sim}
        ]
        trend_msg, trend_status = predict_vpd_trend_v3(history_sim, sim_hour, current_matrix)
        st.info(f"🔮 **Xu hướng biến động kế tiếp:** {trend_msg}")
        
        # Kiểm tra ngưỡng nguy hiểm khẩn cấp hoặc cảnh báo sớm
        if vpd_sim > vpd_max:
            st.markdown(f"<div class='danger-box-red'>🚨 CẢNH BÁO NGUY HIỂM: VPD ({vpd_sim:.2f} kPa) vượt ngưỡng tối ưu buổi ({vpd_max} kPa) cho {preset_choice.split()[0]}. Cây trồng đang bị stress nhiệt/khô nghiêm trọng!</div>", unsafe_allow_unsafe_html=True)
        elif vpd_sim < vpd_min:
            st.markdown(f"<div class='danger-box-blue'>🚨 CẢNH BÁO NGUY HIỂM: VPD ({vpd_sim:.2f} kPa) thấp hơn mức tối thiểu ({vpd_min} kPa). Nguy cơ đọng sương, nấm bệnh bùng phát!</div>", unsafe_allow_unsafe_html=True)
        elif (vpd_max - 0.1 <= vpd_sim <= vpd_max) or (vpd_min <= vpd_sim <= vpd_min + 0.1):
            st.markdown(f"<div class='danger-box-yellow'>⚠️ CẢNH BÁO SỚM (EARLY WARNING): VPD ({vpd_sim:.2f} kPa) đang tiệm cận biên giới nguy hiểm vùng sinh học. Hãy chú ý giám sát!</div>", unsafe_allow_unsafe_html=True)
        else:
            st.success("🟩 Môi trường lý tưởng! Chỉ số vi khí hậu đang nằm trong dải phát triển sinh sinh học tối ưu của cây.")

        # Xây dựng dataframe giả định 24h để hiển thị đồ thị trực quan giống dữ liệu chạy thật
        records_24h = []
        base_today = datetime.now().replace(hour=0, minute=0, second=0)
        for h in range(24):
            for m in [0, 30]:
                dt_loop = base_today + timedelta(hours=h, minutes=m)
                t_l, r_l = get_weather_by_time(dt_loop)
                records_24h.append({
                    "Hiển thị Giờ": dt_loop.strftime("%H:%M"),
                    "Nhiệt độ (°C)": t_l,
                    "Độ ẩm (%)": r_l,
                    "VPD (kPa)": calculate_vpd(t_l, r_l),
                    "Giờ": h
                })
        df_sim_24h = pd.DataFrame(records_24h)
        
        # Vẽ các đồ thị altair tương tác
        st.altair_chart(draw_vpd_chart(df_sim_24h, vpd_min, vpd_max), use_container_width=True)
        st.altair_chart(draw_combined_temp_humidity_chart(df_sim_24h), use_container_width=True)
        
        # Tạo bảng thống kê tổng quát 5 khối sinh học trong ngày
        st.subheader("📋 Phân Tích Khối Chu Kỳ & Đề Xuất Thiết Bị")
        df_report_rt = analyze_day_by_blocks_rt(df_sim_24h, current_matrix)
        st.dataframe(df_report_rt, use_container_width=True, hide_index=True)
        
        if st.button("📤 Phát Lệnh Cảnh Báo Khẩn Cấp Lên Telegram", type="primary", key="btn_tele_tab1"):
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

# ==========================================
# TAB 2: QUÉT FILE IOT HỆ THỐNG (.XLSX/.CSV)
# ==========================================
with tab2:
    st.header("📂 Hệ Thống Quét Lịch Sử Nhật Ký Thiết Bị Môi Trường")
    st.write("Tải lên tệp nhật ký cảm biến thu thập từ phần cứng (hỗ trợ Excel hoặc CSV) để phân tích tích lũy số giờ stress.")
    
    uploaded_file = st.file_uploader("Chọn file dữ liệu nhật ký IoT:", type=["xlsx", "csv"], key="uploader_tab2")
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_file = pd.read_csv(uploaded_file)
            else:
                df_file = pd.read_excel(uploaded_file)
                
            required_cols = ["Nhiệt độ (°C)", "Độ ẩm (%)", "Hiển thị Giờ"]
            if all(c in df_file.columns for c in required_cols):
                if "VPD (kPa)" not in df_file.columns:
                    df_file["VPD (kPa)"] = df_file.apply(lambda row: calculate_vpd(row["Nhiệt độ (°C)"], row["Độ ẩm (%)"]), axis=1)
                if "Giờ" not in df_file.columns:
                    df_file["Giờ"] = pd.to_datetime(df_file["Hiển thị Giờ"], format="%H:%M", errors='coerce').dt.hour
                    df_file["Giờ"] = df_file["Giờ"].fillna(12).astype(int)
                
                st.success(f"📥 Đọc file thành công! Tìm thấy `{len(df_file)}` mốc thời gian ghi nhận cảm biến.")
                
                f_preset_choice = st.selectbox(
                    "Chọn mô hình cây trồng mục tiêu để quét file:",
                    ["🍓 Dâu Tây Tây Nguyên (VPD tối ưu: 0.6 - 1.2)", "🌹 Hoa Hồng Nhà Kính (VPD: 0.8 - 1.4)", "🍅 Cà Chua Công Nghệ Cao (VPD: 0.7 - 1.3)"],
                    key="sb_plant_tab2"
                )
                file_matrix = get_plant_matrix_by_choice(f_preset_choice)
                
                # Tính tổng số giờ stress cây trồng
                stress_hours, stress_msg_file = calculate_plant_stress_hours(df_file, file_matrix)
                st.warning(f"⚠️ **Thống kê tích lũy:** Tổng số giờ cây bị rơi vào trạng thái Stress VPD: **{stress_hours:.1f} giờ**")
                
                st.altair_chart(draw_vpd_chart(df_file), use_container_width=True)
                st.altair_chart(draw_combined_temp_humidity_chart(df_file), use_container_width=True)
                
                st.subheader("📋 Báo Cáo Phân Tích Trích Xuất File")
                df_block_report = analyze_day_by_blocks_rt(df_file, file_matrix)
                st.dataframe(df_block_report, use_container_width=True, hide_index=True)
                
                if st.button("📤 Gửi báo cáo ma trận qua Telegram", type="primary", key="btn_send_file_tele"):
                    if TELE_TOKEN and TELE_CHAT_ID:
                        file_tele_msg = f"📂 *BÁO CÁO CHU KỲ FILE*\\n📦 File: `{uploaded_file.name}`\\n🎯 Mô hình: *{f_preset_choice}*\\n━━━━━━━━━━━━━━━━━━━━\\n\\n"
                        for _, r_data in df_block_report.iterrows():
                            file_tele_msg += f"Buổi *{r_data['Khoảng Buổi']}*\\n▪️ Môi trường: {r_data['Nhiệt độ TB']} | {r_data['Độ ẩm TB']}\\n▪️ VPD TB: *{r_data['VPD Trung Bình']}*\\n▪️ Đánh giá: *{r_data['Đánh giá sinh học']}*\\n▪️ Giải pháp: {r_data['Giải pháp kỹ thuật']}\\n────────────────────\\n"
                        file_tele_msg += "\\n📊 _Hệ thống tự động chấm điểm sinh học VPD Smart Farm_"
                        success = send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, file_tele_msg)
                        if success: st.success("✅ Đã gửi toàn bộ dữ liệu báo cáo qua Telegram thành công!")
            else:
                st.error(f"❌ File tải lên thiếu các cột bắt buộc. Yêu cầu chính xác tên cột: {required_cols}")
        except Exception as err:
            st.error(f"❌ Lỗi xử lý tệp tin nhật ký hệ thống: {str(err)}")

# ==========================================
# TAB 3: PHÂN TÍCH TỪ FILE JSON (MỚI THÊM)
# ==========================================
with tab3:
    st.header("📂 Hệ Thống Phân Tích Dữ Liệu Từ File JSON")
    st.write("Tải lên file dữ liệu cấu trúc JSON chứa lịch sử nhiệt độ và độ ẩm để bóc tách chu kỳ sinh học và phân tích biểu đồ VPD.")

    # 1. Bộ kéo thả file chuyên dụng cho định dạng .json
    uploaded_json = st.file_uploader("Chọn file dữ liệu IoT (.json):", type=["json"], key="uploader_tab3_json")

    if uploaded_json is not None:
        try:
            # Đọc nội dung tệp JSON thành cấu trúc dữ liệu Python
            json_data = json.load(uploaded_json)
            
            raw_records = []
            # Hỗ trợ cả 2 dạng: Mảng gốc [ {...}, {...} ] hoặc cấu trúc có Key chính bọc ngoài {"data": [ ... ]}
            if isinstance(json_data, list):
                raw_records = json_data
            elif isinstance(json_data, dict) and "data" in json_data:
                raw_records = json_data["data"]
            else:
                st.error("❌ Cấu trúc dữ liệu file JSON không đúng chuẩn định dạng. File cần chứa một mảng danh sách các bản ghi dữ liệu.")
            
            if raw_records:
                records_parsed = []
                for idx, item in enumerate(raw_records):
                    # Đọc và ép kiểu an toàn dự phòng cho cả tiếng Anh lẫn tiếng Việt
                    temp = float(item.get("temperature", item.get("Nhiệt độ (°C)", item.get("Nhiệt độ", 25.0))))
                    rh = float(item.get("humidity", item.get("Độ ẩm (%)", item.get("Độ ẩm", 70.0))))
                    
                    # Trích xuất chuỗi thời gian
                    ts_str = item.get("timestamp", item.get("Hiển thị Giờ", item.get("Thời gian")))
                    
                    # Chuẩn hóa cấu trúc thời gian để hiển thị trục X đồ thị sắc nét
                    if ts_str:
                        ts_str = str(ts_str)
                        if ":" in ts_str and len(ts_str) <= 5: # Định dạng kiểu "14:30"
                            display_time = ts_str
                            try:
                                hour_val = int(ts_str.split(":")[0])
                            except:
                                hour_val = 12
                        else: # Định dạng đầy đủ ngày giờ, cố gắng parse tự động
                            try:
                                # Thử parse định dạng chuẩn yyyy-mm-dd hh:mm:ss
                                dt_parsed = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                                display_time = dt_parsed.strftime("%H:%M")
                                hour_val = dt_parsed.hour
                            except:
                                display_time = ts_str[:5]
                                hour_val = 12
                    else:
                        # Nếu hoàn toàn không có thời gian, tự động chia đều mốc giờ trong ngày làm dữ liệu mô phỏng mẫu
                        hour_val = int((idx * 24 / len(raw_records)) % 24)
                        display_time = f"{hour_val:02d}:00"
                    
                    # Sử dụng lại hàm tính toán VPD lõi từ calculations.py
                    vpd_val = calculate_vpd(temp, rh)
                    
                    records_parsed.append({
                        "Hiển thị Giờ": display_time,
                        "Nhiệt độ (°C)": temp,
                        "Độ ẩm (%)": rh,
                        "VPD (kPa)": vpd_val,
                        "Giờ": hour_val
                    })
                
                df_json = pd.DataFrame(records_parsed)
                st.success(f"📥 Phân tích dữ liệu JSON thành công! Nạp được `{len(df_json)}` mốc dữ liệu vào bộ nhớ.")
                
                # Thiết lập giao diện cấu hình ma trận sinh học cây trồng mục tiêu (Tương đương Tag 1)
                st.subheader("🎯 Cấu Hình Phân Tích Sinh Học")
                json_preset_choice = st.selectbox(
                    "Chọn loại cây trồng mục tiêu để đối chiếu dữ liệu JSON:",
                    ["🍓 Dâu Tây Tây Nguyên (VPD tối ưu: 0.6 - 1.2)", 
                     "🌹 Hoa Hồng Nhà Kính (VPD: 0.8 - 1.4)", 
                     "🍅 Cà Chua Công Nghệ Cao (VPD: 0.7 - 1.3)"],
                    key="sb_plant_tab3"
                )
                json_matrix = get_plant_matrix_by_choice(json_preset_choice)
                
                # Quét tính toán tổng giờ bị stress sinh học từ file JSON giống Tab 2
                json_stress_hours, _ = calculate_plant_stress_hours(df_json, json_matrix)
                st.warning(f"⚠️ **Thống kê tích lũy JSON:** Tổng số giờ cây trồng chịu áp lực Stress VPD gắt: **{json_stress_hours:.1f} giờ**")
                
                # Hiển thị khối số liệu trung bình (Metrics tổng hợp dữ liệu)
                st.subheader("📊 Số Liệu Cảm Biến Trung Bình Chu Kỳ")
                m_json_col1, m_json_col2, m_json_col3, m_json_col4 = st.columns(4)
                m_json_col1.metric("Nhiệt Độ TB", f"{df_json['Nhiệt độ (°C)'].mean():.1f} °C")
                m_json_col2.metric("Độ Ẩm Không Khí TB", f"{df_json['Độ ẩm (%)'].mean():.1f} %")
                m_json_col3.metric("Điểm Sương TB", f"{calculate_dew_point(df_json['Nhiệt độ (°C)'].mean(), df_json['Độ ẩm (%)'].mean()):.1f} °C")
                m_json_col4.metric("VPD Trung Bình", f"{df_json['VPD (kPa)'].mean():.2f} kPa")
                
                # Tái sử dụng thư viện đồ thị Altair từ charts.py để dựng hình tương tác phóng to/thu nhỏ rộng rãi
                st.subheader("📈 Đồ Thị Diễn Biến Chỉ Số Vi Khí Hậu Từ File JSON")
                st.altair_chart(draw_vpd_chart(df_json), use_container_width=True)
                st.altair_chart(draw_combined_temp_humidity_chart(df_json), use_container_width=True)
                
                # Gọi logic lõi trong analytics.py để chia khối thời gian phân tách buổi sinh học
                st.subheader("📋 Báo Cáo Phân Tích Chu Kỳ Buổi & Giải Pháp Vận Hành")
                df_json_block_report = analyze_day_by_blocks_rt(df_json, json_matrix)
                st.dataframe(df_json_block_report, use_container_width=True, hide_index=True)
                
                # Tích hợp bộ chuyển tiếp dữ liệu phân tích sang Telegram Bot định dạng Markdown chuyên nghiệp
                if st.button("📤 Gửi Toàn Bộ Báo Cáo JSON Qua Telegram", type="primary", key="btn_send_json_tele"):
                    if TELE_TOKEN and TELE_CHAT_ID:
                        json_tele_msg = (
                            f"📂 *BÁO CÁO CHU KỲ IOT (FILE JSON)*\\n"
                            f"📦 File nguồn: `{uploaded_json.name}`\\n"
                            f"🎯 Đối tượng kiểm tra: *{json_preset_choice.split()[0]}*\\n"
                            f"⚠️ Tích lũy Stress: *{json_stress_hours:.1f} giờ*\\n"
                            f"━━━━━━━━━━━━━━━━━━━━\\n\\n"
                        )
                        for _, r_data in df_json_block_report.iterrows():
                            json_tele_msg += (
                                f"Buổi *{r_data['Khoảng Buổi']}*\\n"
                                f"▪️ Môi trường: {r_data['Nhiệt độ TB']} | {r_data['Độ ẩm TB']}\\n"
                                f"▪️ VPD TB: *{r_data['VPD Trung Bình']}*\\n"
                                f"▪️ Đánh giá: *{r_data['Đánh giá sinh học']}*\\n"
                                f"▪️ Giải pháp: {r_data['Giải pháp kỹ thuật']}\\n"
                                f"────────────────────\\n"
                            )
                        json_tele_msg += "\\n📊 _Hệ thống xử lý phân tích cấu trúc dữ liệu JSON tự động thành công!_"
                        
                        if send_telegram_message(TELE_TOKEN, TELE_CHAT_ID, json_tele_msg):
                            st.success("✅ Đã xuất dữ liệu phân tích tệp JSON và truyền tải thông báo thành công qua Telegram Bot!")
                        else:
                            st.error("❌ Truyền dữ liệu API sang máy chủ Telegram thất bại. Hãy kiểm tra lại mã kết nối.")
            
        except Exception as err:
            st.error(f"❌ Không thể đọc cấu trúc tệp tin JSON này. Vui lòng kiểm tra lại định dạng cú pháp dấu ngoặc nhọn/ngoặc vuông. Chi tiết lỗi: {str(err)}")
