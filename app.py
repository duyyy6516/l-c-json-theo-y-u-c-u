import streamlit as st
import pandas as pd
import numpy as np
import requests  # Thư viện dùng để ra lệnh cho Bot Telegram nhắn tin qua mạng
import json

# Cấu hình giao diện tối ưu cho điện thoại
st.set_page_config(
    page_title="Hệ Thống Phân Tích & Chủ Động Gửi Bot",
    page_icon="📱",
    layout="centered"
)

st.title("📱 Hệ Thống VPD & Kích Hoạt Bot Chủ Động")
st.markdown("Ứng dụng lọc dữ liệu theo Ngày và **chỉ gửi tin nhắn Telegram về điện thoại khi bạn chủ động nhấn nút bấm**.")

# --- CẤU HÌNH THÔNG TIN BOT TELEGRAM (ĐÃ ĐIỀN SỐ THẬT CỦA BẠN) ---
TELEGRAM_TOKEN = "8537718260:AAFtydsQNB8mnGQ51Tt15rlu4dBKjJcGGWU"   # Token thật từ @BotFather
TELEGRAM_CHAT_ID = "7290661009"                                     # Chat ID thật từ @userinfobot

def calculate_vpd(temp, humi):
    """Tính toán chỉ số VPD (kPa) từ Nhiệt độ và Độ ẩm theo công thức Tetens"""
    vp_sat = 0.61078 * np.exp((17.27 * temp) / (temp + 237.3))
    vpd = vp_sat * (1 - (humi / 100))
    return np.clip(vpd, 0, None)

def send_telegram_message(message):
    """Gửi tin nhắn khẩn cấp qua mạng về ứng dụng Telegram trên điện thoại"""
    if not TELEGRAM_TOKEN or "THAY_MÃ" in TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=3)
    except:
        pass 

def analyze_environment_text(vpd, temp, humi, station_id, time_log):
    """Phân tích dữ liệu trả về 3 cột văn phong điện thoại (Chưa gửi tin nhắn)"""
    sid = str(station_id)
    
    if humi == 0:
        msg = f"🔌 *MẤT TÍN HIỆU THIẾT BỊ*\n⏱ Thời gian: {time_log}\n📍 Số Trạm: {sid}\n📝 *Lý do:* Độ ẩm báo về bằng 0%. Cảm biến có thể bị tuột dây.\n🛠 *Hành động:* Ra vườn kiểm tra lại cục cảm biến ngay!"
        return pd.Series(["Mất tín hiệu thiết bị", f"Trạm {sid} báo độ ẩm bằng 0%.", "Ra vườn kiểm tra lại dây cáp, rút ra cắm lại cục cảm biến.", msg, True])
    
    if humi >= 99.5 or vpd == 0:
        msg = f"⚠️ *KHÔNG KHÍ ẨM ƯỚT BÃO HÒA*\n⏱ Thời gian: {time_log}\n📍 Số Trạm: {sid}\n💧 Độ ẩm: {humi}%\n🛠 *Hành động:* Bật ngay quạt hút đuổi ẩm và ngừng tưới nước để tránh nấm bệnh!"
        return pd.Series(["Không khí ẩm ướt bão hòa", f"Trạm {sid} báo độ ẩm chạm trần {humi}%. Nhà màng bí bách.", "Bật ngay quạt hút đuổi ẩm và ngừng tưới nước!", msg, True])
    
    if temp > 40.0 and humi < 40.0:
        msg = f"🔥 *BÁO ĐỘNG: KHÔ NÓNG GẮT*\n⏱ Thời gian: {time_log}\n📍 Số Trạm: {sid}\n🌡 Nhiệt độ: {temp}°C | 💧 Ẩm: {humi}%\n📝 *Chỉ số bốc hơi vọt lên:* {vpd} kPa\n🛠 *Hành động:* CHẠY RA KÉO LƯỚI LAN ĐEN CẮT NẮNG, BẬT PHUN SƯƠNG KHẨN CẤP!"
        return pd.Series(["⚠️ CẢNH BÁO: KHÔ NÓNG GẮT", f"Trạm {sid} báo nhiệt vọt lên {temp}°C, trời quá hanh khô ({humi}%).", "CHẠY RA KÉO LƯỚI LAN ĐEN CẮT NẮNG, BẬT PHUN SƯƠNG BÙ ẨM KHẨN CẤP!", msg, True])

    if vpd < 0.4:
        return pd.Series(["Nhà kính quá ẩm", f"Độ ẩm trạm {sid} quá cao ({humi}%), trời lạnh mát.", "Bật quạt đối lưu, mở cửa hông để thoát bớt hơi ẩm.", "", False])
    if 0.4 <= vpd < 0.8:
        return pd.Series(["Môi trường mát mẻ lý tưởng", f"Trạm {sid} ghi nhận không khí dịu an toàn.", "Rất tốt cho bầu rễ và cây con. Tiếp tục duy trì chăm sóc bình thường.", "", False])
    if 0.8 <= vpd <= 1.2:
        return pd.Series(["Thời tiết hoàn hảo", f"Trạm {sid} đạt trạng thái cân bằng vàng.", "Thời điểm vàng để cây lớn và nuôi quả. Giữ nguyên chế độ vườn.", "", False])
    
    if humi < 40.0:
        return pd.Series(["Môi trường khô hanh", f"Trạm {sid} báo độ ẩm hơi thấp ({humi}%).", "Bật hệ thống phun sương giữa vườn để bù lại độ ẩm.", "", False])
    else:
        return pd.Series(["Nhiệt độ tăng cao", f"Trạm {sid} báo trời bị hầm nóng ({temp}°C).", "Tăng thêm thời gian tưới nhỏ giọt dưới gốc để cấp nước cho rễ.", "", False])

# Khu vực tải file dữ liệu JSON
uploaded_file = st.file_uploader("Kéo thả file dữ liệu JSON vào đây để phân tích", type=["json"])

if uploaded_file is not None:
    try:
        raw_data = json.load(uploaded_file)
        df = pd.DataFrame(raw_data)
        
        time_col, stt_col = None, None
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['thời gian', 'thoigian', 'time', 'timestamp', 'date']: time_col = col
            if col_lower in ['stt', 'station', 'id', 'tram', 'trạm']: stt_col = col
                
        if not time_col or not stt_col:
            st.error("⚠️ File JSON không chứa cột định danh 'STT' hoặc 'Thời gian'.")
        else:
            df[time_col] = df[time_col].astype(str)
            df[stt_col] = df[stt_col].astype(str)
            
            # Trích xuất danh sách Ngày để chọn
            df['Ngay_Thang'] = df[time_col].str.slice(0, 10)
            list_all_days = sorted(df['Ngay_Thang'].unique())
            
            st.subheader("📅 Bước 1: Chọn Ngày Cần Xem")
            selected_day = st.selectbox("Chọn đúng 1 ngày để xử lý siêu tốc:", options=list_all_days, index=0)
            
            # Lọc bảng dữ liệu của riêng ngày được chọn
            df_filtered = df[df['Ngay_Thang'] == selected_day].copy()
            
            processed_chunks = []
            
            for station_id in df_filtered[stt_col].unique():
                sub_df = df_filtered[df_filtered[stt_col] == station_id].copy()
                t_col, h_col = None, None
                
                if station_id == "5":
                    for col in sub_df.columns:
                        if col.lower() in ['tempkk', 'temp_kk', 'nhietdokk', 'temp']: t_col = col
                        if col.lower() in ['humikk', 'humi_kk', 'doamkk', 'humi']: h_col = col
                    if t_col and h_col:
                        sub_df[t_col] = pd.to_numeric(sub_df[t_col], errors='coerce')
                        sub_df[h_col] = pd.to_numeric(sub_df[h_col], errors='coerce')
                else:
                    if 'Nhiệt Độ' in sub_df.columns or 'Nhiệt độ' in sub_df.columns:
                        s_temp = pd.Series(np.nan, index=sub_df.index)
                        if 'Nhiệt Độ' in sub_df.columns: s_temp = s_temp.fillna(sub_df['Nhiệt Độ'])
                        if 'Nhiệt độ' in sub_df.columns: s_temp = s_temp.fillna(sub_df['Nhiệt độ'])
                        sub_df['Nhiệt_Độ_Đất'] = pd.to_numeric(s_temp, errors='coerce')
                        t_col = 'Nhiệt_Độ_Đất'
                    for col in sub_df.columns:
                        if col in ['Độ ẩm', 'doam', 'độ ẩm']: 
                            sub_df['Độ_Ẩm_Đất'] = pd.to_numeric(sub_df[col], errors='coerce')
                            h_col = 'Độ_Ẩm_Đất'
                    
                    if t_col and h_col:
                        sub_df[t_col] = sub_df[t_col].apply(lambda x: x / 10.0 if x > 100 else x)
                        sub_df[h_col] = sub_df[h_col].apply(lambda x: x / 10.0 if x > 100 else x)
                
                if t_col and h_col:
                    sub_df = sub_df.dropna(subset=[t_col, h_col])
                    if not sub_df.empty:
                        sub_df['VPD (kPa)'] = calculate_vpd(sub_df[t_col], sub_df[h_col]).round(3)
                        
                        # Biên dịch nội dung sẵn (chưa kích hoạt gửi tin nhắn)
                        sub_df[['Trạng Thái Vườn', 'Lý Do Từ Cảm Biến', 'Hành Động Khắc Phục', 'Chuoi_Tin_Nhan', 'La_Nguy_Hiem']] = sub_df.apply(
                            lambda row: analyze_environment_text(row['VPD (kPa)'], row[t_col], row[h_col], row[stt_col], row[time_col]), axis=1
                        )
                        
                        sub_df = sub_df.rename(columns={stt_col: "Số Trạm"})
                        sub_cols = [time_col, "Số Trạm", 'VPD (kPa)', 'Trạng Thái Vườn', 'Lý Do Từ Cảm Biến', 'Hành Động Khắc Phục', 'Chuoi_Tin_Nhan', 'La_Nguy_Hiem']
                        processed_chunks.append(sub_df[sub_cols])
            
            if processed_chunks:
                final_df = pd.concat(processed_chunks, ignore_index=True)
                final_df = final_df.sort_values(by=time_col, ascending=True)
                
                # --- NÚT BẤM KÍCH HOẠT CHỦ ĐỘNG ---
                st.subheader("🚀 Bước 2: Bấm Gửi Báo Động Về Điện Thoại")
                danger_df = final_df[final_df['La_Nguy_Hiem'] == True]
                
                st.write(f"Tìm thấy **{len(danger_df)}** mốc thời gian có nguy cơ Khô Nóng hoặc Lỗi trong ngày {selected_day}.")
                
                # Tạo nút bấm lớn
                if st.button("🔔 XỬ LÝ & GỬI THÔNG BÁO TELEGRAM", use_container_width=True, type="primary"):
                    if danger_df.empty:
                        st.success("🎉 Ngày này môi trường rất an toàn, không có mốc nguy hiểm nào để bắn Telegram!")
                    else:
                        with st.spinner("🤖 Đang kích hoạt Bot bắn tin nhắn về điện thoại..."):
                            # Vòng lặp chỉ quét qua các dòng thực sự nguy hiểm để gửi tin nhắn
                            for _, row in danger_df.iterrows():
                                send_telegram_message(row['Chuoi_Tin_Nhan'])
                        st.success(f"✅ Đã gửi thành công {len(danger_df)} tin nhắn cảnh báo về máy Telegram cá nhân!")
                
                # Hiển thị bảng số liệu sạch cho người dân xem trước dưới đáy app
                st.subheader(f"📋 Bảng Số Liệu Xem Trước Ngày: {selected_day}")
                show_cols = [time_col, "Số Trạm", 'VPD (kPa)', 'Trạng Thái Vườn', 'Lý Do Từ Cảm Biến', 'Hành Động Khắc Phục']
                st.dataframe(final_df[show_cols], use_container_width=True)
            else:
                st.warning("⚠️ Không thể trích xuất dữ liệu Nhiệt độ và Độ ẩm hợp lệ từ ngày đã chọn.")
                
    except Exception as e:
        st.error(f"Không thể đọc file JSON. Lỗi hệ thống: {str(e)}")
