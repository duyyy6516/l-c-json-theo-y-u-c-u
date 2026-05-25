import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    """
    Vẽ biểu đồ VPD phân tách 5 vùng màu nền sinh học chuẩn chỉnh:
    - [0.0 -> vpd_min - 0.2]: 🔵 Quá Ẩm -> Xanh dương đậm pastel
    - [vpd_min - 0.2 -> vpd_min]: 🌐 Ẩm -> Xanh dương nhạt thanh mát
    - [vpd_min -> vpd_max]: 🟩 Lý Tưởng -> Xanh lá cây an toàn
    - [vpd_max -> vpd_max + 0.5]: 💛 Nóng -> Vàng chanh/Vàng kem ấm
    - [vpd_max + 0.5 -> 3.0]: 🔴 Quá Nóng -> Đỏ hồng rực báo động
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Chưa có dữ liệu đồ thị")

    wet_limit = max(0.0, vpd_min - 0.2)
    hot_limit = vpd_max + 0.5
    
    # Khai báo 5 vùng dữ liệu tương ứng với 5 màu sắc yêu cầu
    zones = pd.DataFrame([
        {"start": 0.0, "end": wet_limit, "Vùng": "🔵 Quá Ẩm (Xanh Đậm)", "color": "#B3E5FC"},
        {"start": wet_limit, "end": vpd_min, "Vùng": "🌐 Ẩm (Xanh Nhạt)", "color": "#E1F5FE"},
        {"start": vpd_min, "end": vpd_max, "Vùng": "🟩 Lý Tưởng (Xanh Lá)", "color": "#C8E6C9"},
        {"start": vpd_max, "end": hot_limit, "Vùng": "💛 Nóng (Vàng)", "color": "#FFF9C4"},
        {"start": hot_limit, "end": 3.0, "Vùng": "🔴 Quá Nóng (Đỏ)", "color": "#FFCDD2"}
    ])

    # Tạo lớp phủ màu nền (Tăng độ đậm lên opacity=0.75 để nhìn rõ màu sắc tách biệt)
    background = alt.Chart(zones).mark_rect(opacity=0.75).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 2.5]), title="Chỉ số VPD (kPa)"),
        y2='end:Q',
        color=alt.Color('Vùng:N', 
                        scale=alt.Scale(
                            domain=["🔵 Quá Ẩm (Xanh Đậm)", "🌐 Ẩm (Xanh Nhạt)", "🟩 Lý Tưởng (Xanh Lá)", "💛 Nóng (Vàng)", "🔴 Quá Nóng (Đỏ)"],
                            range=["#B3E5FC", "#E1F5FE", "#C8E6C9", "#FFF9C4", "#FFCDD2"]
                        ),
                        legend=alt.Legend(
                            title="Phân Vùng Khí Hậu", 
                            orient="top",
                            direction="horizontal",
                            labelFontSize=10,
                            titleFontSize=11
                        ))
    )

    # Vẽ các đường giới hạn nét đứt mảnh ngăn cách rõ ràng
    rules_data = pd.DataFrame([{"y": wet_limit}, {"y": vpd_min}, {"y": vpd_max}, {"y": hot_limit}])
    rules = alt.Chart(rules_data).mark_rule(stroke="#78909C", strokeDash=[3, 3], strokeWidth=1.0).encode(y='y:Q')

    # Vẽ đường đồ thị trạm cảm biến (Dùng màu xám đen đậm #263238 để tương phản rõ ràng)
    line = alt.Chart(df).mark_line(
        point=alt.OverlayMarkDef(color="#263238", size=45, filled=True), 
        color="#263238", 
        strokeWidth=2.8
    ).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Mốc thời gian quét dữ liệu"),
        y=alt.Y('VPD (kPa):Q'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )

    chart = alt.layer(background, rules, line).properties(
        height=390,
        title=alt.TitleParams(
            text="MA TRẬN ĐỐI CHIẾU 5 VÙNG SINH HỌC VPD",
            subtitle=f"Cận dưới: {vpd_min} kPa | Cận trên: {vpd_max} kPa | Ngưỡng quá nóng: {hot_limit} kPa",
            anchor="start",
            fontSize=14,
            font="Segoe UI",
            subtitleColor="#546E7A"
        )
    ).configure_axis(
        grid=False,
        labelFont="Segoe UI",
        titleFont="Segoe UI",
        labelColor="#263238",
        titleColor="#263238"
    ).configure_view(
        strokeWidth=0
    )

    return chart

def draw_temperature_chart(df):
    return alt.Chart(df).mark_line(point=True, color="#EF5350", strokeWidth=2).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Nhiệt độ (°C):Q', title="Nhiệt độ (°C)"),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=260).configure_view(strokeWidth=0)

def draw_humidity_chart(df):
    return alt.Chart(df).mark_line(point=True, color="#29B6F6", strokeWidth=2).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Độ ẩm (%):Q', title="Độ ẩm (%)"),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=260).configure_view(strokeWidth=0)
