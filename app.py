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
    ".danger-box-red { padding: 12px; background-color: #C0392B; border-left: 6px solid #17202A; color: #FFFFFF; border-radius: 4px; font-weight: bold; }",
    "</style>"
]
st.markdown("".join(css_styles), unsafe_allow_html=True)

# Khởi tạo ma trận ngưỡng mặc định cho các mô hình cây trồng độc lập
PLANT_PRESETS = {
    "Cà chua chịu nhiệt (Giai đoạn VEG)": {
        "🌅 Sáng (05h-10h)": [0.6, 1.0],
        "☀️ Trưa (10h-15h)": [0.9, 1.4],
        "🌇 Chiều (15h-19h)": [0.7, 1.1],
        "🌌 Tối (19h-23h)": [0.5, 0.8],
        "🌙 Khuya (23h-05h)": [0.4, 0.7]
    },
    "Dâu tây Đà Lạt (Giai đoạn ra hoa/quả)": {
        "🌅 Sáng (05h-10h)": [0.5, 0.8],
        "☀️ Trưa (10h-15h)": [0.8, 1.2],
        "🌇 Chiều (15h-19h)": [0.6, 0.9],
        "🌌 Tối (19h-23h)": [0.4, 0.7],
        "🌙 Khuya (23h-05h)": [0.3, 0.6]
    },
    "Hoa Lan Hồ Điệp (Nhà màng kín)": {
        "🌅 Sáng (05h-10h)": [0.4, 0.7],
        "☀️ Trưa (10h-15h)": [0.6, 1.0],
        "🌇 Chiều (15h-19h)": [0.5, 0.8],
        "🌌 Tối (19h-23h)": [0.3, 0.6],
        "🌙 Khuya (23h-05h)": [0.2, 0.5]
    }
}

st.title("🌿 VPD Smart Farm Monitor Pro — Đà Lạt")
st.caption("Hệ thống giám sát thâm hụt áp suất hơi (VPD) thời gian thực & Phân tích chu kỳ sinh học tối ưu")

# Giao diện Sidebar điều khiển thiết lập hệ thống
with st.sidebar:
    st.header("⚙️ Cấu Hình Hệ Thống")
    preset_choice = st.selectbox("🎯 Mô hình cây trồng", list(PLANT_PRESETS.keys()))
    current_matrix = PLANT_PRESETS[preset_choice]
    
    st.subheader("📊 Ma trận VPD mục tiêu (kPa)")
    updated_matrix = {}
    for block, values in current_matrix.items():
        col_min, col_max = st.columns(2)
        with col_min:
            v_min = st.number_input(f"{block.split(' ')[0]} Min", min_value=0.0, max_value=3.0, value=values[0], step=0.1)
        with col_max:
            v_max = st.number_input(f"{block.split(' ')[0]} Max", min_value=0.0, max_value=5.0, value=values[1], step=0.1)
        updated_matrix[block] = [v_min, v_max]

    st.write("---")
    st.subheader("🔔 Cổng Kết Nối Telegram")
    tele_token_input = st.text_input("Bot Token", value=TELE_TOKEN, type="password")
    tele_chat_input = st.text_input("Chat ID", value=TELE_CHAT_ID)

# Khởi tạo các tabs chức năng (Cập nhật tên các tab theo yêu cầu)
tab_rt, tab_file, tab_json = st.tabs([
    "📊 PHÂN TÍCH VPD THEO THỜI GIAN THỰC", 
    "📂 PHÂN TÍCH TỆP TIN DỮ LIỆU LOG",
    "🔮 PHÂN TÍCH VPD DỰA VÀO FILE JSON"
])

# --- TAB 1: REALTIME RUNNING (GIỮ NGUYÊN HOÀN TOÀN KHÔNG ĐỘNG VÀO) ---
with tab_rt:
    now = datetime.now()
    current_hour_now = now.hour
    
    st.subheader("⏱️ Trạng Thái Cảm Biến Hiện Tại")
    
    # Tính toán các thông số môi trường tức thời tại thời điểm chạy
    c_temp, c_rh = get_weather_by_time(now)
    c_vpd = calculate_vpd(c_temp, c_rh)
    c_dew = calculate_dew_point(c_temp, c_rh)
    c_block = get_biological_block(current_hour_now)
    b_min, b_max = updated_matrix[c_block]
    
    # Hiển thị số liệu Metric trực quan sinh động
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("🌡️ Nhiệt độ phòng", f"{c_temp} °C")
    m_col2.metric("💧 Độ ẩm không khí", f"{c_rh} %")
    
    # Định dạng màu sắc cảnh báo động cho VPD chỉ số
    if c_vpd > b_max:
         m_col3.metric("⚠️ Chỉ số VPD", f"{c_vpd} kPa", delta="Quá Khô (Stress)", delta_color="inverse")
    elif c_vpd < b_min:
         m_col3.metric("⚠️ Chỉ số VPD", f"{c_vpd} kPa", delta="Quá Ẩm (Bệnh Lớp)", delta_color="inverse")
    else:
         m_col3.metric("✅ Chỉ số VPD", f"{c_vpd} kPa", delta="Lý Tưởng")
         
    m_col4.metric("🥶 Điểm sương DewPoint", f"{c_dew} °C")
    
    # Tạo mảng lịch sử 24 giờ giả lập để vẽ đồ thị diễn biến trong ngày
    rt_history_list = []
    base_time = now - timedelta(hours=23)
    for i in range(24):
        loop_time = base_time + timedelta(hours=i)
        l_temp, l_rh = get_weather_by_time(loop_time)
        l_vpd = calculate_vpd(l_temp, l_rh)
        rt_history_list.append({
            "Mốc Giờ": loop_time.hour,
            "Hiển thị Giờ": f"{loop_time.hour:02d}:00",
            "Nhiệt độ (°C)": l_temp,
            "Độ ẩm (%)": l_rh,
            "VPD (kPa)": l_vpd
        })
    df_rt_history = pd.DataFrame(rt_history_list)
    
    # Phân tích dự báo xu hướng biến động VPD chu kỳ kế tiếp dựa trên thuật toán V3
    st.write("---")
    st.subheader("🔮 Dự Báo & Khuyến Nghị Vận Hành Tự Động")
    
    recent_3_points = rt_history_list[-3:]
    recent_3_points.reverse() # Đảo chiều để điểm mới nhất đứng đầu làm history_data đầu vào cho hàm analytics
    
    trend_txt, trend_status = predict_vpd_trend_v3(recent_3_points, current_hour_now, updated_matrix)
    st.info(trend_txt)
    
    # Khối tổng hợp báo cáo ma trận của cả ngày hiện tại
    st.write("---")
    st.subheader("📈 Đồ Thị Động Học Môi Trường Toàn Diện (24 Giờ)")
    
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        vpd_chart_obj = draw_vpd_chart(df_rt_history, v_min=b_min, v_max=b_max)
        st.altair_chart(vpd_chart_obj, use_container_width=True)
    with g_col2:
        env_chart_obj = draw_combined_temp_humidity_chart(df_rt_history)
        st.altair_chart(env_chart_obj, use_container_width=True)
        
    st.write("---")
    st.subheader("📋 Phân Tích Chi Tiết Theo Chu Kỳ Sinh Học")
    df_rt_blocks_report = analyze_day_by_blocks_rt(df_rt_history, updated_matrix)
    st.dataframe(df_rt_blocks_report, use_container_width=True, hide_index=True)
    
    # Nút bấm tích hợp kích hoạt gửi dữ liệu khẩn cấp qua Telegram API
    if st.button("📤 Gửi cảnh báo Realtime qua Telegram", type="primary", key="btn_send_rt_tele"):
        if tele_token_input and tele_chat_input:
            rt_tele_msg = (
                f"🚨 *CẢNH BÁO VPD REALTIME FARM*\n"
                f"🎯 Mô hình: *{preset_choice}*\n"
                f"⏰ Thời gian: `{now.strftime('%H:%M:%S %d/%m/%Y')}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"▪️ Nhiệt độ: `{c_temp} °C`\n"
                f"▪️ Độ ẩm: `{c_rh} %`\n"
                f"▪️ Chỉ số VPD: *{c_vpd} kPa* (Ngưỡng chuẩn: {b_min}-{b_max})\n"
                f"▪️ Điểm Sương: `{c_dew} °C`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔮 *Xu Hướng Dự Báo*: {trend_txt}\n\n"
                f"📊 _Hệ thống giám sát VPD Smart Farm tự động thông minh_"
            )
            success = send_telegram_message(tele_token_input, tele_chat_input, rt_tele_msg)
            if success:
                st.success("✅ Đã gửi thông báo Realtime tới Telegram thành công!")
            else:
                st.error("❌ Không thể kết nối với Telegram API. Vui lòng kiểm tra Token/Chat ID.")

# --- TAB 2: FILE ANALYSIS (CSV / XLSX cũ) ---
with tab_file:
    st.subheader("📂 Tải Lên Nhật Ký Cảm Biến Dạng Tệp Tin (CSV / XLSX)")
    st.caption("Yêu cầu file chứa các cột tối thiểu: 'Nhiệt độ', 'Độ ẩm' hoặc 'VPD'. Nếu thiếu cột VPD, hệ thống sẽ tự tính toán dựa trên nhiệt ẩm gốc.")
    
    uploaded_file = st.file_uploader("Chọn file dữ liệu log cảm biến", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_file = pd.read_csv(uploaded_file)
            else:
                df_file = pd.read_excel(uploaded_file)
                
            st.success(f"🎉 Tải lên tệp thành công! Đã ghi nhận {len(df_file)} dòng dữ liệu.")
            
            # Chuẩn hóa tên cột tự động để tránh lỗi sai ký tự từ người dùng nhập liệu
            rename_dict = {}
            for col in df_file.columns:
                if "nhiệt" in col.lower() or "temp" in col.lower(): rename_dict[col] = "Nhiệt độ (°C)"
                elif "ẩm" in col.lower() or "humid" in col.lower(): rename_dict[col] = "Độ ẩm (%)"
                elif "vpd" in col.lower(): rename_dict[col] = "VPD (kPa)"
                elif "giờ" in col.lower() or "time" in col.lower() or "date" in col.lower(): rename_dict[col] = "Thời Gian"
            df_file.rename(columns=rename_dict, inplace=True)
            
            # Kiểm tra xem các cột cốt lõi đã có đầy đủ chưa
            required_cols = ["Nhiệt độ (°C)", "Độ ẩm (%)"]
            if not all(x in df_file.columns for x in required_cols):
                st.error("❌ Cấu trúc tệp không hợp lệ! File cần có cột dữ liệu chứa từ khóa liên quan đến 'Nhiệt độ' và 'Độ ẩm'.")
            else:
                if "VPD (kPa)" not in df_file.columns:
                    df_file["VPD (kPa)"] = df_file.apply(lambda r: calculate_vpd(r["Nhiệt độ (°C)"], r["Độ ẩm (%)"]), axis=1)
                
                if "Thời Gian" not in df_file.columns:
                    st.warning("⚠️ Không tìm thấy cột thời gian cụ thể trong file. Hệ thống tự sinh mốc giờ tuần tự cách nhau 1 giờ.")
                    df_file["Thời Gian"] = [datetime.now() - timedelta(hours=len(df_file)-1-idx) for idx in range(len(df_file))]
                
                df_file["Thời Gian"] = pd.to_datetime(df_file["Thời Gian"])
                df_file["Mốc Giờ"] = df_file["Thời Gian"].dt.hour
                df_file["Hiển thị Giờ"] = df_file["Thời Gian"].dt.strftime("%H:%M")
                
                st.write("---")
                st.subheader("🎯 Báo Cáo Phân Tích Tổng Quan Tệp Tin")
                
                f_preset_choice = st.selectbox("🎯 Đối sánh với mô hình cây trồng", list(PLANT_PRESETS.keys()), key="file_plant_preset")
                f_matrix = PLANT_PRESETS[f_preset_choice]
                
                total_hours = len(df_file)
                stress_h_under, stress_h_over = calculate_plant_stress_hours(df_file.to_dict('records'), f_matrix)
                
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                f_col1.metric("📊 Tổng số bản ghi", f"{total_hours} mốc")
                f_col2.metric("🔵 Giờ quá ẩm (Dưới ngưỡng)", f"{stress_h_under} giờ", delta=f"{round(stress_h_under/total_hours*100, 1)}% tổng thời gian", delta_color="inverse")
                f_col3.metric("🔴 Giờ quá gắt (Vượt ngưỡng)", f"{stress_h_over} giờ", delta=f"{round(stress_h_over/total_hours*100, 1)}% tổng thời gian", delta_color="inverse")
                f_col4.metric("🟢 Trạng thái an toàn sinh học", f"{total_hours - stress_h_under - stress_h_over} giờ", delta=f"{round((total_hours - stress_h_under - stress_h_over)/total_hours*100, 1)}% An toàn")
                
                st.write("---")
                st.subheader("📊 Trực Quan Hóa Dữ Liệu Biến Thiên Của File")
                fg_col1, fg_col2 = st.columns(2)
                with fg_col1:
                    st.altair_chart(draw_vpd_chart(df_file), use_container_width=True)
                with fg_col2:
                    st.altair_chart(draw_combined_temp_humidity_chart(df_file), use_container_width=True)
                    
                st.write("---")
                st.subheader("📋 Báo Cáo Phân Tích Ma Trận Dữ Liệu File")
                df_block_report = analyze_day_by_blocks_rt(df_file, f_matrix)
                
                if not df_block_report.empty:
                    st.dataframe(df_block_report, use_container_width=True, hide_index=True)
                    
                    if st.button("📤 Gửi báo cáo ma trận qua Telegram", type="primary", key="btn_send_file_tele"):
                        if tele_token_input and tele_chat_input:
                            file_tele_msg = f"📂 *BÁO CÁO CHU KỲ FILE*\\n📦 File: `{uploaded_file.name}`\\n🎯 Mô hình: *{f_preset_choice}*\\n━━━━━━━━━━━━━━━━━━━━\\n\\n"
                            for _, r_data in df_block_report.iterrows():
                                file_tele_msg += f"Buổi *{r_data['Khoảng Buổi']}*\\n▪️ Môi trường: {r_data['Nhiệt độ TB']} | {r_data['Độ ẩm TB']}\\n▪️ VPD TB: *{r_data['VPD Trung Bình']}*\\n▪️ Đánh giá: *{r_data['Đánh giá sinh học']}*\\n▪️ Giải pháp: {r_data['Giải pháp kỹ thuật']}\\n────────────────────\\n"
                            file_tele_msg += "\\n📊 _Hệ thống tự động chấm điểm sinh học VPD Smart Farm_"
                            success = send_telegram_message(tele_token_input, tele_chat_input, file_tele_msg)
                            if success: 
                                st.success("✅ Đã gửi toàn bộ dữ liệu báo cáo qua Telegram thành công!")
                            else:
                                st.error("❌ Không thể kết nối gửi tệp dữ liệu báo cáo qua Telegram API.")
                else:
                    st.info("Chưa có đủ dữ liệu thích hợp để bóc tách chu kỳ buổi.")
        except Exception as err:
            st.error(f"❌ Đã xảy ra lỗi trong quá trình xử lý tệp tin: {str(err)}")

# --- TAB 3: JSON FILE ANALYSIS (MỚI THÊM THEO YÊU CẦU) ---
with tab_json:
    st.subheader("🔮 Tải Lên Nhật Ký Cảm Biến Cấu Trúc Định Dạng JSON")
    st.caption("Chấp nhận định dạng mảng JSON bao gồm danh sách các đối tượng dữ liệu có cấu trúc cặp Khóa - Giá trị chứa thông tin môi trường.")
    
    uploaded_json = st.file_uploader("Chọn file cấu trúc JSON cần phân tích", type=["json"])
    
    if uploaded_json is not None:
        try:
            # Đọc tệp tin JSON và chuyển đổi thành DataFrame
            raw_data = json.load(uploaded_json)
            
            # Nếu JSON ở dạng một object lớn chứa list bên trong, cố gắng giải nén tự động
            if isinstance(raw_data, dict):
                for key, val in raw_data.items():
                    if isinstance(val, list):
                        raw_data = val
                        break
            
            if not isinstance(raw_data, list):
                st.error("❌ Định dạng cấu trúc tệp JSON không hợp lệ. File JSON phải là một mảng chứa danh sách bản ghi dữ liệu.")
            else:
                df_json = pd.DataFrame(raw_data)
                st.success(f"🎉 Tải lên tệp JSON thành công! Đã xử lý {len(df_json)} điểm dữ liệu.")
                
                # Áp dụng logic chuẩn hóa tự động tên cột tương tự như file dữ liệu log thường
                json_rename_dict = {}
                for col in df_json.columns:
                    if "nhiệt" in str(col).lower() or "temp" in str(col).lower(): json_rename_dict[col] = "Nhiệt độ (°C)"
                    elif "ẩm" in str(col).lower() or "humid" in str(col).lower(): json_rename_dict[col] = "Độ ẩm (%)"
                    elif "vpd" in str(col).lower(): json_rename_dict[col] = "VPD (kPa)"
                    elif "giờ" in str(col).lower() or "time" in str(col).lower() or "date" in str(col).lower(): json_rename_dict[col] = "Thời Gian"
                df_json.rename(columns=json_rename_dict, inplace=True)
                
                # Kiểm tra ràng buộc các cột dữ liệu bắt buộc
                json_required = ["Nhiệt độ (°C)", "Độ ẩm (%)"]
                if not all(x in df_json.columns for x in json_required):
                    st.error("❌ Cấu trúc JSON thiếu các trường thuộc tính quy chuẩn liên quan đến 'Nhiệt độ' và 'Độ ẩm'.")
                else:
                    # Chuyển đổi định dạng dữ liệu về dạng số thực tránh lỗi định dạng chuỗi
                    df_json["Nhiệt độ (°C)"] = pd.to_numeric(df_json["Nhiệt độ (°C)"], errors='coerce')
                    df_json["Độ ẩm (%)"] = pd.to_numeric(df_json["Độ ẩm (%)"], errors='coerce')
                    df_json.dropna(subset=json_required, inplace=True)
                    
                    if "VPD (kPa)" not in df_json.columns:
                        df_json["VPD (kPa)"] = df_json.apply(lambda r: calculate_vpd(r["Nhiệt độ (°C)"], r["Độ ẩm (%)"]), axis=1)
                    else:
                        df_json["VPD (kPa)"] = pd.to_numeric(df_json["VPD (kPa)"], errors='coerce')
                    
                    if "Thời Gian" not in df_json.columns:
                        df_json["Thời Gian"] = [datetime.now() - timedelta(hours=len(df_json)-1-idx) for idx in range(len(df_json))]
                    
                    df_json["Thời Gian"] = pd.to_datetime(df_json["Thời Gian"])
                    df_json["Mốc Giờ"] = df_json["Thời Gian"].dt.hour
                    df_json["Hiển thị Giờ"] = df_json["Thời Gian"].dt.strftime("%H:%M")
                    
                    # Phần hiển thị báo cáo tổng hợp thông số thống kê
                    st.write("---")
                    st.subheader("🎯 Báo Cáo Tổng Quan Dữ Liệu Tệp JSON")
                    
                    json_plant_choice = st.selectbox("🎯 Đối sánh với mô hình cây trồng", list(PLANT_PRESETS.keys()), key="json_plant_preset")
                    json_matrix = PLANT_PRESETS[json_plant_choice]
                    
                    j_total_hours = len(df_json)
                    j_stress_under, j_stress_over = calculate_plant_stress_hours(df_json.to_dict('records'), json_matrix)
                    
                    j_col1, j_col2, j_col3, j_col4 = st.columns(4)
                    j_col1.metric("📊 Bản ghi JSON hợp lệ", f"{j_total_hours} mốc")
                    j_col2.metric("🔵 Giờ quá ẩm", f"{j_stress_under} giờ", delta=f"{round(j_stress_under/j_total_hours*100, 1)}%", delta_color="inverse")
                    j_col3.metric("🔴 Giờ quá gắt", f"{j_stress_over} giờ", delta=f"{round(j_stress_over/j_total_hours*100, 1)}%", delta_color="inverse")
                    j_col4.metric("🟢 Trạng thái an toàn", f"{j_total_hours - j_stress_under - j_stress_over} giờ", delta=f"{round((j_total_hours - j_stress_under - j_stress_over)/j_total_hours*100, 1)}%")
                    
                    # Vẽ đồ thị phân tích từ tệp JSON
                    st.write("---")
                    st.subheader("📊 Đồ Thị Phân Tích Dữ Liệu Biến Thiên Từ JSON")
                    jg_col1, jg_col2 = st.columns(2)
                    with jg_col1:
                        st.altair_chart(draw_vpd_chart(df_json), use_container_width=True)
                    with jg_col2:
                        st.altair_chart(draw_combined_temp_humidity_chart(df_json), use_container_width=True)
                        
                    # Phân tích ma trận sinh học chu kỳ buổi cho file JSON
                    st.write("---")
                    st.subheader("📋 Báo Cáo Phân Tích Ma Trận Chu Kỳ Buổi (JSON)")
                    df_json_report = analyze_day_by_blocks_rt(df_json, json_matrix)
                    
                    if not df_json_report.empty:
                        st.dataframe(df_json_report, use_container_width=True, hide_index=True)
                        
                        if st.button("📤 Gửi báo cáo JSON qua Telegram", type="primary", key="btn_send_json_tele"):
                            if tele_token_input and tele_chat_input:
                                json_tele_msg = f"🔮 *BÁO CÁO TOÀN DIỆN FILE JSON*\\n📦 File: `{uploaded_json.name}`\\n🎯 Mô hình: *{json_plant_choice}*\\n━━━━━━━━━━━━━━━━━━━━\\n\\n"
                                for _, r_data in df_json_report.iterrows():
                                    json_tele_msg += f"Buổi *{r_data['Khoảng Buổi']}*\\n▪️ Môi trường: {r_data['Nhiệt độ TB']} | {r_data['Độ ẩm TB']}\\n▪️ VPD TB: *{r_data['VPD Trung Bình']}*\\n▪️ Đánh giá: *{r_data['Đánh giá sinh học']}*\\n▪️ Giải pháp: {r_data['Giải pháp kỹ thuật']}\\n────────────────────\\n"
                                json_tele_msg += "\\n📊 _Hệ thống trích xuất dữ liệu tự động từ tệp tin JSON Smart Farm_"
                                success = send_telegram_message(tele_token_input, tele_chat_input, json_tele_msg)
                                if success: 
                                    st.success("✅ Đã gửi toàn bộ dữ liệu báo cáo JSON qua Telegram thành công!")
                                else:
                                    st.error("❌ Không thể kết nối gửi dữ liệu báo cáo JSON qua Telegram API.")
                    else:
                        st.info("Chưa có đủ dữ liệu thích hợp để bóc tách chu kỳ buổi từ JSON.")
        except Exception as err:
            st.error(f"❌ Đã xảy ra lỗi nghiêm trọng khi parse file JSON: {str(err)}")
