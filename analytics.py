import pandas as pd
import numpy as np

def get_biological_block(hour):
    """Xác định khối thời gian sinh học của cây trồng tại Đà Lạt"""
    if 5 <= hour < 10: return "🌅 Sáng (05h - 10h)"
    elif 10 <= hour < 15: return "☀️ Trưa (10h - 15h)"
    elif 15 <= hour < 19: return "🌇 Chiều (15h - 19h)"
    elif 19 <= hour < 23: return "🌌 Tối (19h - 23h)"
    else: return "🌙 Khuya (23h - 05h)"

def calculate_dew_point(temp, rh):
    """Tính điểm đọng sương (Dew Point) bằng công thức Magnus-Tetens"""
    a = 17.27
    b = 237.7
    alpha = ((a * temp) / (b + temp)) + np.log(rh / 100.0)
    return round((b * alpha) / (a - alpha), 2)

def predict_vpd_trend_dynamic(history_data, current_hour, plant_matrix):
    """Tính toán độ dốc (Slope) toán học dựa trên dải ma trận động của từng khoảng buổi (Tab 1)"""
    if not history_data or len(history_data) < 3:
        return "📊 Hệ thống đang tích lũy thêm chu kỳ dữ liệu...", "normal"
    try:
        v1 = float(history_data[0]["VPD (kPa)"])
        v2 = float(history_data[1]["VPD (kPa)"])
        v3 = float(history_data[2]["VPD (kPa)"])
        
        current_block = get_biological_block(current_hour)
        vpd_min, vpd_max = plant_matrix[current_block]
        slope = ((v1 - v2) + (v2 - v3)) / 2.0
        
        if abs(v1 - v2) < 0.005 and abs(v2 - v3) < 0.005:
            if v1 < vpd_min: return "🟦 CẢNH BÁO: Hiện trạng quá ẩm đang bị kẹt đứng im lâu. Cần bật quạt đối lưu lập tức.", "danger_blue"
            elif v1 > vpd_max: return "🟥 CẢNH BÁO: Hiện trạng khô nóng đang đứng im kéo dài. Cần kích hoạt hệ thống phun sương.", "danger_red"
            else: return "🟩 Xu hướng: Chỉ số VPD đang duy trì đi ngang rất ổn định trong dải lý tưởng.", "normal"
            
        if v1 > vpd_max and slope > 0.02: 
            return f"🚨 [CẢNH BÁO SỚM] Buổi này cây cần max {vpd_max} kPa, hiện tại {v1:.2f} kPa và đang tăng khô gắt thêm!", "danger_red"
        if v1 < vpd_min and slope < -0.02: 
            return f"🚨 [CẢNH BÁO SỚM] Buổi này cây cần min {vpd_min} kPa, hiện tại {v1:.2f} kPa và đang có xu hướng ẩm ướt thêm!", "danger_blue"
            
        if slope > 0.04: return "📈 Xu hướng: Chỉ số VPD đang tăng nhanh (Khô dần).", "normal"
        elif slope < -0.04: return "📉 Xu hướng: Chỉ số VPD đang sụt giảm nhanh (Ẩm lên).", "normal"
        else: return "🔄 Xu hướng: Biến động biên độ nhỏ, nằm trong tầm kiểm soát sinh học.", "normal"
    except:
        return "🔄 Chỉ số xu hướng đang được chuẩn hóa toán học...", "normal"

def calculate_static_plant_stress(df_data, vpd_min, vpd_max, mode_filter):
    """Hàm tính toán stress nông học dựa trên dải cố định (Chạy ổn định cho Tab 2)"""
    if df_data.empty or "VPD (kPa)" not in df_data.columns:
        return {"dry_hours": 0.0, "wet_hours": 0.0, "fungus_risk": 0}
    
    minutes_per_point = 10
    if len(df_data) > 1 and "datetime_internal" in df_data.columns:
        try:
            minutes_per_point = pd.Series(df_data["datetime_internal"]).diff().dropna().dt.total_seconds().median() / 60.0
        except: minutes_per_point = 10

    dry_points, wet_points, fungus_points = 0, 0, 0
    for idx, row in df_data.iterrows():
        vpd_val = float(row["VPD (kPa)"])
        temp_val = float(row["Nhiệt độ (°C)"])
        if vpd_val > vpd_max: dry_points += 1
        elif vpd_val < vpd_min:
            wet_points += 1
            if 16.0 <= temp_val <= 25.0: fungus_points += 1
                
    dry_hours = round((dry_points * minutes_per_point) / 60.0, 1)
    wet_hours = round((wet_points * minutes_per_point) / 60.0, 1)
    fungus_hours = (fungus_points * minutes_per_point) / 60.0
    fungus_risk_pct = min(int((fungus_hours / 6.0) * 100), 100)
    
    return {"dry_hours": dry_hours, "wet_hours": wet_hours, "fungus_risk": fungus_risk_pct}

def analyze_day_by_blocks_dynamic(history_list, plant_matrix, target_day_str):
    """Hàm phân tích đối chiếu dữ liệu Tab 1 trực tiếp với 5 khoảng dải ma trận động"""
    if not history_list: return pd.DataFrame()
    df = pd.DataFrame(history_list)
    df_filtered = df[df["Ngày"] == target_day_str].copy()
    if df_filtered.empty: return pd.DataFrame()
    
    df_filtered["Buổi"] = df_filtered["datetime_internal"].dt.hour.apply(get_biological_block)
    summary = df_filtered.groupby("Buổi").agg({"Nhiệt độ (°C)": "mean", "Độ ẩm (%)": "mean", "VPD (kPa)": "mean"}).reindex([
        "🌅 Sáng (05h - 10h)", "☀️ Trưa (10h - 15h)", "🌇 Chiều (15h - 19h)", "🌌 Tối (19h - 23h)", "🌙 Khuya (23h - 05h)"
    ]).dropna()
    
    report_data = []
    for idx, row in summary.iterrows():
        avg_t, avg_h, avg_v = round(row["Nhiệt độ (°C)"], 1), round(row["Độ ẩm (%)"], 1), round(row["VPD (kPa)"], 2)
        b_min, b_max = plant_matrix[idx]
        if avg_v < b_min:
            status = f"⚠️ Quá ẩm (Mục tiêu: {b_min}-{b_max})"
            sol = "Bật quạt đối lưu khí mạnh, mở bớt màng thông gió rèm."
        elif avg_v > b_max:
            status = f"🚨 Quá khô (Mục tiêu: {b_min}-{b_max})"
            sol = "Kéo lưới cắt nắng sương, kích hoạt hệ thống phun mịn hạt."
        else:
            status = f"✅ Lý tưởng ({b_min}-{b_max})"
            sol = "Môi trường lý tưởng cho buổi này. Duy trì thông gió thông thường."
            
        report_data.append({
            "Khoảng Buổi": idx, "Nhiệt độ TB": f"{avg_t} °C", "Độ ẩm TB": f"{avg_h} %",
            "VPD Trung Bình": f"{avg_v} kPa", "Đánh giá sinh học": status, "Giải pháp kỹ thuật": sol
        })
    return pd.DataFrame(report_data)
