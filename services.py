import requests

def send_telegram_message(token, chat_id, text):
    """Gửi tin nhắn dữ liệu và cảnh báo Agronomy về máy điện thoại qua Telegram API"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass  # Bypass an toàn nếu đường truyền internet của farm tạm thời chập chờn

def get_quick_solution(vpd, vmin, vmax, hour):
    """Hệ thống chỉ lệnh kỹ thuật số tự động đề xuất phương án cho người vận hành"""
    if vmin <= vpd <= vmax:
        return "Môi trường tối ưu. Tiếp tục duy trì trạng thái cảm biến hiện tại."
        
    if vpd < vmin:
        if 5 <= hour < 15:
            return "VPD quá ẩm trong ngày. Hãy tắt ngay phun sương, mở tối đa bạt mái rèm, tăng công suất quạt đối lưu."
        else:
            return "Độ ẩm ban đêm quá cao. Bật quạt lưu thông gió nhẹ để tránh đọng sương rỉ sắt nấm bệnh trên lá."
            
    if vpd > vmax:
        if 10 <= hour < 16:
            return "Khô nóng gắt đỉnh điểm! Kéo ngay lưới cắt nắng 50%, kích hoạt hệ thống phun sương mịn hạt ngắn chu kỳ 2 phút."
        else:
            return "VPD khô gắt cuối ngày. Hãy tưới ẩm nhẹ nền đất nhà kính giữ ẩm, đóng bớt cửa gió đón gió hanh."
            
    return "Theo dõi sát sao diễn biến chỉ số trên biểu đồ Altair."
