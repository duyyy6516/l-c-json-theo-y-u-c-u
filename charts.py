import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    """
    Vẽ biểu đồ VPD phối màu theo phong cách UI/UX Nông nghiệp Hiện đại (Modern Pastel):
    - [0 -> vpd_min - 0.2]: 💙 Quá Ẩm (Màu xanh sương mù dịu nhẹ)
    - [vpd_min - 0.2 -> vpd_min]: 🔵 Ẩm (Màu xanh ngọc mint nhạt)
    - [vpd_min -> vpd_max]: 🟩 Lý Tưởng (Màu xanh lá lá cây nhạt - Vùng an toàn)
    - [vpd_max -> vpd_max + 0.5]: 🟠 Nóng (Màu vàng cam bơ ấm)
    - [vpd_max + 0.5 -> 3.0]: 🔴 Quá Nóng (Màu hồng san hô / Đỏ pastel không chói)
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Chưa có dữ liệu đồ thị")

    wet_limit = max(0.0, vpd_min - 0.2)
    hot_limit = vpd_max + 0.5
    
    # Định nghĩa 5 phân vùng màu nền mượt mà (Mã màu tinh chỉnh theo chuẩn UI Pro)
    zones = pd.DataFrame([
        {"start": 0.0, "end": wet_limit, "Vùng": "💙 Quá Ẩm", "color": "#E1F5FE"},      # Khí hậu quá ẩm sương mù
        {"start": wet_limit, "end": vpd_min, "Vùng": "🔵 Ẩm", "color": "#E0F2F1"},         # Ẩm nhẹ, mát mẻ
        {"start": vpd_min, "end": vpd_max, "Vùng": "🟩 Lý Tưởng", "color": "#E8F5E9"},     # Vùng quang hợp hoàn hảo
        {"start": vpd_max, "end": hot_limit, "Vùng": "🟠 Nóng", "color": "#FFF3E0"},       # Khô nóng nhẹ
        {"start": hot_limit, "end": 3.0, "Vùng": "🔴 Quá Nóng", "color": "#FFEBEE"}       # Đỏ gắt nguy hiểm dạng nhạt
    ])

    # 1. Vẽ các mảng màu nền (Opacity giảm xuống 0.8 để mượt mà hơn)
    background = alt.Chart(zones).mark_rect(opacity=0.8).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 2.5]), title="Chỉ số VPD (kPa)"),
        y2='end:Q',
        color=alt.Color('Vùng:N', 
                        scale=alt.Scale(
                            domain=["💙 Quá Ẩm", "🔵 Ẩm", "🟩 Lý Tưởng", "🟠 Nóng", "🔴 Quá Nóng"],
                            range=["#E1F5FE", "#E0F2F1", "#E8F5E9", "#FFF3E0", "#FFEBEE"]
                        ),
                        legend=alt.Legend(
                            title="Chỉ dẫn Sinh học", 
                            orient="top",
                            direction="horizontal",
                            labelFontSize=11,
                            titleFontSize=12
                        ))
    )

    # 2. Vẽ các đường biên giới hạn nét đứt thanh mảnh (Màu xám Slate nhẹ, không dùng màu đậm gây rối)
    rules_data = pd.DataFrame([
        {"y": vpd_min, "color": "#90A4AE"},
        {"y": vpd_max, "color": "#90A4AE"},
        {"y": hot_limit, "color": "#CFD8DC"}
    ])
    rules = alt.Chart(rules_data).mark_rule(strokeDash=[3, 3], strokeWidth=1.2).encode(
        y='y:Q',
        color=alt.Color('color:N', scale=None)
    )

    # 3. Vẽ đường Line dữ liệu thực tế (Dùng màu Xám Than Đậm #37474F để tương phản cực cao trên nền Pastel)
    line = alt.Chart(df).mark_line(point=alt.OverlayMarkDef(color="#37474F", size=40), color="#37474F", strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian quét cảm biến"),
        y=alt.Y('VPD (kPa):Q'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )

    # Gộp các lớp đồ thị và cấu hình lưới mờ tinh tế
    chart = alt.layer(background, rules, line).properties(
        height=380,
        title=alt.TitleParams(
            text="BIỂU ĐỒ PHÂN TÍCH MA TRẬN VPD ĐA VÙNG",
            subtitle=f"Cận dưới: {vpd_min} kPa | Cận trên lý tưởng: {vpd_max} kPa | Ngưỡng báo động đỏ: {hot_limit} kPa",
            anchor="start",
            fontSize=14,
            font="Segoe UI",
            subtitleColor="#546E7A"
        )
    ).configure_axis(
        grid=False,
        labelFont="Segoe UI",
        titleFont="Segoe UI",
        labelColor="#37474F",
        titleColor="#37474F"
    ).configure_view(
        strokeWidth=0 # Bỏ khung viền ngoài thô cứng của biểu đồ
    )

    return chart

def draw_temperature_chart(df):
    """Biểu đồ nhiệt độ màu đỏ san hô dịu mắt"""
    return alt.Chart(df).mark_line(point=True, color="#EF5350", strokeWidth=2).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Nhiệt độ (°C):Q', title="Nhiệt độ (°C)"),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=260).configure_view(strokeWidth=0)

def draw_humidity_chart(df):
    """Biểu đồ độ ẩm màu xanh dương lỏng dịu mắt"""
    return alt.Chart(df).mark_line(point=True, color="#42A5F5", strokeWidth=2).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Độ ẩm (%):Q', title="Độ ẩm (%)"),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=260).configure_view(strokeWidth=0)
