import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    """
    Biểu đồ VPD thế hệ mới: Tự động phân tách nền theo các KHÚC THỜI GIAN TRONG NGÀY
    (Sáng, Trưa, Chiều, Tối, Khuya) và nhuộm màu cảnh báo cực đậm theo trục đứng.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Chưa có dữ liệu đồ thị")

    # Sao chép dataframe tránh ghi đè dữ liệu gốc
    df_chart = df.copy()

    # 1. ĐỊNH NGHĨA KHÚC BUỔI CHO TỪNG ĐIỂM DỮ LIỆU (Trục X)
    def assign_time_block(dt):
        try:
            hour = dt.hour
            if 5 <= hour < 10: return "🌅 Sáng (05h-10h)"
            elif 10 <= hour < 15: return "☀️ Trưa (10h-15h)"
            elif 15 <= hour < 19: return "🌇 Chiều (15h-19h)"
            elif 19 <= hour < 23: return "🌌 Tối (19h-23h)"
            else: return "🌙 Khuya (23h-05h)"
        except:
            return "Mô phỏng"

    if "datetime_internal" in df_chart.columns:
        df_chart["Khúc Buổi"] = df_chart["datetime_internal"].apply(assign_time_block)
    else:
        df_chart["Khúc Buổi"] = "Chưa phân khúc"

    # 2. XÁC ĐỊNH CÁC NGƯỠNG CẢNH BÁO MÀU ĐẬM (Trục Y)
    wet_limit = max(0.0, vpd_min - 0.2)
    hot_limit = vpd_max + 0.5
    
    zones = pd.DataFrame([
        {"start": 0.0, "end": wet_limit, "Trạng thái": "🔵 Quá Ẩm", "color": "#0B5345"},      
        {"start": wet_limit, "end": vpd_min, "Trạng thái": "🌐 Ẩm", "color": "#2980B9"},       
        {"start": vpd_min, "end": vpd_max, "Trạng thái": "🟩 Lý Tưởng", "color": "#27AE60"},     
        {"start": vpd_max, "end": hot_limit, "Trạng thái": "💛 Nóng", "color": "#F39C12"},          
        {"start": hot_limit, "end": 3.0, "Trạng thái": "🔴 Quá Nóng", "color": "#C0392B"}            
    ])

    # Lớp 1: Khối nền màu bão hòa 100% phân chia dải an toàn sinh học theo trục đứng Y
    background = alt.Chart(zones).mark_rect(opacity=1.0).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 2.5]), title="Chỉ số VPD (kPa)"),
        y2='end:Q',
        color=alt.Color('Trạng thái:N', 
                        scale=alt.Scale(
                            domain=["🔵 Quá Ẩm", "🌐 Ẩm", "🟩 Lý Tưởng", "💛 Nóng", "🔴 Quá Nóng"],
                            range=["#0B5345", "#2980B9", "#27AE60", "#F39C12", "#C0392B"]
                        ),
                        legend=alt.Legend(title="Màu Cảnh Báo", orient="top", direction="horizontal"))
    )

    # Lớp 2: Các đường chỉ ranh giới đứt nét
    rules_data = pd.DataFrame([{"y": wet_limit}, {"y": vpd_min}, {"y": vpd_max}, {"y": hot_limit}])
    rules = alt.Chart(rules_data).mark_rule(stroke="#17202A", strokeDash=[4, 3], strokeWidth=1.5).encode(y='y:Q')

    # Lớp 3: Đường Line nối các điểm dữ liệu thực tế xuyên qua các khúc Sáng - Trưa - Chiều - Tối
    # Trục X bây giờ sẽ nhóm theo "Khúc Buổi" trước, sau đó mới chi tiết đến "Hiển thị Giờ"
    line = alt.Chart(df_chart).mark_line(
        point=alt.OverlayMarkDef(color="#FFFFFF", size=65, filled=True, stroke="#17202A", strokeWidth=1.5), 
        color="#FFFFFF", 
        strokeWidth=4.0
    ).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian chi tiết"),
        y=alt.Y('VPD (kPa):Q'),
        column=alt.Column('Khúc Buổi:N', 
                          sort=["🌅 Sáng (05h-10h)", "☀️ Trưa (10h-15h)", "🌇 Chiều (15h-19h)", "🌌 Tối (19h-23h)", "🌙 Khuya (23h-05h)"],
                          title="KHÚC THỜI GIAN TRONG NGÀY",
                          header=alt.Header(labelFontSize=12, labelFontWeight="bold", labelColor="#17202A")),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )

    # Gộp cấu trúc ma trận đa cột (Mỗi cột là một khúc buổi)
    chart = alt.layer(background, rules, line, data=df_chart).properties(
        width=160, # Độ rộng của mỗi khúc buổi khi đứng cạnh nhau
        height=380,
        title=alt.TitleParams(
            text="MA TRẬN ĐỐI CHIẾU PHÂN KHÚC THỜI GIAN THEO BUỔI",
            subtitle=f"Cận dưới: {vpd_min} kPa | Cận trên: {vpd_max} kPa | Khóa màu Solid đậm 100%",
            anchor="start",
            fontSize=16,
            font="Segoe UI",
            subtitleColor="#2C3E50"
        )
    ).configure_axis(
        grid=False,
        labelColor="#17202A",
        titleColor="#17202A",
        labelFontSize=11,
        titleFontSize=12
    ).configure_view(
        strokeWidth=1,
        stroke="#BDC3C7" # Tạo viền mảnh ngăn cách giữa các hộp Sáng/Trưa/Chiều/Tối
    )

    return chart

def draw_temperature_chart(df):
    return alt.Chart(df).mark_line(point=True, color="#E74C3C", strokeWidth=3).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Nhiệt độ (°C):Q', title="Nhiệt độ (°C)"),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=240).configure_view(strokeWidth=0)

def draw_humidity_chart(df):
    return alt.Chart(df).mark_line(point=True, color="#3498DB", strokeWidth=3).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Độ ẩm (%):Q', title="Độ ẩm (%)"),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=240).configure_view(strokeWidth=0)
