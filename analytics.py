import pandas as pd
from datetime import datetime

def analyze_day_by_blocks_rt(history_list, vpd_min, vpd_max, target_date_str):
    """Tính toán số liệu trung bình theo từng buổi sáng, trưa, chiều, tối"""
    day_data = [r for r in history_list if r["Ngày"] == target_date_str]
    
    blocks = {
        "🌅 Sáng (07h-11h)": [],
        "☀️ Trưa (11h-15h)": [],
        "🌤️ Chiều (15h-19h)": [],
        "🌙 Tối (19h-24h)": []
    }
    
    for r in day_data:
        time_obj = datetime.strptime(r["Hiển thị Giờ"], "%H:%M")
        hour = time_obj.hour
        vpd_val = r["VPD (kPa)"]
        
        if 7 <= hour < 11:
            blocks["🌅 Sáng (07h-11h)"].append(vpd_val)
        elif 11 <= hour < 15:
            blocks["☀️ Trưa (11h-15h)"].append(vpd_val)
        elif 15 <= hour < 19:
            blocks["🌤️ Chiều (15h-19h)"].append(vpd_val)
        else:
            blocks["🌙 Tối (19h-24h)"].append(vpd_val)
            
    summary = []
    for block_name, vpd_list in blocks.items():
        if vpd_list:
            avg_vpd = sum(vpd_list) / len(vpd_list)
            if avg_vpd < vpd_min:
                danh_gia = "🟦 Quá ẩm"
                huong_xu_ly = "Mở bạt hông muộn hoặc quạt gió xua tan sương" if "Sáng" in block_name else "Bật đối lưu mạnh, giảm tưới"
            elif vpd_min <= avg_vpd <= vpd_max:
                danh_gia = "🟩 Lý tưởng"
                huong_xu_ly = "Môi trường hoàn hảo. Duy trì thông thoáng tự nhiên."
            else:
                danh_gia = "🟥 Quá khô"
                huong_xu_ly = "Cấp ẩm rễ" if "Sáng" in block_name else "Kéo lưới đen, phun sương 5-10 phút/lần"
            
            summary.append({
                "Khoảng Thời Gian": block_name,
                "VPD TB (kPa)": round(avg_vpd, 2),
                "Đánh Giá": danh_gia,
                "Hướng Xử Lý Đề Xuất (Kỹ thuật nhà kính)": huong_xu_ly
            })
        else:
            summary.append({
                "Khoảng Thời Gian": block_name,
                "VPD TB (kPa)": "--",
                "Đánh Giá": "⚪ Đang chờ mốc giờ...",
                "Hướng Xử Lý Đề Xuất (Kỹ thuật nhà kính)": "Chưa có dữ liệu thu thập cho buổi này."
            })
    return pd.DataFrame(summary)

def predict_vpd_trend_v3(filtered_history, current_hour):
    """Thuật toán dự báo xu hướng thời tiết tự nhiên của Đà Lạt"""
    if len(filtered_history) < 2:
        return "🔄 Hệ thống đang tích lũy số liệu mốc giờ để tính toán...", "info"
        
    if 7 <= current_hour < 11:
        return "Nắng đang lên nhanh, bức xạ tăng mạnh. Dự báo nhiệt độ tiếp tục tăng và độ ẩm sẽ giảm sâu.", "warning"
    elif 11 <= current_hour < 14:
        return "Đang ở đỉnh điểm bức xạ. Dự báo duy trì khô nóng cực hạn trước khi dịu dần sau 14h30.", "error"
    elif 14 <= current_hour < 18:
        return "Nắng đang tắt dần. Dự báo nhiệt độ nhà kính hạ nhanh và ẩm độ bắt đầu đảo chiều tăng mạnh.", "success"
    else:
        return "Giai đoạn đêm và rạng sáng. Không có bức xạ, nhiệt hạ thấp và ẩm bão hòa tiến sát mốc 95%.", "info"
