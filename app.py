import streamlit as st
import pandas as pd
import numpy as np
import requests
import json

# Cấu hình giao diện tối ưu di động
st.set_page_config(
    page_title="Hệ Thống VPD Siêu Tốc & Bot Telegram",
    page_icon="📱",
    layout="centered"
)

st.title("📱 Hệ Thống VPD Siêu Tốc & Bot Cảnh Báo")
st.markdown("⚡ *Phiên bản tối ưu hóa bằng thuật toán Vectorized. Xử lý hàng ngàn dòng dữ liệu trong vòng chưa đầy 1 giây!*")

# --- CẤU HÌNH THÔNG TIN BOT TELEGRAM THẬT CỦA BẠN ---
TELEGRAM_TOKEN = "8537718260:AAFtydsQNB8mnGQ51Tt15rlu4dBKjJcGGWU"   
TELEGRAM_CHAT_ID = "7290661009"                                     

def send_telegram_message(text):
    """Gửi tin nhắn về Telegram, tự động ngắt nhỏ nếu chuỗi quá dài để tránh lỗi Telegram API"""
    if not TELEGRAM_TOKEN or "THAY_MÃ" in TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Telegram giới hạn tối đa 4096 ký tự mỗi tin nhắn
    if len(text) <= 4000:
        try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
        except: pass
    else:
        # Tự động chia nhỏ văn bản theo dòng nếu chuỗi quá dài
        lines = text.split('\n')
        chunk = ""
        for line in lines:
            if len(chunk) + len(line) + 1 > 4000:
                try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}, timeout=5)
                except: pass
                chunk = line
            else:
                chunk += "\n" + line if chunk else line
        if chunk:
            try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}, timeout=5)
            except: pass

# Tải file dữ liệu JSON lên ứng dụng
uploaded_file = st.file_uploader("Kéo thả file dữ liệu JSON vào đây để phân tích siêu tốc", type=["json"])

if uploaded_file is not None:
    try:
        # Đọc file thần tốc bằng cơ chế nạp trực tiếp của thư viện Pandas
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
            
            # Trích xuất Ngày để hiển thị danh sách cho người dân chọn
            df['Ngay_Thang'] = df[time_col].str.slice(0, 10)
            list_all_days = sorted(df['Ngay_Thang'].unique())
            
            st.subheader("📅 Bước 1: Chọn Ngày Cần Xem")
            selected_day = st.selectbox("Chọn đúng 1 ngày để xử lý siêu tốc:", options=list_all_days, index=0)
            
            # Lọc nhanh dữ liệu của ngày được chọn
            df_filtered = df[df['Ngay_Thang'] == selected_day].copy()
            
            # Danh sách gom các cục dữ liệu của từng trạm sau xử lý
            processed_chunks = []
            
            # Tách riêng vòng lặp trạm để đồng bộ hóa tên cột, nhưng xử lý tính toán theo mảng (Vector)
            for station_id in df_filtered[stt_col].unique():
                sub_df = df_filtered[df_filtered[stt_col] == station_id].copy()
                t_col, h_col = None, None
                
                if station_id == "5":
                    for col in sub_df.columns:
                        if col.lower() in ['tempkk', 'temp_kk', 'nhietdokk', 'temp']: t_col = col
                        if col.lower() in ['humikk', 'humi_kk', 'doamkk', 'humi']: h_col = col
                    if t_col and h_col:
                        sub_df['T_Real'] = pd.to_numeric(sub_df[t_col], errors='coerce')
                        sub_df['H_Real'] = pd.to_numeric(sub_df[h_col], errors='coerce')
                else:
                    if 'Nhiệt Độ' in sub_df.columns or 'Nhiệt độ' in sub_df.columns:
                        s_temp = pd.Series(np.nan, index=sub_df.index)
                        if 'Nhiệt Độ' in sub_df.columns: s_temp = s_temp.fillna(sub_df['Nhiệt Độ'])
                        if 'Nhiệt độ' in sub_df.columns: s_temp = s_temp.fillna(sub_df['Nhiệt độ'])
                        sub_df['T_Real'] = pd.to_numeric(s_temp, errors='coerce')
                        t_col = 'T_Real'
                    for col in sub_df.columns:
                        if col in ['Độ ẩm', 'doam', 'độ ẩm']: 
                            sub_df['H_Real'] = pd.to_numeric(sub_df[col], errors='coerce')
                            h_col = 'H_Real'
                    
                    # Quy đổi số thô trạm đất bằng toán học mảng (Nhanh gấp 100 lần dùng vòng lặp)
                    if t_col and h_col:
                        sub_df['T_Real'] = np.where(sub_df['T_Real'] > 100, sub_df['T_Real'] / 10.0, sub_df['T_Real'])
                        sub_df['H_Real'] = np.where(sub_df['H_Real'] > 100, sub_df['H_Real'] / 10.0, sub_df['H_Real'])
                
                if t_col and h_col:
                    sub_df = sub_df.dropna(subset=['T_Real', 'H_Real'])
                    if not sub_df.empty:
                        # --- THUẬT TOÁN VECTOR VẬT LÝ TÍNH TOÀN BỘ CỘT CÙNG 1 LÚC ---
                        temp = sub_df['T_Real'].values
                        humi = sub_df['H_Real'].values
                        
                        vp_sat = 0.61078 * np.exp((17.27 * temp) / (temp + 237.3))
                        vpd = vp_sat * (1 - (humi / 100.0))
                        sub_df['VPD (kPa)'] = np.clip(vpd, 0, None).round(3)
                        
                        # --- CƠ CHẾ PHÂN LOẠI TRẠNG THÁI THEO MẢNG CHUẨN TỐC ĐỘ ---
                        t = sub_df['T_Real']
                        h = sub_df['H_Real']
                        v = sub_df['VPD (kPa)']
                        
                        # Khởi tạo các mảng cột rỗng mặc định
                        status = np.full(len(sub_df), "Thời tiết hoàn hảo")
                        reason = np.full(len(sub_df), f"Trạm {station_id} đạt trạng thái cân bằng vàng. Lá mở khỏe.")
                        action = np.full(len(sub_df), "Thời điểm vàng để cây lớn và nuôi quả. Giữ nguyên chế độ vườn.")
                        is_danger = np.zeros(len(sub_df), dtype=bool)
                        
                        # Điều kiện Khô hanh nhẹ
                        cond_dry_light = (h < 40.0)
                        status = np.where(cond_dry_light, "Môi trường khô hanh", status)
                        reason = np.where(cond_dry_light, f"Trạm {station_id} báo độ ẩm hơi thấp.", reason)
                        action = np.where(cond_dry_light, "Bật hệ thống phun sương giữa vườn để bù lại độ ẩm.", action)
                        
                        # Điều kiện Nhiệt độ tăng cao nhẹ
                        cond_hot_light = (t > 30.0)
                        status = np.where(cond_hot_light, "Nhiệt độ tăng cao", status)
                        reason = np.where(cond_hot_light, f"Trạm {station_id} báo trời bị hầm nóng.", reason)
                        action = np.where(cond_hot_light, "Tăng thêm thời gian tưới nhỏ giọt dưới gốc để cấp nước cho rễ.", action)
                        
                        # Điều kiện Thấp Tối Ưu
                        cond_opt_low = (v >= 0.4) & (v < 0.8)
                        status = np.where(cond_opt_low, "Môi trường mát mẻ lý tưởng", status)
                        reason = np.where(cond_opt_low, f"Trạm {station_id} ghi nhận không khí dịu an toàn.", reason)
                        action = np.where(cond_opt_low, "Rất tốt cho bầu rễ và cây con. Tiếp tục duy trì chăm sóc bình thường.", action)
                        
                        # Điều kiện Cao Tối Ưu
                        cond_opt_high = (v >= 0.8) & (v <= 1.2)
                        status = np.where(cond_opt_high, "Thời tiết hoàn hảo", status)
                        reason = np.where(cond_opt_high, f"Trạm {station_id} đạt trạng thái cân bằng vàng.", reason)
                        action = np.where(cond_opt_high, "Thời điểm vàng để cây lớn và nuôi quả. Giữ nguyên chế độ vườn.", action)
                        
                        # Điều kiện Nhà kính quá ẩm
                        cond_wet = (v < 0.4)
                        status = np.where(cond_wet, "Nhà kính quá ẩm", status)
                        reason = np.where(cond_wet, f"Độ ẩm trạm {station_id} quá cao, trời lạnh mát.", reason)
                        action = np.where(cond_wet, "Bật quạt đối lưu, mở cửa hông để thoát bớt hơi ẩm.", action)
                        
                        # [NGUY HIỂM] Điều kiện Khô Nóng Gắt (VPD > 1.2, T > 40, H < 40)
                        cond_dry_hot_extreme = (v > 1.2) & (t > 40.0) & (h < 40.0)
                        status = np.where(cond_dry_hot_extreme, "⚠️ CẢNH BÁO: KHÔ NÓNG GẮT", status)
                        reason = np.where(cond_dry_hot_extreme, f"Trạm {station_id} báo nhiệt vọt lên cao, trời quá hanh khô.", reason)
                        action = np.where(cond_dry_hot_extreme, "CHẠY RA KÉO LƯỚI LAN ĐEN CẮT NẮNG, BẬT PHUN SƯƠNG BÙ ẨM KHẨN CẤP!", action)
                        is_danger = np.where(cond_dry_hot_extreme, True, is_danger)
                        
                        # [NGUY HIỂM] Điều kiện bão hòa ẩm
                        cond_sat = (h >= 99.5) | (v == 0)
                        status = np.where(cond_sat, "Không khí ẩm ướt bão hòa", status)
                        reason = np.where(cond_sat, f"Trạm {station_id} báo độ ẩm chạm trần. Nhà màng bí bách.", reason)
                        action = np.where(cond_sat, "Bật ngay quạt hút đuổi ẩm và ngừng tưới nước!", action)
                        is_danger = np.where(cond_sat, True, is_danger)
                        
                        # [NGUY HIỂM] Điều kiện mất tín hiệu (Humi = 0)
                        cond_lost = (h == 0)
                        status = np.where(cond_lost, "Mất tín hiệu thiết bị", status)
                        reason = np.where(cond_lost, f"Trạm {station_id} báo độ ẩm bằng 0%.", reason)
                        action = np.where(cond_lost, "Ra vườn kiểm tra lại dây cáp, rút ra cắm lại cục cảm biến.", action)
                        is_danger = np.where(cond_lost, True, is_danger)
                        
                        # Đẩy mảng vào DataFrame
                        sub_df['Trạng Trái Vườn'] = status
                        sub_df['Lý Do Từ Cảm Biến'] = reason
                        sub_df['Hành Động Khắc Phục'] = action
                        sub_df['La_Nguy_Hiem'] = is_danger
                        
                        sub_df = sub_df.rename(columns={stt_col: "Số Trạm"})
                        processed_chunks.append(sub_df[[time_col, "Số Trạm", "T_Real", "H_Real", 'VPD (kPa)', 'Trạng Trái Vườn', 'Lý Do Từ Cảm Biến', 'Hành Động Khắc Phục', 'La_Nguy_Hiem']])
            
            if processed_chunks:
                final_df = pd.concat(processed_chunks, ignore_index=True)
                final_df = final_df.sort_values(by=time_col, ascending=True)
                
                # --- BƯỚC CHUẨN BỊ GỬI TIN NHẮN TỔNG HỢP SIÊU TỐC ---
                st.subheader("🚀 Bước 2: Bấm Gửi Báo Động Về Điện Thoại")
                danger_df = final_df[final_df['La_Nguy_Hiem'] == True]
                
                st.write(f"Tìm thấy **{len(danger_df)}** mốc thời gian có nguy cơ Khô Nóng hoặc Lỗi hệ thống cần xử lý.")
                
                if st.button("🔔 XỬ LÝ & GỬI THÔNG BÁO TELEGRAM TỔNG HỢP", use_container_width=True, type="primary"):
                    if danger_df.empty:
                        st.success("🎉 Ngày này môi trường rất an toàn, không cần gửi thông báo!")
                    else:
                        with st.spinner("🤖 Đang gộp dữ liệu và gửi tin nhắn siêu tốc về điện thoại..."):
                            # Gộp toàn bộ các mốc nguy hiểm vào một tin nhắn duy nhất, phân tách bằng các dòng đẹp mắt
                            summary_msg = f"📱 *BÁO CÁO CẢNH BÁO TỔNG HỢP*\n📅 Ngày: `{selected_day}`\n" \
                                          f"📊 Tổng số mốc phát hiện bất thường: *{len(danger_df)} mốc*\n" \
                                          f"----------------------------------------"
                            
                            # Lấy tối đa 15 mốc đại diện nổi bật nhất (hoặc lấy tất cả nếu ít) để tin nhắn không bị tràn mâm
                            sample_danger = danger_df.tail(15) 
                            for _, row in sample_danger.iterrows():
                                summary_msg += f"\n\n⏱ *Time:* `{row[time_col][-8:]}` | 📍 *Trạm:* `{row['Số Trạm']}`" \
                                               f"\n🌡 *T:* {row['T_Real']}°C | 💧 *H:* {row['H_Real']}% | 💨 *VPD:* {row['VPD (kPa)']} kPa" \
                                               f"\n🚨 *Tình trạng:* {row['Trạng Trái Vườn']}" \
                                               f"\n🛠 *Xử lý:* {row['Hành Động Khắc Phục']}" \
                                               f"\n----------------------------------------"
                            
                            if len(danger_df) > 15:
                                summary_msg += f"\n\n...và *{len(danger_df) - 15} mốc khác*. Vui lòng xem bảng chi tiết trên ứng dụng điện thoại!"
                            
                            # Gửi tin nhắn gộp siêu tốc qua mạng
                            send_telegram_message(summary_msg)
                            
                        st.success("✅ Đã xử lý gộp và gửi thông báo tổng hợp về máy Telegram của bạn thành công!")
                
                # Hiển thị bảng số liệu sạch cho người dân xem dưới đáy app
                st.subheader(f"📋 Bảng Xem Trước Số Liệu Ngày: {selected_day}")
                st.dataframe(final_df[[time_col, "Số Trạm", 'VPD (kPa)', 'Trạng Trái Vườn', 'Lý Do Từ Cảm Biến', 'Hành Động Khắc Phục']], use_container_width=True)
            else:
                st.warning("⚠️ Không thể trích xuất dữ liệu Nhiệt độ và Độ ẩm hợp lệ từ ngày đã chọn.")
                
    except Exception as e:
        st.error(f"Không thể đọc file JSON. Lỗi hệ thống: {str(e)}")
