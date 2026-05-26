import pandas as pd
import numpy as np

def predict_vpd_trend_v3(history_data, current_hour, vpd_min, vpd_max):
    """Thuật toán toán học dự báo xu hướng nâng cao dựa vào Slope của 3 điểm gần nhất"""
    if not history_data or len(history_data) < 3:
        return "📊 Hệ thống đang tích lũy thêm chu kỳ dữ liệu để phân tích xu hướng...", "normal"
    
    try:
        v1 = float(history_data[0]["VPD (kPa)"])
        v2 = float(history_data[1]["VPD (kPa)"])
        v3 = float(history_data[2]["VPD (kPa)"])
        
        diff_1 = v1 - v2
        diff_2 = v2 - v3
        
        if abs(diff_1) < 0.005 and abs(diff_2) < 0.005:
            if v1 < vpd_min:
                return "🟦 CẢNH BÁO: Hiện trạng quá ẩm đang bị kẹt đứng im lâu. Cần bật quạt đối lưu lập tức.", "danger_blue"
            elif v1 > vpd_max:
                return "🟥 CẢNH BÁO: Hiện trạng khô nóng đang đứng im kéo dài. Cần kích hoạt hệ thống phun sương.", "danger_red"
            else:
                return "🟩 Xu hướng: Chỉ số VPD ổn định đi ngang trong dải mục tiêu sinh học lý tưởng.", "normal"
        
        slope = (diff_1 + diff_2) / 2.0
        if v1 > vpd_max and slope > 0.015:
            return f"🚨 [CẢNH BÁO SỚM] Chỉ số vượt dải đỉnh mục tiêu ({v1:.2f} kPa) và đang tăng khô gắt dồn dập!", "danger_red"
        if v1 < vpd_min and slope < -0.015:
            return f"🚨 [CẢNH BÁO SỚM] Chỉ số sụt xuống dưới dải mục tiêu ({v1:.2f} kPa) và đang đọng ẩm tăng nhanh!", "danger_blue"
            
        if slope > 0.04: return "📈 Xu hướng: Chỉ số VPD đang đi lên nhanh (Môi trường khô dần).", "normal"
        elif slope < -0.04: return "📉 Xu hướng: Chỉ số VPD đang lao dốc mạnh (Môi trường ẩm lên).", "normal"
        return "🔄 Xu hướng: Biến động biên độ nhỏ, vi khí hậu nằm trong tầm kiểm soát an toàn.", "normal"
    except Exception:
        return "🔄 Hệ thống đang cập nhật toán đồ xu hướng...", "normal"

def calculate_plant_stress_hours(df_filtered, vpd_min, vpd_max, filter_mode):
    """Tính toán thời lượng tích lũy stress nông học của cây trồng"""
    if df_filtered.empty or "VPD (kPa)" not in df_filtered.columns:
        return {"dry_hours": 0.0, "wet_hours": 0.0, "fungus_risk": 0}
        
    minutes_interval = 10
    if len(df_filtered) > 1 and "datetime_internal" in df_filtered.columns:
        try:
            minutes_interval = pd.Series(df_filtered["datetime_internal"]).diff().dropna().dt.total_seconds().median() / 60.0
        except Exception:
            minutes_interval = 10
            
    dry_pts = 0
    wet_pts = 0
    fungus_pts = 0
    
    for idx, row in df_filtered.iterrows():
        v = float(row["VPD (kPa)"])
        t = float(row["Nhiệt độ (°C)"])
        if v > vpd_max:
            dry_pts += 1
        elif v < vpd_min:
            wet_pts += 1
            if 16.0 <= t <= 25.0:
                fungus_pts += 1
                
    dry_h = round((dry_pts * minutes_interval) / 60.0, 1)
    wet_h = round((wet_pts * minutes_interval) / 60.0, 1)
    fungus_h = (fungus_pts * minutes_interval) / 60.0
    fungus_risk = min(int((fungus_h / 6.0) * 100), 100)
    
    return {"dry_hours": dry_h, "wet_hours": wet_h, "fungus_risk": fungus_risk}

def analyze_day_by_blocks_rt(history_data, vpd_min, vpd_max, target_day):
    """Phân nhóm dữ liệu và đối chiếu ma trận buổi thực tế"""
    if not history_data:
        return pd.DataFrame()
        
    df = pd.DataFrame(history_data)
    df_filtered = df[df["Bag"] == target_day].copy()
    if df_filtered.empty:
        return pd.DataFrame()
        
    df_filtered["Hour"] = df_filtered["datetime_internal"].dt.hour
    
    def assign_block(h):
        if 5 <= h < 10: return "🌅 Sáng (05h - 10h)"
        elif 10 <= h < 15: return "☀️ Trưa (10h - 15h)"
        elif 15 <= h < 19: return "🌇 Chiều (15h - 19h)"
        elif 19 <= h < 23: return "🌌 Tối (19h - 23h)"
        else: return "🌙 Khuya (23h - 05h)"
        
    df_filtered["Buổi"] = df_filtered["Hour"].apply(assign_block)
    
    summary = df_filtered.groupby("Buổi").agg({
        "Nhiệt độ (°C)": "mean", "Độ ẩm (%)": "mean", "VPD (kPa)": "mean"
    }).reindex(["🌅 Sáng (05h - 10h)", "☀️ Trưa (10h - 15h)", "🌇 Chiều (15h - 19h)", "🌌 Tối (19h - 23h)", "🌙 Khuya (23h - 05h)"]).dropna()
    
    report_data = []
    for idx, row in summary.iterrows():
        avg_t = round(row["Nhiệt độ (°C)"], 1)
        avg_h = round(row["Độ ẩm (%)"], 1)
        avg_v = round(row["VPD (kPa)"], 2)
        
        if avg_v < vpd_min:
            status = f"⚠️ Quá ẩm (Mục tiêu chung: {vpd_min}-{vpd_max})"
            sol = "Bật quạt đối lưu, mở thông bạt rèm che."
        elif avg_v > vpd_max:
            status = f"🚨 Quá khô (Mục tiêu chung: {vpd_min}-{vpd_max})"
            sol = "Bật phun sương mịn hạt, kéo rèm giảm bức xạ nhiệt."
        else:
            status = f"✅ Lý tưởng ({vpd_min}-{vpd_max})"
            sol = "Chỉ số hoàn hảo. Giữ nguyên thông gió thường trực."
            
        report_data.append({
            "Khoảng Buổi": idx,
            "Nhiệt độ TB": f"{avg_t} °C",
            "Độ ẩm TB": f"{avg_h} %",
            "VPD Trung Bình": f"{avg_v} kPa",
            "Đánh giá sinh học": status,
            "Giải pháp kỹ thuật": sol
        })
        
    return pd.DataFrame(report_data)
