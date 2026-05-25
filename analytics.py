import pandas as pd
import numpy as np

def get_biological_block(hour):
    """Phân chia buổi sinh học dựa trên đồng hồ sinh học của cây trồng"""
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
    """Dự báo xu hướng toán học dựa trên dải VPD động của từng buổi cụ thể"""
    if not history_data or len(history_data) < 3:
        return "📊 Hệ thống đang tích lũy thêm chu kỳ dữ liệu...", "normal"
    try:
        v1 = float(history_data[0]["VPD (kPa)"])
        v2 = float(history_data[1]["VPD (kPa)"])
        v3 = float(history_data[2]["VPD (kPa)"])
        
        current_block = get_biological_block(current_hour)
        
        # Sửa lỗi TypeError: Kiểm tra nếu plant_matrix được truyền dạng dict (Ma trận động)
        if isinstance(plant_matrix, dict) and current_block in plant_matrix:
            vpd_min, vpd_max = plant_matrix[current_block]
        # Nếu plant_matrix vô tình bị truyền dạng số đơn lẻ (do tương thích ngược từ app.py)
        elif isinstance(plant_matrix, (int, float)):
            vpd_min = plant_matrix
            vpd_max = vpd_matrix_backup_global_max if 'vpd_matrix_backup_global_max' in locals() else 1.2
        else:
            vpd_min, vpd_max = 0.8, 1.2
        
        diff_1 = v1 - v2
        diff_2 = v2 - v3
        
        if abs(diff_1) < 0.005 and abs(diff_2) < 0.005:
            if v1 < vpd_min: return "🟦 CẢNH BÁO: Hiện trạng quá ẩm đang bị kẹt đứng im lâu. Cần bật quạt đối lưu lập tức.", "danger_blue"
            elif v1 > vpd_max: return "🟥 CẢNH BÁO: Hiện trạng khô nóng đang đứng im kéo dài. Cần kích hoạt hệ thống phun sương.", "danger_red"
            else: return "🟩 Xu hướng: Chỉ số VPD đang duy trì đi ngang rất ổn định trong dải lý tưởng.", "normal"
            
        slope = (diff_1 + diff_2) / 2.0
        
        if v1 > vpd_max and slope > 0.02: 
            return f"🚨 [CẢNH BÁO SỚM] Buổi này cây cần max {vpd_max} kPa, hiện tại {v1:.2f} kPa và đang tăng khô gắt thêm!", "danger_red"
        if v1 < vpd_min and slope < -0.02: 
            return f"🚨 [CẢNH BÁO SỚM] Buổi này cây cần min {vpd_min} kPa, hiện tại {v1:.2f} kPa và đang có xu hướng ẩm ướt thêm!", "danger_blue"
            
        if slope > 0.04: return "📈 Xu hướng: Chỉ số VPD đang tăng nhanh (Khô dần).", "normal"
        elif slope < -0.04: return "📉 Xu hướng: Chỉ số VPD đang sụt giảm nhanh (Ẩm lên).", "normal"
        else: return "🔄 Xu hướng: Biến động biên độ nhỏ, nằm trong tầm kiểm soát sinh học.", "normal"
    except:
        return "🔄 Chỉ số xu hướng đang được chuẩn hóa toán học...", "normal"

def calculate_dynamic_plant_stress(df_data, plant_matrix, mode_filter):
    """
    Thuật toán Agronomy chuyên sâu: Tính toán giờ Stress Khô / Ẩm tích lũy 
    đối chiếu linh hoạt theo cấu hình ma trận của từng buổi cụ thể.
    """
    if df_data.empty or "VPD (kPa)" not in df_data.columns:
        return {"dry_hours": 0.0, "wet_hours": 0.0, "fungus_risk": 0}
    
    if "1 Ngày gần nhất" in mode_filter or "10 phút" in mode_filter: 
        minutes_per_point = 10
    elif "1 Tuần gần nhất" in mode_filter or "1 Tháng gần nhất" in mode_filter: 
        minutes_per_point = 1440
    elif "Toàn bộ dữ liệu gốc" in mode_filter:
        if len(df_data) > 1 and "datetime_internal" in df_data.columns:
            try:
                time_diffs = pd.Series(df_data["datetime_internal"]).diff().dropna()
                minutes_per_point = time_diffs.dt.total_seconds().median() / 60.0
            except: minutes_per_point = 10
        else: minutes_per_point = 10
    else:
        minutes_per_point = 10

    dry_points = 0
    wet_points = 0
    fungus_points = 0

    for idx, row in df_data.iterrows():
        dt = row["datetime_internal"]
        vpd_val = row["VPD (kPa)"]
        temp_val = row["Nhiệt độ (°C)"]
        
        block_name = get_biological_block(dt.hour)
        
        # Tương thích ngược xử lý lỗi ép kiểu cấu hình ma trận
        if isinstance(plant_matrix, dict) and block_name in plant_matrix:
            b_min, b_max = plant_matrix[block_name]
        else:
            b_min, b_max = 0.6, 1.2
        
        if vpd_val > b_max:
            dry_points += 1
        elif vpd_val < b_min:
            wet_points += 1
            if 16.0 <= temp_val <= 25.0:
                fungus_points += 1
                
    dry_hours = round((dry_points * minutes_per_point) / 60.0, 1)
    wet_hours = round((wet_points * minutes_per_point) / 60.0, 1)
    fungus_hours = (fungus_points * minutes_per_point) / 60.0
    fungus_risk_pct = min(int((fungus_hours / 6.0) * 100), 100)
    
    return {
        "dry_hours": dry_hours,
        "wet_hours": wet_hours,
        "fungus_risk": fungus_risk_pct
    }

def analyze_day_by_blocks_dynamic(history_list, plant_matrix, target_day_str=None):
    """Phân tích báo cáo chu kỳ buổi đối chiếu trực tiếp với ma trận ngưỡng động"""
    if not history_list: return pd.DataFrame()
    df = pd.DataFrame(history_list)
    
    # Sửa lỗi đảo vị trí tham số truyền vào từ app.py cũ
    if target_day_str is None and isinstance(plant_matrix, str):
        target_day_str = plant_matrix
        plant_matrix = None

    df_filtered = df[df["Ngày"] == target_day_str].copy()
    if df_filtered.empty: return pd.DataFrame()
    
    df_filtered["Buổi"] = df_filtered["datetime_internal"].dt.hour.apply(get_biological_block)
    summary = df_filtered.groupby("Buổi").agg({"Nhiệt độ (°C)": "mean", "Độ ẩm (%)": "mean", "VPD (kPa)": "mean"}).reindex([
        "🌅 Sáng (05h - 10h)", "☀️ Trưa (10h - 15h)", "🌇 Chiều (15h - 19h)", "🌌 Tối (19h - 23h)", "🌙 Khuya (23h - 05h)"
    ]).dropna()
    
    report_data = []
    for idx, row in summary.iterrows():
        avg_t = round(row["Nhiệt độ (°C)"], 1)
        avg_h = round(row["Độ ẩm (%)"], 1)
        avg_v = round(row["VPD (kPa)"], 2)
        
        if isinstance(plant_matrix, dict) and idx in plant_matrix:
            b_min, b_max = plant_matrix[idx]
        else:
            b_min, b_max = 0.6, 1.2
        
        if avg_v < b_min:
            status = f"⚠️ Quá ẩm (Mục tiêu: {b_min}-{b_max})"
            sol = "Bật quạt đối lưu khí mạnh, mở bớt màng thông gió rèm."
        elif avg_v > b_max:
            status = f"🚨 Quá khô (Mục tiêu: {b_min}-{b_max})"
            sol = "Kéo lưới cắt nắng sương, kích hoạt hệ thống phun mịn hạt."
        else:
            status = f"✅ Lý tưởng ({b_min}-{b_max})"
            sol = "Môi trường hoàn hảo cho buổi này. Duy trì hệ thống thông gió."
            
        report_data.append({
            "Khoảng Buổi": idx, "Nhiệt độ TB": f"{avg_t} °C", "Độ ẩm TB": f"{avg_h} %",
            "VPD Trung Bình": f"{avg_v} kPa", "Đánh giá sinh học": status, "Giải pháp kỹ thuật": sol
        })
    return pd.DataFrame(report_data)


# ==============================================================================
#  🛠️ ĐOẠN ĐẶC BIỆT: VÁ LỖI COMPATIBILITY WRAPPERS (SỬA TRIỆT ĐỂ LỖI TYPEERROR)
# ==============================================================================

def predict_vpd_trend_v3(history_data, current_hour, *args):
    """Hàm bọc thông minh xử lý cả cấu hình cũ (4 tham số) và mới (3 tham số)"""
    if len(args) == 2:
        # Nếu app.py truyền vpd_min, vpd_max (Hệ thống cũ) -> Tự động chuyển đổi thành ma trận đồng bộ
        v_min, v_max = args[0], args[1]
        mock_matrix = {
            "🌅 Sáng (05h - 10h)": (v_min, v_max),
            "☀️ Trưa (10h - 15h)": (v_min, v_max),
            "🌇 Chiều (15h - 19h)": (v_min, v_max),
            "🌌 Tối (19h - 23h)": (v_min, v_max),
            "🌙 Khuya (23h - 05h)": (v_min, v_max)
        }
        global vpd_matrix_backup_global_max
        vpd_matrix_backup_global_max = v_max
        return predict_vpd_trend_dynamic(history_data, current_hour, mock_matrix)
    elif len(args) == 1:
        # Đúng chuẩn cấu hình ma trận mới
        return predict_vpd_trend_dynamic(history_data, current_hour, args[0])
    else:
        return "🔄 Lỗi cấu trúc truyền tham số dự báo.", "normal"

def calculate_plant_stress_hours(df_data, *args):
    """Hàm bọc xử lý stress hours thích ứng linh hoạt tham số đầu vào"""
    if len(args) == 3:
        # Nếu truyền dạng (vpd_min, vpd_max, mode_filter)
        v_min, v_max, mode = args[0], args[1], args[2]
        mock_matrix = {k: (v_min, v_max) for k in ["🌅 Sáng (05h - 10h)", "☀️ Trưa (10h - 15h)", "🌇 Chiều (15h - 19h)", "🌌 Tối (19h - 23h)", "🌙 Khuya (23h - 05h)"]}
        return calculate_dynamic_plant_stress(df_data, mock_matrix, mode)
    elif len(args) == 2:
        # Nếu truyền dạng (plant_matrix, mode_filter)
        return calculate_dynamic_plant_stress(df_data, args[0], args[1])
    return {"dry_hours": 0.0, "wet_hours": 0.0, "fungus_risk": 0}

def analyze_day_by_blocks_rt(history_list, *args):
    """Hàm bọc xử lý phân tích chu kỳ lịch sử realtime cũ"""
    if len(args) == 3:
        # Truyền dạng (vpd_min, vpd_max, selected_view_day)
        v_min, v_max, day_str = args[0], args[1], args[2]
        mock_matrix = {k: (v_min, v_max) for k in ["🌅 Sáng (05h - 10h)", "☀️ Trưa (10h - 15h)", "🌇 Chiều (15h - 19h)", "🌌 Tối (19h - 23h)", "🌙 Khuya (23h - 05h)"]}
        return analyze_day_by_blocks_dynamic(history_list, mock_matrix, day_str)
    elif len(args) == 2:
        # Truyền dạng (plant_matrix, selected_view_day)
        return analyze_day_by_blocks_dynamic(history_list, args[0], args[1])
    return pd.DataFrame()
