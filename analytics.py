import pandas as pd
import numpy as np

def get_biological_block(hour):
    if 5 <= hour < 10: return "🌅 Sáng (05h-10h)"
    elif 10 <= hour < 15: return "☀️ Trưa (10h-15h)"
    elif 15 <= hour < 19: return "🌇 Chiều (15h-19h)"
    elif 19 <= hour < 23: return "🌌 Tối (19h-23h)"
    else: return "🌙 Khuya (23h-05h)"

def calculate_dew_point(temp, rh):
    a = 17.27
    b = 237.7
    alpha = ((a * temp) / (b + temp)) + np.log(rh / 100.0)
    return round((b * alpha) / (a - alpha), 2)

def predict_vpd_trend_v3(history_data, current_hour, plant_matrix):
    if not history_data or len(history_data) < 3:
        return "📊 Hệ thống đang tích lũy thêm chu kỳ dữ liệu...", "normal"
    try:
        v1 = float(history_data[0]["VPD (kPa)"])
        v2 = float(history_data[1]["VPD (kPa)"])
        v3 = float(history_data[2]["VPD (kPa)"])
        
        current_block = get_biological_block(current_hour)
        vpd_min, vpd_max = plant_matrix[current_block]
        
        diff_1 = v1 - v2
        diff_2 = v2 - v3
        
        if abs(diff_1) < 0.005 and abs(diff_2) < 0.005:
            if v1 >= vpd_max + 0.5: return "🟥 CẢNH BÁO: Trạng thái QUÁ NÓNG kéo dài. Nguy cơ cháy lá cực cao!", "danger_red"
            elif v1 < vpd_min - 0.2: return "🟦 CẢNH BÁO: Trạng thái QUÁ ẨM đứng im lâu ngày. Bật quạt đối lưu gấp!", "danger_blue"
            elif vpd_min <= v1 <= vpd_max: return "🟩 Xu hướng: Chỉ số VPD đang duy trì đi ngang ổn định trong dải lý tưởng.", "normal"
            else: return "🔄 Xu hướng: Chỉ số ít biến động nhưng nằm ngoài dải an toàn tối ưu.", "normal"
            
        slope = (diff_1 + diff_2) / 2.0
        
        if v1 >= vpd_max + 0.5 and slope > 0.02: return "🚨 [CẢNH BÁO ĐỎ] Đã chạm ngưỡng QUÁ NÓNG và đang tiếp tục tăng khô gắt!", "danger_red"
        if v1 < vpd_min - 0.2 and slope < -0.02: return "🚨 [CẢNH BÁO ĐỎ] Đã chạm ngưỡng QUÁ ẨM và đang tiếp tục tụt sâu đọng sương!", "danger_blue"
        
        if slope > 0.04: return "📈 Xu hướng: Chỉ số VPD đang tăng (Khí hậu nóng khô dần).", "normal"
        elif slope < -0.04: return "📉 Xu hướng: Chỉ số VPD đang sụt giảm (Khí hậu ẩm mát lên).", "normal"
        else: return "🔄 Xu hướng: Biến động biên độ nhỏ, nằm trong tầm kiểm soát.", "normal"
    except:
        return "🔄 Chỉ số xu hướng đang được chuẩn hóa toán học...", "normal"

def calculate_plant_stress_hours(df_data, plant_matrix, mode_filter):
    if df_data.empty or "VPD (kPa)" not in df_data.columns:
        return {"dry_hours": 0.0, "wet_hours": 0.0, "fungus_risk": 0}
    
    if "1 Ngày gần nhất" in mode_filter or "10 phút" in mode_filter: minutes_per_point = 10
    elif "1 Tuần gần nhất" in mode_filter: minutes_per_point = 1440
    elif "Toàn bộ dữ liệu gốc" in mode_filter:
        if len(df_data) > 1 and "datetime_internal" in df_data.columns:
            try:
                time_diffs = pd.Series(df_data["datetime_internal"]).diff().dropna()
                minutes_per_point = time_diffs.dt.total_seconds().median() / 60.0
            except: minutes_per_point = 10
        else: minutes_per_point = 10
    else: minutes_per_point = 10

    dry_points = 0
    wet_points = 0
    fungus_points = 0

    for idx, row in df_data.iterrows():
        dt = row["datetime_internal"]
        vpd_val = row["VPD (kPa)"]
        temp_val = row["Nhiệt độ (°C)"]
        
        block_name = get_biological_block(dt.hour)
        vpd_min, vpd_max = plant_matrix[block_name]
        
        if vpd_val > vpd_max:
            dry_points += 1
        elif vpd_val < vpd_min:
            wet_points += 1
            if 16.0 <= temp_val <= 25.0:
                fungus_points += 1
                
    dry_hours = round((dry_points * minutes_per_point) / 60.0, 1)
    wet_hours = round((wet_points * minutes_per_point) / 60.0, 1)
    fungus_hours = (fungus_points * minutes_per_point) / 60.0
    fungus_risk_pct = min(int((fungus_hours / 6.0) * 100), 100)
    
    return {"dry_hours": dry_hours, "wet_hours": wet_hours, "fungus_risk": fungus_risk_pct}

def analyze_day_by_blocks_rt(history_list, plant_matrix, target_day_str):
    if not history_list: return pd.DataFrame()
    df = pd.DataFrame(history_list)
    df_filtered = df[df["Ngày"] == target_day_str].copy()
    if df_filtered.empty: return pd.DataFrame()
    
    df_filtered["Buổi"] = df_filtered["datetime_internal"].dt.hour.apply(get_biological_block)
    summary = df_filtered.groupby("Buổi").agg({"Nhiệt độ (°C)": "mean", "Độ ẩm (%)": "mean", "VPD (kPa)": "mean"}).reindex([
        "🌅 Sáng (05h-10h)", "☀️ Trưa (10h-15h)", "🌇 Chiều (15h-19h)", "🌌 Tối (19h-23h)", "🌙 Khuya (23h-05h)"
    ]).dropna()
    
    report_data = []
    for idx, row in summary.iterrows():
        avg_t = round(row["Nhiệt độ (°C)"], 1)
        avg_h = round(row["Độ ẩm (%)"], 1)
        avg_v = round(row["VPD (kPa)"], 2)
        
        vpd_min, vpd_max = plant_matrix[idx]
        
        if avg_v >= vpd_max + 0.5:
            status = "🔴 Quá Nóng"
            sol = "Xả rèm đỉnh, phun sương hạt mịn công suất tối đa, bật quạt hút nhiệt."
        elif avg_v > vpd_max:
            status = "💛 Nóng"
            sol = "Kéo lưới cắt nắng, kích hoạt nhẹ phun sương giữ ẩm."
        elif avg_v < vpd_min - 0.2:
            status = "🔵 Quá Ẩm"
            sol = "Bật toàn bộ hệ thống quạt đối lưu, kích hoạt sưởi nhẹ nếu có."
        elif avg_v < vpd_min:
            status = "🌐 Ẩm"
            sol = "Mở bớt rèm hông nhà kính để lưu thông khí tự nhiên."
        else:
            status = "🟩 Lý Tưởng"
            sol = "Môi trường hoàn hảo. Duy trì hiện trạng tự động."
            
        report_data.append({
            "Khoảng Buổi": idx, "Nhiệt độ TB": f"{avg_t} °C", "Độ ẩm TB": f"{avg_h} %",
            "VPD Trung Bình": f"{avg_v} kPa", "Đánh giá sinh học": status, "Giải pháp kỹ thuật": sol
        })
    return pd.DataFrame(report_data)
