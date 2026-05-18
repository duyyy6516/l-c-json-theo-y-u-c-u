import streamlit as st
import pandas as pd
import numpy as np
import requests  # Thư viện dùng để ra lệnh cho Bot Telegram nhắn tin qua mạng
import json

# Cấu hình giao diện tối ưu cho điện thoại
st.set_page_config(
    page_title="Hệ Thống Phân Tích & Bot Thông Báo",
    page_icon="📱",
    layout="centered"
)

st.title("📱 Hệ Thống Tính VPD & Bot Cảnh Báo")
st.markdown("Ứng dụng tự động xử lý file dữ liệu, hiển thị bảng phân tích và **kích hoạt Bot Telegram nhắn tin khẩn cấp về điện thoại** nếu phát hiện bất thường.")

# --- CẤU HÌNH THÔNG TIN BOT TELEGRAM (ĐÃ CẬP NHẬT THÔNG TIN THẬT CỦA BẠN) ---
TELEGRAM_TOKEN = "8537718260:AAFtydsQNB8mnGQ51Tt15rlu4dBKjJcGGWU"   # Token thật từ @BotFather
TELEGRAM_CHAT_ID = "7290661009"                                     # Chat ID thật từ @userinfobot

def calculate_vpd(temp, humi):
    """Tính toán chỉ số VPD (kPa) từ Nhiệt độ và Độ ẩm theo công thức Tetens"""
    vp_sat = 0.61078 * np.exp((17.27 * temp) / (temp + 237.3))
    vpd = vp_sat * (1 - (humi / 100))
    return np.clip(vpd, 0, None)

def send_telegram_message(message):
    """Gửi tin nhắn khẩn cấp qua mạng về ứng dụng Telegram trên điện thoại"""
    if TELEGRAM_TOKEN == "THAY_MÃ_TOKEN_BOT_CỦA_BẠN_VÀO_ĐÂY" or not TELEGRAM_TOKEN:
        return # Chặn lỗi bảo mật nếu chưa khai báo token
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=3)
    except:
        pass # Tránh làm sập giao diện web nếu mạng internet bị nghẽn đột xuất

def analyze_and_trigger_bot(vpd, temp, humi, station_id, time_log):
    """
    Phân tích tách 3 cột dạng tin nhắn điện thoại.
    Nếu gặp mốc nguy hiểm, tự động gọi hàm send_telegram_message để báo về máy.
    """
    sid = str(station_id)
    
    # 1. Kiểm tra lỗi mất tín hiệu cảm biến (Độ ẩm bằng 0)
    if humi == 0:
        msg = f"🔌 *MẤT TÍN HIỆU THIẾT BỊ*\n⏱ Thời gian: {time_log}\n📍 Số Trạm: {sid}\n" \
              f"📝 *Lý do:* Độ ẩm báo về bằng 0%. Cảm biến có thể bị tuột dây hoặc lỏng giắc cắm.\n" \
              f"🛠 *Hành động:* Ra vườn kiểm tra lại cục cảm biến ngay!"
        send_telegram_message(msg) # Bắn tin nhắn ngầm về điện thoại người dân
        return pd.Series(["Mất tín hiệu thiết bị", f"Trạm {sid} báo độ ẩm bằng 0%.", "Ra vườn kiểm tra lại dây cáp, rút ra cắm lại cục cảm biến."])
    
    # 2. Kiểm tra trạng thái bão hòa ẩm (Độ ẩm quá cao)
    if humi >= 99.5 or vpd == 0:
        msg = f"⚠️ *KHÔNG KHÍ ẨM ƯỚT BÃO HÒA*\n⏱ Thời gian: {time_log}\n📍 Số Trạm: {sid}\n💧 Độ ẩm: {humi}%\n" \
              f"🛠 *Hành động:* Bật ngay quạt hút đuổi ẩm và ngừng tưới nước để tránh nấm bệnh!"
        send_telegram_message(msg) # Bắn tin nhắn ngầm về điện thoại người dân
        return pd.Series(["Không khí ẩm ướt bão hòa", f"Trạm {sid} báo độ ẩm chạm trần {humi}%. Nhà màng bí bách.", "Bật ngay quạt hút đuổi ẩm và ngừng tưới nước!"])
    
    # 3. Kiểm tra trạng thái Khô Nóng Gắt (Phần lớn dữ liệu file rơi vào đây)
    if temp > 40.0 and humi < 40.0:
        msg = f"🔥 *BÁO ĐỘNG: KHÔ NÓNG GẮT*\n⏱ Thời gian: {time_log}\n📍 Số Trạm: {sid}\n" \
              f"🌡 Nhiệt độ: {temp}°C | 💧 Ẩm: {humi}%\n📝 *Chỉ số bốc hơi vọt lên:* {vpd} kPa\n" \
              f"🛠 *Hành động:* CHẠY RA KÉO LƯỚI LAN ĐEN CẮT NẮNG, BẬT PHUN SƯƠNG KHẨN CẤP!"
        send_telegram_message(msg) # Bắn tin nhắn ngầm về điện thoại người dân
        return pd.Series(["⚠️ CẢNH BÁO: KHÔ NÓNG GẮT", f"Trạm {sid} báo nhiệt vọt lên {temp}°C, trời quá hanh khô ({humi}%).", "CHẠY RA KÉO LƯỚI LAN ĐEN CẮT NẮNG, BẬT PHUN SƯƠNG BÙ ẨM KHẨN CẤP!"])

    # 4. Kiểm tra trạng thái không khí quá ẩm ướt thông thường
    if vpd < 0.4:
        return pd.Series(["Nhà kính quá ẩm", f"Độ ẩm trạm {sid} quá cao ({humi}%), trời lạnh mát. Cây bị nghẹn rễ.", "Bật quạt đối lưu, mở cửa hông để thoát bớt hơi ẩm."])
    
    # 5. Kiểm tra trạng thái Thấp Tối Ưu
    if 0.4 <= vpd < 0.8:
        return pd.Series(["Môi trường mát mẻ lý tưởng", f"Trạm {sid} ghi nhận không khí dịu an toàn.", "Rất tốt cho bầu rễ và cây con. Tiếp tục duy trì chăm sóc bình thường."])
    
    # 6. Kiểm tra trạng thái Cao Tối Ưu
    if 0.8 <= vpd <= 1.2:
        return pd.Series(["Thời tiết hoàn hảo", f"Trạm {sid} đạt trạng thái cân bằng vàng. Lá mở khỏe.", "Thời điểm vàng để cây lớn và nuôi quả. Giữ nguyên chế độ vườn."])
    
    # Mốc hanh khô nhẹ hoặc hầm nhẹ thông thường
    if humi < 40.0:
        return pd.Series(["Môi trường khô hanh", f"Trạm {sid} báo độ ẩm hơi thấp ({humi}%).", "Bật hệ thống phun sương giữa vườn để bù lại độ ẩm."])
    else:
        return pd.Series(["Nhiệt độ tăng cao", f"Trạm {sid} báo trời bị hầm nóng ({temp}°C).", "Tăng thêm thời gian tưới nhỏ giọt dưới gốc để cấp nước cho rễ."])

# Khu vực tải file dữ liệu JSON
uploaded_file = st.file_uploader("Kéo thả file dữ liệu JSON vào đây để phân tích & kích hoạt Bot", type=["json"])

if uploaded_file is not None:
    try:
        raw_data = json.load(uploaded_file)
        df = pd.DataFrame(raw_data)
        
        # Tự động dò tìm cột Thời gian và cột STT trạm
        time_col = None
        stt_col = None
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['thời gian', 'thoigian', 'time', 'timestamp', 'date']: time_col = col
            if col_lower in ['stt', 'station', 'id', 'tram', 'trạm']: stt_col = col
                
        if not time_col or not stt_col:
            st.error("⚠️ File JSON không chứa cột định danh 'STT' hoặc 'Thời gian'.")
        else:
            df[time_col] = df[time_col].astype(str)
            df[stt_col] = df[stt_col].astype(str)
            
            processed_chunks = []
            
            # Duyệt qua từng Trạm để bóc tách dữ liệu
            for station_id in df[stt_col].unique():
                sub_df = df[df[stt_col] == station_id].copy()
                
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
                        # Bước 1: Tính toán chỉ số VPD trước
                        sub_df['VPD (kPa)'] = calculate_vpd(sub_df[t_col], sub_df[h_col]).round(3)
                        
                        # Bước 2: Phân tích tách thành 3 nội dung cột riêng, tự động bắn Telegram ngầm nếu có lỗi nguy hiểm
                        sub_df[['Trạng Thái Vườn', 'Lý Do Từ Cảm Biến', 'Hành Động Khắc Phục']] = sub_df.apply(
                            lambda row: analyze_and_trigger_bot(row['VPD (kPa)'], row[t_col], row[h_col], row[stt_col], row[time_col]), axis=1
                        )
                        
                        sub_df = sub_df.rename(columns={stt_col: "Số Trạm"})
                        sub_cols = [time_col, "Số Trạm", 'VPD (kPa)', 'Trạng Thái Vườn', 'Lý Do Từ Cảm Biến', 'Hành Động Khắc Phục']
                        processed_chunks.append(sub_df[sub_cols])
            
            # Gộp chung dữ liệu các trạm và xuất ra bảng tổng hợp duy nhất
            if processed_chunks:
                final_df = pd.concat(processed_chunks, ignore_index=True)
                final_df = final_df.sort_values(by=time_col, ascending=True)
                
                st.subheader("📋 Kết Quả Phân Tích Tổng Hợp Từ File JSON")
                st.info("💡 *Hệ thống đã rà soát toàn bộ tệp tin của bạn và tự động kích hoạt Bot Telegram gửi thông báo khẩn về điện thoại đối với các mốc gặp Khô Nóng hoặc Lỗi.*")
                
                # Hiển thị bảng sạch cấu trúc phân tách rõ ràng ra màn hình
                st.dataframe(final_df, use_container_width=True)
            else:
                st.warning("⚠️ Không thể trích xuất dữ liệu Nhiệt độ và Độ ẩm hợp lệ từ file để phân tích.")
                
    except Exception as e:
        st.error(f"Không thể đọc file JSON. Lỗi hệ thống: {str(e)}")
