import numpy as np

def calculate_vpd(temp, rh):
    """Tính áp suất hơi bão hòa thiếu hụt VPD (kPa) từ Nhiệt độ (°C) và Độ ẩm (%)"""
    vpsat = 0.61078 * np.exp((17.27 * temp) / (temp + 237.3))
    vpair = vpsat * (rh / 100.0)
    return max(0.0, vpsat - vpair)

def get_weather_by_time(dt_obj):
    """Hàm tạo dữ liệu chu kỳ thời tiết thực tế nhà kính tại Đà Lạt theo mốc giờ"""
    hour = dt_obj.hour + dt_obj.minute / 60.0
    
    # Hàm sóng hình sin nhiệt độ: Đáy lúc 5h30 sáng, đỉnh lúc 13h30 trưa
    t_base = 21.0
    t_amplitude = 6.5
    t_phase = (hour - 13.5) * (2 * np.pi / 24.0)
    temperature = t_base + t_amplitude * np.cos(t_phase)
    
    # Độ ẩm tỷ lệ nghịch biến với đồ thị nhiệt độ
    h_base = 72.0
    h_amplitude = 23.0
    h_phase = (hour - 5.5) * (2 * np.pi / 24.0)
    humidity = h_base + h_amplitude * np.cos(h_phase)
    
    # Tạo độ nhiễu tự nhiên của môi trường thực tế (Nhỏ hơn 0.15)
    noise_t = np.sin(hour * 1.5) * 0.4
    noise_h = np.cos(hour * 1.5) * 1.2
    
    final_t = round(float(np.clip(temperature + noise_t, 10.0, 34.0)), 1)
    final_h = round(float(np.clip(humidity + noise_h, 30.0, 100.0)), 1)
    
    return final_t, final_h
