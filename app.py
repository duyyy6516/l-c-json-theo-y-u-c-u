import streamlit as st
import pandas as pd
import numpy as np
import requests  # Dùng để gọi dữ liệu cảm biến và ra lệnh cho Bot nhắn tin
import time

# Cấu hình giao diện tối ưu hoàn toàn cho màn hình dọc Điện thoại (Mobile)
st.set_page_config(
    page_title="Hệ Thống Real-Time Ngưỡng Động",
    page_icon="🚨",
    layout="centered"
)

st.title("🚨 Hệ Thống VPD Real-Time & Cấu Hình Ngưỡng")
st.markdown("⚡ *Cập nhật sau mỗi 30 giây. Bạn có thể tự tay chỉnh khoảng tối ưu VPD tùy theo loại cây trồng ngay bên dưới.*")

# --- CẤU HÌNH THÔNG TIN KẾT NỐI THẬT CỦA BẠN ---
API_URL = "https://api.myjson.online/v1/records/67b45649e7351b655d426f2e" # Link Server hút data cảm biến thực tế
TELEGRAM_TOKEN = "8537718260:AAFtydsQNB8mnGQ51Tt15rlu4dBKjJcGGWU"        # Token thật từ @BotFather
TELEGRAM_CHAT_ID = "7290661009"                                          # Chat ID thật từ @userinfobot

# =====================================================================
# 🛠️ KHU VỰC CÀI ĐẶT CẤU HÌNH NGƯỠNG ĐỘNG NGAY TRÊN ĐIỆN THOẠI
# =====================================================================
st.subheader("⚙️ Cài Đặt Ngưỡng VPD Cho Vườn")

# Thanh trượt cài đặt ngưỡng dưới (Phân định vùng Quá Ẩm và Ẩm Dịu Mát)
low_threshold = st.slider(
    "1. Ngưỡng VPD Thấp (Dưới mức này không khí quá ẩm):",
    min_value=0.1, max_value=1.0, value=0.4, step=0.05, format="%.2f kPa"
)

# Thanh trượt cài đặt ngưỡng trên (Phân định vùng Quang Hợp và Khô Nóng Stress)
high_threshold = st.slider(
    "2. Ngưỡng VPD Cao (Vượt mức này cây bị stress khô nóng):",
    min_value=1.0, max_value=3.0, value=1.2, step=0.05, format="%.2f kPa"
)

# Tính toán mốc chênh lệch ở giữa để chia đôi vùng Thấp Tối Ưu và Cao Tối Ưu
mid_threshold = round((low_threshold + high_threshold) / 2, 2)

st.markdown(f"""
📋 **Dải phân loại đang áp dụng:**
* 🔴 **Quá ẩm nghẹn rễ:** Dưới `{low_threshold} kPa`
* 🔵 **Ẩm dịu mát (Cây con):** Từ `{low_threshold} kPa` đến `{mid_threshold} kPa`
* 🟢 **Cân bằng vàng (Quang hợp):** Từ `{mid_threshold} kPa` đến `{high_threshold} kPa`
* 🟠 **Khô nóng / Stress gắt:** Trên `{high_threshold} kPa`
""")
st.markdown("---")

# =====================================================================
# LẬP TRÌNH LOGIC VẬN HÀNH THỜI GIAN THỰC
# =====================================================================

def calculate_vpd(temp, humi):
    """Tính toán chỉ số VPD (kPa) từ Nhiệt độ và Độ ẩm theo công thức Tetens"""
    vp_sat = 0.61078 * np.exp((17.27 * temp) / (temp + 237.3))
    vpd = vp_sat * (1 - (humi / 100))
    return np.clip(vpd, 0, None)

def send_telegram_auto(message):
    """Hàm tự động kết nối mạng để Bot phát tin nhắn về máy điện thoại của bạn"""
    if not TELEGRAM_TOKEN or "THAY_MÃ" in TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=3)
    except:
        pass 

def analyze_realtime_and_trigger_bot(vpd, temp, humi, station_id, time_log):
    """
    HÀM THỜI GIAN THỰC CHỦ CHỐT:
    Quét dữ liệu cảm biến và so sánh ĐỘNG với các ngưỡng do người dân tự kéo ngoài màn hình.
    """
    sid = str(station_id)
    
    # 1. Kiểm tra khẩn cấp: Cảm biến báo số 0 (Đứt dây, lỏng nguồn)
    if humi == 0:
        msg = f"🔌 *MẤT TÍN HIỆU THIẾT BỊ*\n⏱ Cập nhật: {time_log}\n📍 Vị trí: Trạm {sid}\n📝 *Lý do:* Độ ẩm đột ngột tụt về 0%. Mất kết nối đầu dò.\n🛠 *Hành động:* Ra vườn kiểm tra lại dây cáp, rút ra cắm lại cục cảm biến ngay!"
        send_telegram_auto(msg) 
        return pd.Series(["Mất tín hiệu thiết bị", f"Trạm {sid} báo độ ẩm bằng 0%.", "Ra vườn kiểm tra lại dây cáp, rút ra cắm lại cục cảm biến."])
    
    # 2. Kiểm tra khẩn cấp: Khô Nóng Gắt (Vượt ngưỡng cao do người dùng cài đặt)
    if vpd > high_threshold and temp > 40.0 and humi < 40.0:
        msg = f"🔥 *BÁO ĐỘNG REAL-TIME: KHÔ NÓNG GẮT*\n⏱ Cập nhật: {time_log}\n📍 Vị trí: Trạm {sid}\n🌡 Nhiệt độ: {temp}°C | 💧 Độ ẩm: {humi}%\n💨 *Chỉ số VPD thực tế:* {vpd} kPa (Ngưỡng chặn: {high_threshold} kPa)\n🛠 *Hành động:* CHẠY RA KÉO LƯỚI LAN ĐEN CẮT NẮNG, BẬT PHUN SƯƠNG BÙ ẨM KHẨN CẤP!"
        send_telegram_auto(msg) 
        return pd.Series(["⚠️ CẢNH BÁO: KHÔ NÓNG GẮT", f"Trạm {sid} vượt ngưỡng khô gắt cài đặt ({vpd} kPa).", "CHẠY RA KÉO LƯỚI LAN ĐEN CẮT NẮNG, BẬT PHUN SƯƠNG BÙ ẨM KHẨN CẤP!"])
        
    # 3. Kiểm tra khẩn cấp: Bão hòa ẩm đọng sương
    if humi >= 99.5 or vpd == 0:
        msg = f"⚠️ *THÔNG BÁO: BÃO HÒA ẨM*\n⏱ Cập nhật: {time_log}\n📍 Vị trí: Trạm {sid}\n💧 Độ ẩm chạm trần: {humi}%\n🛠 *Hành động:* Bật ngay quạt hút đuổi ẩm và ngừng tưới nước để tránh thối rễ, nấm bệnh!"
        send_telegram_auto(msg) 
        return pd.Series(["Không khí ẩm ướt bão hòa", f"Trạm {sid} báo độ ẩm chạm trần {humi}%. Nhà màng bí bách.", "Bật ngay quạt hút đuổi ẩm và ngừng tưới nước!"])

    # --- SO SÁNH ĐỘNG VỚI THANH KÉO TRƯỢT ĐỂ PHÂN LOẠI TRẠNG THÁI ---
    if vpd < low_threshold:
        return pd.Series(["Nhà kính quá ẩm", f"VPD thấp hơn mốc cài đặt ({vpd} < {low_threshold} kPa). Không khí hầm ẩm.", "Bật quạt đối lưu, mở cửa hông để thoát bớt hơi ẩm."])
    
    if low_threshold <= vpd < mid_threshold:
        return pd.Series(["Môi trường mát mẻ lý tưởng", f"VPD nằm trong khoảng ẩm dịu ngọt ({vpd} kPa). Rất tốt cho cây con.", "Mọi thứ bình thường. Tiếp tục duy trì."])
        
    if mid_threshold <= vpd <= high_threshold:
        return pd.Series(["Thời tiết hoàn hảo", f"VPD đạt điểm vàng quang hợp ({vpd} kPa). Cây ăn phân khỏe nhất.", "Thời điểm vàng nuôi quả lớn. Giữ nguyên chế độ vườn."])
    
    # Trường hợp VPD vượt ngưỡng cao nhưng chưa tới mức cực đoan gắt
    if humi < 40.0:
        return pd.Series(["Môi trường khô hanh", f"VPD vượt ngưỡng nhẹ ({vpd} kPa), độ ẩm không khí xuống thấp ({humi}%).", "Bật hệ thống phun sương giữa vườn để bù lại độ ẩm."])
    else:
        return pd.Series(["Nhiệt độ tăng cao", f"Nhiệt độ nhà màng hầm nóng ({temp}°C) làm đẩy VPD lên mức {vpd} kPa.", "Tăng thời gian tưới nhỏ giọt dưới gốc cấp nước cho rễ làm mát cây."])

# --- GỌI MẠNG HÚT DỮ LIỆU CẢM BIẾN TỰ ĐỘNG ---
def fetch_realtime_api_data():
    try:
        response = requests.get(API_URL, timeout=4)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except:
        return None
    return None

df = fetch_realtime_api_data()

if df is not None and not df.empty:
    time_col = 'Thời gian' if 'Thời gian' in df.columns else 'time'
    stt_col = 'STT' if 'STT' in df.columns else 'station'
    
    if time_col in df.columns and stt_col in df.columns:
        df[time_col] = df[time_col].astype(str)
        df[stt_col] = df[stt_col].astype(str)
        
        df = df.sort_values(by=time_col, ascending=True)
        latest_time_log = df[time_col].iloc[-1]
        
        st.markdown(f"⏱️ **Mốc thời gian cảm biến thực cập nhật:** `{latest_time_log}`")
        st.subheader("🔔 Trạng Thái Theo Dõi Theo Cấu Hình Mới")
        
        processed_chunks = []
        
        for station_id in df[stt_col].unique():
            row = df[df[stt_col] == station_id].tail(1).iloc[0]
            
            t_col = 'tempKK' if station_id == "5" else ('Nhiệt Độ' if 'Nhiệt Độ' in df.columns else 'Nhiệt độ')
            h_col = 'humiKK' if station_id == "5" else 'Độ ẩm'
            
            if t_col in df.columns and h_col in df.columns and not pd.isna(row[t_col]) and not pd.isna(row[h_col]):
                t_val = pd.to_numeric(row[t_col])
                h_val = pd.to_numeric(row[h_col])
                
                if station_id != "5" and t_val > 100: t_val /= 10.0
                if station_id != "5" and h_val > 100: h_val /= 10.0
                
                vpd_val = calculate_vpd(t_val, h_val).round(3)
                
                # Chạy phân tích dựa trên biến số linh động vừa cấu hình
                result_series = analyze_realtime_and_trigger_bot(vpd_val, t_val, h_val, station_id, latest_time_log)
                
                row_df = pd.DataFrame([{
                    "Thời gian": latest_time_log,
                    "Số Trạm": station_id,
                    "VPD (kPa)": vpd_val,
                    "Trạng Thái Vườn": result_series[0],
                    "Lý Do Từ Cảm Biến": result_series[1],
                    "Hành Động Khắc Phục": result_series[2]
                }])
                processed_chunks.append(row_df)
                
        if processed_chunks:
            final_latest_df = pd.concat(processed_chunks, ignore_index=True)
            st.dataframe(final_latest_df, use_container_width=True)

else:
    st.info("🔌 Đang chờ tín hiệu truyền dẫn Real-time từ các trạm cảm biến ngoài vườn...")

# Chu kỳ 30 giây app tự làm mới để đồng bộ hóa cấu hình và lấy số liệu cảm biến mới
time.sleep(30)
st.rerun()
